/**
 * RAHAT Offline Synchronization Engine.
 * Manages local mutation queuing, true API reachability detection, FIFO replay,
 * foreign key remapping (local temporary IDs to server IDs), and idempotency headers.
 */

import { offlineDb, OfflinePatient, OfflineCareRequest, SyncQueueItem } from "./db";
import { Patient, PatientCreateInput } from "@/types/patient";
import { CareRequest, CareRequestCreateInput } from "@/types/careRequest";
import { Facility } from "@/types/facility";
import { Referral } from "@/types/referral";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface SyncResult {
  syncedCount: number;
  failedCount: number;
  remainingCount: number;
  errors: string[];
}

/**
 * Generate a UUID v4 string safely in browser or fallback.
 */
export function generateClientUUID(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

/**
 * Probe actual backend reachability beyond browser navigator.onLine.
 */
export async function checkBackendReachability(): Promise<boolean> {
  if (typeof navigator !== "undefined" && !navigator.onLine) {
    return false;
  }
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3000);
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: "GET",
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    return response.ok;
  } catch {
    return false;
  }
}

/**
 * Queue offline patient registration with client temporary UUID.
 */
export async function queueOfflinePatient(patientIn: PatientCreateInput): Promise<OfflinePatient> {
  const tempId = generateClientUUID();
  const tempCode = `OFFLINE-${Math.random().toString(36).substring(2, 8).toUpperCase()}`;
  const nowIso = new Date().toISOString();

  const localPatient: OfflinePatient = {
    id: tempId,
    patient_code: tempCode,
    full_name: patientIn.full_name,
    age: patientIn.age || null,
    gender: patientIn.gender,
    blood_group: patientIn.blood_group || null,
    phone: patientIn.phone || null,
    emergency_contact_name: patientIn.emergency_contact_name || null,
    emergency_contact_phone: patientIn.emergency_contact_phone || null,
    village_id: patientIn.village_id || null,
    address: patientIn.address || null,
    abha_reference: patientIn.abha_reference || null,
    chronic_conditions: patientIn.chronic_conditions || [],
    allergies: patientIn.allergies || [],
    pending_sync: true,
    local_temp_id: true,
    created_at: nowIso,
    updated_at: nowIso,
    synced_at: undefined,
  };

  // 1. Save to local Dexie table
  await offlineDb.patients.put(localPatient);

  // 2. Add to persistent sync queue
  const queueItem: SyncQueueItem = {
    operation_id: generateClientUUID(),
    entity_type: "PATIENT",
    entity_id: tempId,
    operation_type: "CREATE",
    payload: patientIn as unknown as Record<string, unknown>,
    idempotency_key: generateClientUUID(),
    retry_count: 0,
    status: "PENDING",
    created_at: nowIso,
  };
  await offlineDb.syncQueue.add(queueItem);

  return localPatient;
}

/**
 * Queue offline care request creation with client temporary UUID.
 */
export async function queueOfflineCareRequest(requestIn: CareRequestCreateInput): Promise<OfflineCareRequest> {
  const tempId = generateClientUUID();
  const tempNumber = `CR-OFFLINE-${Math.random().toString(36).substring(2, 8).toUpperCase()}`;
  const nowIso = new Date().toISOString();

  // If patient_id was an offline temp id, check if it was already mapped
  let effectivePatientId = requestIn.patient_id;
  const mapped = await offlineDb.idMap.get(requestIn.patient_id);
  if (mapped) {
    effectivePatientId = mapped.server_id;
  }

  const localCr: OfflineCareRequest = {
    id: tempId,
    request_number: tempNumber,
    patient_id: effectivePatientId,
    care_category: requestIn.care_category || "GENERAL_MEDICINE",
    required_service: requestIn.required_service || "General Medicine",
    urgency: requestIn.urgency || "MEDIUM",
    diagnostic_requirements: requestIn.diagnostic_requirements || [],
    specialist_required: !!requestIn.specialist_required,
    symptoms_summary: requestIn.symptoms_summary,
    status: "SUBMITTED",
    notes: requestIn.notes || null,
    pending_sync: true,
    local_temp_id: true,
    created_at: nowIso,
    updated_at: nowIso,
  };

  // 1. Save to local Dexie table
  await offlineDb.careRequests.put(localCr);

  // 2. Add to persistent sync queue
  const queueItem: SyncQueueItem = {
    operation_id: generateClientUUID(),
    entity_type: "CARE_REQUEST",
    entity_id: tempId,
    operation_type: "CREATE",
    payload: {
      ...requestIn,
      patient_id: effectivePatientId,
    } as unknown as Record<string, unknown>,
    idempotency_key: generateClientUUID(),
    retry_count: 0,
    status: "PENDING",
    created_at: nowIso,
  };
  await offlineDb.syncQueue.add(queueItem);

  return localCr;
}

/**
 * Process all pending mutations in the sync queue (FIFO).
 */
export async function processSyncQueue(token: string): Promise<SyncResult> {
  const result: SyncResult = {
    syncedCount: 0,
    failedCount: 0,
    remainingCount: 0,
    errors: [],
  };

  // 1. Verify reachability
  const isReachable = await checkBackendReachability();
  if (!isReachable) {
    result.errors.push("Backend is unreachable. Synchronization paused.");
    const count = await offlineDb.syncQueue.where("status").equals("PENDING").count();
    result.remainingCount = count;
    return result;
  }

  // 2. Fetch pending items sorted by local_id asc
  const queueItems = await offlineDb.syncQueue
    .where("status")
    .anyOf(["PENDING", "FAILED"])
    .sortBy("local_id");

  for (const item of queueItems) {
    if (!item.local_id) continue;

    try {
      // Mark as SYNCING
      await offlineDb.syncQueue.update(item.local_id, {
        status: "SYNCING",
        last_attempt_at: new Date().toISOString(),
      });

      if (item.entity_type === "PATIENT" && item.operation_type === "CREATE") {
        const response = await fetch(`${API_BASE_URL}/api/v1/patients`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
            "X-Idempotency-Key": item.idempotency_key,
          },
          body: JSON.stringify(item.payload),
        });

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.detail || `Server error (${response.status})`);
        }

        const serverPatient: Patient = await response.json();

        // Save ID Mapping
        await offlineDb.idMap.put({
          temp_id: item.entity_id,
          server_id: serverPatient.id,
          entity_type: "PATIENT",
          created_at: new Date().toISOString(),
        });

        // Replace local Dexie patient record
        await offlineDb.patients.delete(item.entity_id);
        await offlineDb.patients.put({
          ...serverPatient,
          pending_sync: false,
          local_temp_id: false,
          synced_at: new Date().toISOString(),
        });

        // Update any pending care requests that used this temp patient_id
        const linkedCrs = await offlineDb.careRequests.where("patient_id").equals(item.entity_id).toArray();
        for (const cr of linkedCrs) {
          await offlineDb.careRequests.update(cr.id, { patient_id: serverPatient.id });
        }

        // Mark queue item completed
        await offlineDb.syncQueue.delete(item.local_id);
        result.syncedCount += 1;
      } else if (item.entity_type === "CARE_REQUEST" && item.operation_type === "CREATE") {
        // Remap patient_id if needed
        const payload = { ...item.payload };
        if (typeof payload.patient_id === "string") {
          const mapped = await offlineDb.idMap.get(payload.patient_id);
          if (mapped) {
            payload.patient_id = mapped.server_id;
          }
        }

        const response = await fetch(`${API_BASE_URL}/api/v1/care-requests`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
            "X-Idempotency-Key": item.idempotency_key,
          },
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.detail || `Server error (${response.status})`);
        }

        const serverCr: CareRequest = await response.json();

        // Save ID Mapping
        await offlineDb.idMap.put({
          temp_id: item.entity_id,
          server_id: serverCr.id,
          entity_type: "CARE_REQUEST",
          created_at: new Date().toISOString(),
        });

        // Replace local Dexie record
        await offlineDb.careRequests.delete(item.entity_id);
        await offlineDb.careRequests.put({
          ...serverCr,
          pending_sync: false,
          local_temp_id: false,
          synced_at: new Date().toISOString(),
        });

        // Mark queue item completed
        await offlineDb.syncQueue.delete(item.local_id);
        result.syncedCount += 1;
      }
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : "Sync failed";
      const newRetries = (item.retry_count || 0) + 1;
      const finalStatus = newRetries >= 5 ? "FAILED" : "PENDING";

      await offlineDb.syncQueue.update(item.local_id, {
        status: finalStatus,
        retry_count: newRetries,
        error_message: errorMsg,
      });

      result.failedCount += 1;
      result.errors.push(`${item.entity_type} (${item.entity_id.slice(0, 8)}): ${errorMsg}`);
    }
  }

  result.remainingCount = await offlineDb.syncQueue.where("status").equals("PENDING").count();
  return result;
}

/**
 * Cache server data into IndexedDB for offline viewing.
 */
export async function cachePatientsLocally(patients: Patient[]): Promise<void> {
  const now = new Date().toISOString();
  await offlineDb.transaction("rw", offlineDb.patients, async () => {
    for (const p of patients) {
      const existing = await offlineDb.patients.get(p.id);
      if (!existing || !existing.pending_sync) {
        await offlineDb.patients.put({
          ...p,
          pending_sync: false,
          local_temp_id: false,
          synced_at: now,
        });
      }
    }
  });
}

export async function cacheCareRequestsLocally(careRequests: CareRequest[]): Promise<void> {
  const now = new Date().toISOString();
  await offlineDb.transaction("rw", offlineDb.careRequests, async () => {
    for (const cr of careRequests) {
      const existing = await offlineDb.careRequests.get(cr.id);
      if (!existing || !existing.pending_sync) {
        await offlineDb.careRequests.put({
          ...cr,
          pending_sync: false,
          local_temp_id: false,
          synced_at: now,
        });
      }
    }
  });
}

export async function cacheFacilitiesLocally(facilities: Facility[]): Promise<void> {
  const now = new Date().toISOString();
  await offlineDb.transaction("rw", offlineDb.facilities, async () => {
    for (const fac of facilities) {
      await offlineDb.facilities.put({
        ...fac,
        synced_at: now,
      });
    }
  });
}

export async function cacheReferralsLocally(referrals: Referral[]): Promise<void> {
  const now = new Date().toISOString();
  await offlineDb.transaction("rw", offlineDb.referrals, async () => {
    for (const ref of referrals) {
      await offlineDb.referrals.put({
        ...ref,
        synced_at: now,
      });
    }
  });
}

export async function cacheDashboardLocally(key: string, data: unknown): Promise<void> {
  const now = new Date().toISOString();
  await offlineDb.cachedDashboards.put({
    key,
    data,
    synced_at: now,
  });
}
