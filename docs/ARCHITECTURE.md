# RAHAT Technical Architecture Overview
# Rural Healthcare Access & Referral Assistance Technology

> **Complete Architecture Specification across Phases 1–14**

---

## 1. High-Level System Architecture

```
                                  +---------------------------------------+
                                  |       Frontline & Facility Users      |
                                  |   (ASHA, ANM, CHO, Doctor, MO, Admin) |
                                  +-------------------+-------------------+
                                                      |
                                                      v
                                  +---------------------------------------+
                                  |         Next.js 16 Client App         |
                                  |  - Responsive App Router UI           |
                                  |  - IndexedDB Local Queuing (Dexie)    |
                                  |  - Offline-First Service Worker (PWA) |
                                  +-------------------+-------------------+
                                                      |
                                                      | HTTPS / REST (JWT Bearer)
                                                      v
                                  +---------------------------------------+
                                  |        FastAPI Backend Gateway        |
                                  |  - Strict 8-Role RBAC Middleware      |
                                  |  - Sliding-Window Rate Limiter        |
                                  |  - Tamper-Evident Audit Logger        |
                                  |  - Liveness & Readiness Probes        |
                                  +---------+-------------------+---------+
                                            |                   |
                     +----------------------+                   +-----------------------+
                     v                                                                  v
+---------------------------------------+                              +---------------------------------------+
|   Deterministic Recommendation Engine |                              |      AI Referral Assistant Layer      |
| - 6-Factor Multi-Criteria Scoring     |                              | - Data Minimization Sanitizer         |
| - Haversine Geospatial Distance       |                              | - Non-Diagnostic Summary Drafter      |
| - Dynamic Capability & Bed Filter     |                              | - Missing Info Callout Generator      |
+-------------------+-------------------+                              +-------------------+-------------------+
                    |                                                                      |
                    +-----------------------------------+----------------------------------+
                                                        |
                                                        v
                                  +---------------------------------------+
                                  |    14-State Referral State Machine    |
                                  | - Validated State Transitions         |
                                  | - Event Timeline Generation           |
                                  | - Closed-Loop Back-Referral Tracker   |
                                  +---------+-------------------+---------+
                                            |                   |
                     +----------------------+                   +-----------------------+
                     v                                                                  v
+---------------------------------------+                              +---------------------------------------+
|      PostgreSQL 16 + PostGIS 3.4      |                              |            Redis 7 In-Memory          |
| - 13 Relational Domain Models         |                              | - Session Invalidation Blacklist      |
| - Spatial R-Tree Indexing (POINT)     |                              | - Real-time Rate Limiting Store       |
| - Persistent Volume: postgres_data    |                              | - Persistent Volume: redis_data       |
+---------------------------------------+                              +---------------------------------------+
```

---

## 2. Relational Database Domain Models (13 Entities)

| Model | Table | Primary Key | Key Relationships & Description |
| :--- | :--- | :--- | :--- |
| **`Role`** | `roles` | UUID | RBAC permissions matrix JSON; 1-to-many with `User`. |
| **`User`** | `users` | UUID | User authentication, hashed passwords, role linkage, facility affiliation. |
| **`Village`** | `villages` | UUID | Habitational units with PostGIS `POINT` coordinates (SRID 4326). |
| **`Facility`** | `facilities` | UUID | Sub Centers, PHCs, CHCs, SDHs, DHs with PostGIS coordinates, bed counts. |
| **`FacilityCapability`** | `facility_capabilities` | UUID | Specialties, NICU, trauma care, ICU, and diagnostic availability. |
| **`HealthcareProfessional`** | `healthcare_professionals` | UUID | Doctors, nurses, ASHAs, ANMs with councils, specialties, and duty rosters. |
| **`Patient`** | `patients` | UUID | Patient demographic index, ABHA reference, anonymous code, medical history. |
| **`CareRequest`** | `care_requests` | UUID | Initial frontline triage, chief complaint, vitals, required services. |
| **`Referral`** | `referrals` | UUID | Core inter-facility workflow entity linking care request, origin, destination. |
| **`ReferralEvent`** | `referral_events` | UUID | Immutable chronological lifecycle audit milestones and status transitions. |
| **`FollowUp`** | `follow_ups` | UUID | Post-discharge village monitoring tasks assigned to frontline ASHA workers. |
| **`Notification`** | `notifications` | UUID | System alerts, dispatch updates, and emergency triage notifications. |
| **`AuditLog`** | `audit_logs` | UUID | Tamper-evident security and data modification audit records. |

---

## 3. 14-State Referral Lifecycle State Machine

```
   CREATED
      │
      ▼
PENDING_ACCEPTANCE ──► [ REJECTED ] ──► [ REROUTED ] (spawns child in PENDING_ACCEPTANCE)
      │
      ▼
   ACCEPTED
      │
      ▼
PATIENT_NOTIFIED
      │
      ▼
   DEPARTED (In Transit)
      │
      ▼
   ARRIVED (Emergency Bay)
      │
      ▼
  IN_SERVICE (Active Care)
      │
      ▼
  COMPLETED (Care Rendered)
      │
      ▼
BACK_REFERRED (Village Follow-Up)
      │
      ▼
  FOLLOW_UP
      │
      ▼
    CLOSED (Terminal State)
```

- **Terminal States**: `CLOSED`, `CANCELLED` (Zero outgoing transitions).
- **Enforcement**: Transition matrix validated in `ReferralService`; all illegal state skips rejected with HTTP 400.

---

## 4. Multi-Factor Deterministic Facility Recommendation Engine

$$\text{Score} = 0.30 \cdot S_{\text{service}} + 0.20 \cdot S_{\text{diagnostic}} + 0.20 \cdot S_{\text{specialist}} + 0.15 \cdot S_{\text{distance}} + 0.10 \cdot S_{\text{availability}} + 0.05 \cdot S_{\text{workload}}$$

1. **Service Capability Match ($S_{\text{service}}$, Weight: 30%)**: Proportional coverage of required clinical specialties.
2. **Diagnostic Readiness Match ($S_{\text{diagnostic}}$, Weight: 20%)**: Laboratory, imaging, and diagnostic equipment availability.
3. **Specialist Duty Availability ($S_{\text{specialist}}$, Weight: 20%)**: On-duty roster status of required medical specialists.
4. **Geographic Proximity ($S_{\text{distance}}$, Weight: 15%)**: Computed via Haversine / PostGIS geodesic distance:
   $$S_{\text{distance}} = \max\left(0, 100 - \frac{\text{Distance (km)}}{1.5}\right)$$
5. **Bed Availability & Capacity ($S_{\text{availability}}$, Weight: 10%)**: Real-time available general, ICU, and oxygen bed ratios.
6. **Active Workload Factor ($S_{\text{workload}}$, Weight: 5%)**: Inverse penalty based on current active referrals in service.

---

## 5. Assistive AI Referral Assistant & Safety Guardrails

- **Strict Non-Diagnostic Policy**: The AI assistant drafts administrative intake summaries and highlights missing clinical history. It **never diagnoses, prescribes, changes urgency, or routes patients autonomously**.
- **Mandatory Disclaimer**: Every AI response includes: `"AI-assisted — requires human review"`.
- **Privacy Minimization**: Patient name, phone number, village address, and government IDs are stripped before sending payloads to AI providers.
- **Provider Resilience**: Seamless fallback to deterministic rule-based extractor during provider outages or timeouts.

---

## 6. Offline-First PWA & Background Synchronization

- **Local Storage**: IndexedDB storage managed via Dexie.js for patients, care requests, and offline drafts.
- **Client-Side UUIDs**: Entities created offline receive client-generated UUIDs for deterministic server mapping.
- **Idempotency Keys**: Network requests attach unique `X-Idempotency-Key` headers to guarantee zero duplicate creation upon reconnection.
- **Auto-Sync Engine**: Background worker detects `online` network events and drains pending queues in chronological sequence.

---

## 7. Role-Based Access Control (RBAC) Matrix

| Endpoint Group | `ADMIN` | `DISTRICT_ADMIN` | `FACILITY_ADMIN` | `DOCTOR` | `MEDICAL_OFFICER` | `CHO` | `ANM` | `ASHA` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Patient Registration** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Care Request Creation** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Recommendation Query** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Referral Dispatch** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Referral Accept/Reject** | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Care Completion** | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Back-Referral** | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Frontline Dashboard** | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Facility Dashboard** | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **District Dashboard** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **System Administration** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

---

## 8. District Analytics & Care Completion KPI

$$\text{Care Completion Rate} = \frac{\text{Completed Care Requests in District}}{\text{Eligible Referred Care Requests in District}} \times 100$$

- **Zero-Division Handling**: Returns $0.0\%$ when denominator is 0.
- **8-Stage Conversion Funnel**:
  $$\text{Created} \ge \text{Pending} \ge \text{Accepted} \ge \text{Notified} \ge \text{Departed} \ge \text{Arrived} \ge \text{In Service} \ge \text{Completed}$$
