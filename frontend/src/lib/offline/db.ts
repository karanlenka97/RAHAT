/**
 * Dexie.js IndexedDB Schema for RAHAT Offline-First Frontline Operations.
 */

import Dexie, { Table } from "dexie";
import { Patient } from "@/types/patient";
import { CareRequest } from "@/types/careRequest";
import { Facility } from "@/types/facility";
import { Referral } from "@/types/referral";

export interface OfflinePatient extends Patient {
  pending_sync?: boolean;
  local_temp_id?: boolean;
  synced_at?: string;
}

export interface OfflineCareRequest extends CareRequest {
  pending_sync?: boolean;
  local_temp_id?: boolean;
  synced_at?: string;
}

export interface OfflineFacility extends Facility {
  synced_at?: string;
}

export interface OfflineReferral extends Referral {
  synced_at?: string;
}

export interface SyncQueueItem {
  local_id?: number;
  operation_id: string; // Unique client UUID for the sync item
  entity_type: "PATIENT" | "CARE_REQUEST" | "FACILITY_UPDATE" | string;
  entity_id: string; // Client temp UUID or server UUID
  operation_type: "CREATE" | "UPDATE";
  payload: Record<string, unknown>;
  idempotency_key: string;
  retry_count: number;
  last_attempt_at?: string | null;
  status: "PENDING" | "SYNCING" | "COMPLETED" | "FAILED" | "CONFLICT";
  error_message?: string | null;
  created_at: string;
}

export interface ClientIdMapping {
  temp_id: string;
  server_id: string;
  entity_type: string;
  created_at: string;
}

export interface CachedDashboardItem {
  key: string; // e.g. 'frontline', 'facility', 'district'
  data: unknown;
  synced_at: string;
}

export class RahatOfflineDatabase extends Dexie {
  patients!: Table<OfflinePatient, string>;
  careRequests!: Table<OfflineCareRequest, string>;
  facilities!: Table<OfflineFacility, string>;
  referrals!: Table<OfflineReferral, string>;
  syncQueue!: Table<SyncQueueItem, number>;
  idMap!: Table<ClientIdMapping, string>;
  cachedDashboards!: Table<CachedDashboardItem, string>;

  constructor() {
    super("rahat_offline_db");
    this.version(1).stores({
      patients: "id, patient_code, full_name, phone, village_id, pending_sync, updated_at",
      careRequests: "id, request_number, patient_id, care_category, urgency, status, pending_sync, updated_at",
      facilities: "id, name, facility_type, district, total_beds, available_beds, synced_at",
      referrals: "id, referral_code, patient_id, care_request_id, status, synced_at",
      syncQueue: "++local_id, operation_id, entity_type, entity_id, operation_type, idempotency_key, retry_count, status, created_at",
      idMap: "temp_id, server_id, entity_type, created_at",
      cachedDashboards: "key, synced_at",
    });
  }
}

export const offlineDb = new RahatOfflineDatabase();
