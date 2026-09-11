# SIH 2026 Live Demonstration Runbook
# RAHAT — Rural Healthcare Access & Referral Assistance Technology

> **Smart India Hackathon (SIH 2026) Official Demonstration Runbook**
> Problem Statement: Streamlining Inter-Facility Rural Healthcare Referrals, Capacity Visibility, and Closed-Loop Care Completion.

---

## 1. Executive Summary & Core Value Proposition

In rural and tribal regions across India, over **40% of emergency referrals fail to convert into completed care** due to:
1. **Blind Referrals**: Frontline workers dispatch patients to overburdened or unequipped facilities lacking beds, diagnostics, or on-duty specialists.
2. **Transit Drop-Offs**: Patients get lost during transport with zero visibility between community dispatch and hospital intake.
3. **Open-Loop Care**: Once treated, patients receive no structured back-referral to village health workers for follow-up and rehabilitation.

### The RAHAT Differentiator
> *"RAHAT does not merely create a referral. RAHAT ensures that the referral becomes completed care."*

RAHAT connects **frontline workers (ASHA, ANM, CHO)**, **receiving facilities (PHC, CHC, SDH, DH)**, and **district administrators** into a synchronized, offline-resilient, deterministic care network.

---

## 2. Persona Directory & Demo Credentials

All demonstration accounts use the standardized development password:
`RahatDev@2026`

| Persona | Name | Role | Email | Key Capabilities |
| :--- | :--- | :--- | :--- | :--- |
| **Frontline Health Worker** | Pooja Mishra | `CHO` | `cho@rahat.local` | Patient intake, triage, AI summary review, facility recommendation, referral dispatch, frontline dashboard |
| **Community Health Worker** | Manju Bai | `ASHA` | `asha@rahat.local` | Village patient registration, symptoms recording, offline draft queuing |
| **Facility Specialist** | Dr. Rajesh Varma | `DOCTOR` | `doctor@rahat.local` | Inbound referral triage, accept/reject/reroute, emergency arrival, care completion, back-referral |
| **Medical Officer** | Dr. Sunita Patel | `MEDICAL_OFFICER` | `medical.officer@rahat.local` | Clinical review, transfer authorization, PHC operational queue |
| **Facility Superintendent** | Ramesh Jena | `FACILITY_ADMIN` | `facility.admin@rahat.local` | Bed inventory management, specialist roster, diagnostic capability toggles |
| **District Health Officer** | Dr. Arvind Rao | `DISTRICT_ADMIN` | `district.admin@rahat.local` | District-wide analytics, referral funnel, care completion KPI tracking |
| **System Administrator** | Antigravity Admin | `ADMIN` | `admin@rahat.local` | User management, facility registration, system-wide audit logs |

---

## 3. Golden Path Live Demonstration Script (7-Minute Flow)

```
[ Frontline ASHA/CHO ]          [ Backend Engine ]           [ Receiving Doctor ]          [ District Admin ]
         │                              │                             │                            │
 1. Patient Intake & Vitals             │                             │                            │
         │                              │                             │                            │
 2. Care Request Created                │                             │                            │
         │                              │                             │                            │
 3. AI Assistive Summary ───────────────┤ (Non-diagnostic review)     │                            │
         │                              │                             │                            │
 4. Human Review & Confirm              │                             │                            │
         │                              │                             │                            │
 5. Deterministic Matching ─────────────┤ (6-factor score 0-100)      │                            │
         │                              │                             │                            │
 6. Dispatch Referral ──────────────────┼────────────────────────────>│                            │
         │                              │                   7. Inspect Queue & Accept              │
         │                              │                             │                            │
 8. Patient Notified & Transit          │                             │                            │
         │                              │                   9. Emergency Bay Arrival               │
         │                              │                             │                            │
         │                              │                  10. Service Start & Complete            │
         │                              │                             │                            │
         │                              │                  11. Back-Referral Created               │
         │                              │                             │                            │
 12. Village Follow-Up (Closed) ────────┴─────────────────────────────┴───────────────────────────>│
                                                                                           13. Care Completion KPI
                                                                                               Updates to 100%
```

### Step-by-Step Jury Walkthrough

#### Stage 1: Frontline Patient Registration & Intake (CHO Pooja)
1. **Login**: Navigate to `/login` and sign in as `cho@rahat.local` / `RahatDev@2026`.
2. **Patient Directory**: Navigate to `/patients`. Show search filtering and ABHA identifier linkage.
3. **Register Patient**: Register a synthetic patient (*Sunita Rani, 34/F, Village: Kuarmunda, Sundargarh*).
4. **Create Care Request**: Navigate to `/care-requests/new`.
   - **Category**: `GENERAL_MEDICINE` / `Cardiology`
   - **Urgency**: `HIGH`
   - **Chief Complaint**: *"Severe retrosternal chest pain radiating to left shoulder and jaw with cold diaphoresis for 3 hours."*
   - **Vitals**: BP 150/95 mmHg, Pulse 108 bpm, SpO2 94%.
   - **Diagnostic Needs**: 12-Lead ECG, Cardiac Enzymes.
   - **Specialist Required**: Yes (Cardiologist / Physician).

#### Stage 2: Assistive AI Clinical Summarization & Human-in-the-Loop Review
5. **AI Assistant Generation**: Click **"Generate AI Referral Summary"**.
   - *Key Talking Point*: Highlight the mandatory disclaimer: `"AI-assisted — requires human review"`.
   - *Key Talking Point*: Explain that the AI **does not diagnose or prescribe**; it acts strictly as an administrative drafting assistant.
   - *Key Talking Point*: Show that missing information is explicitly flagged (e.g., *"Past chronic history not documented"*).
6. **Human Review & Application**: Frontline worker reviews the draft summary, modifies notes if needed, and clicks **"Confirm & Apply Summary"**.

#### Stage 3: Explainable Multi-Factor Facility Recommendation Engine
7. **Query Recommendations**: View top-matched facilities.
   - *Key Talking Point*: Emphasize that recommendation scoring is **100% deterministic, relational, and mathematical** (zero LLM hallucinations).
   - **Formula Breakdown**:
     $$\text{Score} = 30\% \cdot \text{Service} + 20\% \cdot \text{Diagnostic} + 20\% \cdot \text{Specialist} + 15\% \cdot \text{Distance} + 10\% \cdot \text{Beds} + 5\% \cdot \text{Workload}$$
   - Inspect the top recommendation (*Rourkela Government Hospital, Score: 94.2/100*).
   - Show matched capabilities (*Cardiology, 12-Lead ECG, 24/7 ICU, 14 beds available, 18.4 km away*).
8. **Dispatch Referral**: Select the top hospital and click **"Dispatch Referral"**. Status becomes `PENDING_ACCEPTANCE`.

#### Stage 4: Receiving Facility Triage & Acceptance (Dr. Rajesh)
9. **Login**: Open a private browser window or log out, and sign in as `doctor@rahat.local`.
10. **Inbound Operational Queue**: Navigate to `/referrals`.
    - Show the prioritized inbound referral card with live elapsed timer.
11. **Accept Referral**: Click **"Accept Referral"**. Status transitions to `ACCEPTED`.

#### Stage 5: Patient Transit Tracking & Emergency Bay Intake
12. **Patient Notification**: Frontline worker or escort records patient dispatch notification (`PATIENT_NOTIFIED`).
13. **Transit Departure**: Record ambulance departure (`DEPARTED`, `transport_mode=108_AMBULANCE`).
14. **Emergency Bay Arrival**: Receiving facility triage nurse records arrival (`ARRIVED`).
15. **Service Initiation**: Doctor admits patient to cardiology emergency bay (`IN_SERVICE`).

#### Stage 6: Care Completion & Closed-Loop Back-Referral
16. **Care Completion**: Doctor completes medical evaluation and intervention.
    - Clinical summary: *"Acute Coronary Syndrome stabilized. Dual antiplatelet therapy administered. 12-Lead ECG normalized."*
    - Click **"Complete Care"** $\rightarrow$ Status transitions to `COMPLETED`.
17. **Generate Back-Referral**: Doctor generates village follow-up instructions for CHO Pooja.
    - Follow-up notes: *"Check BP and pulse weekly at Kuarmunda Health & Wellness Centre. Ensure adherence to medication."*
    - Status transitions to `BACK_REFERRED`.

#### Stage 7: District Analytics & Care Completion KPI (District Admin Dr. Arvind)
18. **Login**: Sign in as `district.admin@rahat.local`.
19. **District Operational Dashboard**: Navigate to `/dashboard/district`.
    - Show the **Care Completion Rate KPI**:
      $$\text{Care Completion Rate} = \frac{\text{Completed Care Requests}}{\text{Eligible Referred Care Requests}} \times 100$$
    - Show the **8-Stage Referral Funnel**:
      `CREATED` $\rightarrow$ `PENDING` $\rightarrow$ `ACCEPTED` $\rightarrow$ `NOTIFIED` $\rightarrow$ `DEPARTED` $\rightarrow$ `ARRIVED` $\rightarrow$ `IN_SERVICE` $\rightarrow$ `COMPLETED`
    - Show the Facility Performance comparison table with bed utilization and average resolution hours.

---

## 4. Failure & Resilience Demonstrations

### Scenario A: Referral Rejection & Immediate Reroute
1. Doctor at Facility A rejects an inbound referral with reason code `CAPACITY_UNAVAILABLE` (*"All ICU beds occupied"*).
2. Status transitions to `REJECTED`.
3. System prompts Frontline CHO with one-click **"Reroute Referral"** modal.
4. CHO selects alternative facility (*Sundargarh District Hospital*).
5. System spawns a new child referral in `PENDING_ACCEPTANCE`, preserving complete audit history.

### Scenario B: AI Service Outage Graceful Fallback
1. Simulate external AI provider disconnection (`AI_PROVIDER=mock` or network timeout).
2. The UI continues operating seamlessly with deterministic rule-based extractions.
3. Zero clinical or referral workflows are blocked.

### Scenario C: Offline-First PWA Mode (No Internet in Remote Tribal Pocket)
1. Disconnect network or toggle Chrome DevTools Network $\rightarrow$ Offline.
2. A prominent yellow banner appears: **"Offline Mode — Local Queuing Active"**.
3. CHO registers a new patient and drafts a care request locally.
4. Data is stored in browser IndexedDB with a client-generated UUID.
5. Reconnect network $\rightarrow$ RAHAT auto-sync engine drains the queue and reconciles data with zero data loss.

---

## 5. SIH Evaluation Matrix Alignment

| Evaluation Criterion | RAHAT Implementation | Jury Proof |
| :--- | :--- | :--- |
| **Innovation & Impact** | Closes the open-loop referral gap; measures completed care rather than dispatches | Care Completion Rate KPI & Closed-loop Back-referral flow |
| **Technical Feasibility** | Multi-tier architecture: Next.js 16 + FastAPI + PostGIS + Redis + Docker | 158/158 automated pytest passes, clean Next.js build |
| **User Experience** | Role-tailored dashboards for ASHA, CHO, Doctor, and District Admin | 8 RBAC persona roles with dedicated action queues |
| **AI Safety & Ethics** | Non-diagnostic, non-prescriptive administrative assistance with human-in-the-loop review | Strict PII minimization, prompt injection resistance |
| **Rural Readiness** | Offline-first PWA with IndexedDB local buffering and idempotency keys | Background auto-sync with conflict-free resolution |

---

## 6. Known Prototype Boundaries

1. **Synthetic Data**: All patients, facilities, ABHA IDs, and phone numbers are generated for demonstration.
2. **Government Integrations**: ABHA and 108 ambulance APIs are configured via extensible mock integration adapters.
3. **Hardware Independence**: Operates on any standard web browser, smartphone, tablet, or laptop without proprietary hardware.
