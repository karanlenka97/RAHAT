# RAHAT — Rural Healthcare Access & Referral Assistance Technology

> **Smart India Hackathon 2026 — Functional Prototype Technical Specification**

---

## 1. Project Overview

### 1.1 Project Name

**RAHAT**

**Rural Healthcare Access & Referral Assistance Technology**

### 1.2 One-Line Description

RAHAT is an offline-first rural healthcare coordination platform that ensures a patient's referral becomes **completed care** by connecting frontline healthcare workers, public health facilities, diagnostics, specialists, referrals, and follow-up into one coordinated workflow.

### 1.3 Core Problem

Rural healthcare systems already contain multiple services such as:

* Primary Health Centres
* Community Health Centres
* Ayushman Arogya Mandirs
* District hospitals
* Telemedicine
* Diagnostics
* Mobile Medical Units
* Emergency services
* NCD screening
* Digital health infrastructure

The problem is not simply the absence of healthcare services.

The major prototype focus is the **coordination gap between these services**.

A referral being created does not necessarily mean that:

* the receiving facility accepted it,
* the patient reached the facility,
* the required service was available,
* treatment was completed,
* the patient was sent back to the local facility,
* or follow-up happened.

### 1.4 RAHAT's Core Objective

RAHAT focuses on:

> **Referral-to-care completion rather than referral generation.**

The platform should track the patient's care journey from the first referral request until the care cycle is completed.

---

# 2. Product Vision

## 2.1 Vision

Build a digital coordination layer that works **with existing government healthcare systems rather than replacing them**.

RAHAT should connect:

```text
Frontline Worker
       ↓
Primary Facility
       ↓
Care Requirement
       ↓
Smart Facility Recommendation
       ↓
Referral
       ↓
Receiving Facility
       ↓
Patient Arrival
       ↓
Treatment / Service
       ↓
Back Referral
       ↓
Local Follow-up
       ↓
Care Completed
```

---

# 3. Important Product Principles

The implementation MUST follow these principles.

### Principle 1 — Do Not Build Another Generic Telemedicine App

RAHAT is not primarily a video consultation application.

### Principle 2 — Do Not Replace Existing Government Systems

RAHAT should use integration adapters so existing government platforms can eventually be connected.

### Principle 3 — Referral ≠ Completed Care

The system's main KPI is:

```text
Referral Completion Rate
```

not simply:

```text
Number of Referrals Created
```

### Principle 4 — AI Does Not Diagnose

AI must never independently diagnose patients.

AI can assist with:

* referral-note summarization,
* information extraction,
* recommendation explanation,
* administrative assistance.

### Principle 5 — Prototype Uses Synthetic Data

No real patient information should be used in the SIH prototype.

All demonstration data must be synthetic.

### Principle 6 — Offline First

The frontline interface must continue to work during poor/no internet connectivity.

---

# 4. Target Users

RAHAT has three primary interfaces.

## 4.1 Frontline Healthcare Worker

Examples:

* ASHA
* ANM
* CHO
* Medical Officer

Responsibilities:

* register/search patients,
* create care requests,
* record basic observations,
* create referrals,
* view referral status,
* update patient journey,
* schedule follow-up.

---

## 4.2 Receiving Facility

Examples:

* PHC
* CHC
* Rural Hospital
* District Hospital
* Specialty Centre

Responsibilities:

* receive referral requests,
* review referral,
* accept/reject referral,
* provide treatment/service,
* mark service completed,
* create back-referral,
* provide follow-up instructions.

---

## 4.3 District Health Administrator

Responsibilities:

* monitor referral pipeline,
* monitor delayed referrals,
* identify facility bottlenecks,
* view facility workload,
* view care completion statistics,
* monitor follow-up,
* identify underserved areas.

---

# 5. User Roles

Implement role-based access control.

## Roles

```text
ADMIN
DISTRICT_ADMIN
FACILITY_ADMIN
DOCTOR
MEDICAL_OFFICER
CHO
ANM
ASHA
```

---

# 6. Role Permissions

## ADMIN

Full system access.

Can:

* manage users,
* manage facilities,
* manage services,
* manage system configuration,
* view all dashboards.

---

## DISTRICT_ADMIN

Can:

* view district dashboard,
* view facilities,
* view referrals,
* view delays,
* view analytics,
* view bottlenecks.

Cannot:

* modify system configuration.

---

## FACILITY_ADMIN

Can:

* manage facility profile,
* manage services,
* manage facility capacity,
* view facility referrals,
* assign referrals.

---

## DOCTOR

Can:

* view assigned referrals,
* review patient information,
* update clinical service status,
* complete referral,
* create back-referral.

---

## MEDICAL_OFFICER

Can:

* create care requests,
* create referrals,
* review patients,
* view recommendations,
* update referral status.

---

## CHO / ANM / ASHA

Can:

* create/search patients,
* create care requests,
* initiate referrals,
* view referral progress,
* update permitted patient journey information,
* manage follow-up tasks.

---

# 7. High-Level Architecture

```text
                     ┌──────────────────────┐
                     │      FRONTEND        │
                     │ Next.js + TypeScript │
                     │ Tailwind + shadcn/ui │
                     └──────────┬───────────┘
                                │
                         REST / JSON
                                │
                     ┌──────────▼───────────┐
                     │       FASTAPI        │
                     │       Backend        │
                     └──────────┬───────────┘
                                │
          ┌─────────────────────┼──────────────────────┐
          │                     │                      │
          ▼                     ▼                      ▼
   ┌─────────────┐      ┌──────────────┐      ┌──────────────┐
   │ PostgreSQL  │      │ Recommendation│      │ Integration  │
   │ + PostGIS   │      │    Engine     │      │   Adapters   │
   └─────────────┘      └──────────────┘      └──────┬───────┘
                                                      │
                                  ┌───────────────────┼───────────────────┐
                                  │                   │                   │
                                  ▼                   ▼                   ▼
                              ABDM Adapter       eSanjeevani         NCD/HMIS
                              (Mock)              Adapter             Adapter
                                (Mock)              (Mock)             (Mock)

                     ┌──────────────────────┐
                     │       REDIS          │
                     │ Cache / Background   │
                     │ Jobs                 │
                     └──────────────────────┘

                     ┌──────────────────────┐
                     │      AI SERVICE      │
                     │ Referral Assistant   │
                     └──────────────────────┘
```

---

# 8. Technology Stack

Yes — this is a good **core stack**, and I would keep it lean for the SIH prototype. I’d make one small improvement: explicitly add the supporting libraries that connect these technologies together.

Replace **Section 8** in `PROJECT_SPEC.md` with this:

# 8. Technology Stack

RAHAT will use a modern, modular and scalable technology stack. The SIH prototype should prioritize reliability, simplicity, rapid development and clear separation between frontend, backend, database and integration layers.

---

## 8.1 Frontend

### Core

```text
Next.js
TypeScript
Tailwind CSS
```

### Supporting Libraries

```text
shadcn/ui
React Hook Form
Zod
TanStack Query
Recharts
Leaflet / MapLibre
Dexie.js
IndexedDB
```

### Responsibilities

The frontend is responsible for:

* User interface
* Role-based dashboards
* Patient management screens
* Care request forms
* Facility recommendations
* Referral lifecycle tracking
* Follow-up management
* District analytics
* Maps
* Notifications
* Offline-first functionality
* API communication

### Architecture

```text
Next.js
   │
   ├── Pages / Routes
   ├── Components
   ├── Feature Modules
   ├── Forms & Validation
   ├── API Services
   ├── State / Server Cache
   └── Offline Storage
          │
          ▼
      FastAPI API
```

---

# 8.2 Backend

### Core

```text
Python
FastAPI
```

### Supporting Libraries

```text
SQLAlchemy
Alembic
Pydantic
JWT
bcrypt / Argon2
HTTPX
```

### Responsibilities

The backend is responsible for:

* Authentication
* Authorization
* RBAC
* Patient APIs
* Care request APIs
* Facility APIs
* Recommendation engine
* Referral lifecycle
* Follow-up management
* Notifications
* Dashboard analytics
* Audit logging
* Offline synchronization
* Government integration adapters
* AI service integration

### Architecture

```text
FastAPI
   │
   ├── API Routes
   ├── Schemas
   ├── Services
   ├── Repositories
   ├── Database Models
   ├── Recommendation Engine
   ├── Integration Adapters
   └── AI Service
```

---

# 8.3 Database

### Core

```text
PostgreSQL
PostGIS
```

### Responsibilities

PostgreSQL stores application data including:

```text
Users
Patients
Villages
Facilities
Facility Capabilities
Healthcare Professionals
Care Requests
Referrals
Referral Events
Follow-ups
Notifications
Audit Logs
```

PostGIS will support location-based functionality such as:

```text
Facility coordinates
Village coordinates
Distance calculations
Nearby facility searches
Geospatial analytics
```

The application should use SQLAlchemy as the database ORM and Alembic for schema migrations.

---

# 8.4 Infrastructure

### Core

```text
Docker
Docker Compose
Redis
```

### Docker Services

The local development environment should contain:

```text
frontend
backend
postgres
redis
```

Architecture:

```text
                 Browser
                    │
                    ▼
               Next.js
                    │
                    ▼
                FastAPI
                 /    \
                /      \
               ▼        ▼
         PostgreSQL    Redis
```

### Redis Responsibilities

Redis may be used for:

* caching,
* temporary data,
* background job coordination,
* notification queues,
* synchronization tasks.

Redis should not be used as the primary database.

PostgreSQL remains the system of record.

---

# 8.5 Testing

RAHAT will use multiple testing layers.

### Backend Unit & API Testing

```text
Pytest
HTTPX
```

Used for:

* API testing
* authentication testing
* RBAC testing
* recommendation engine testing
* referral state-machine testing
* database/service testing

---

### Frontend End-to-End Testing

```text
Playwright
```

The primary end-to-end test must validate the complete golden path:

```text
Login
 ↓
Create Patient
 ↓
Create Care Request
 ↓
Generate Recommendation
 ↓
Create Referral
 ↓
Facility Accepts Referral
 ↓
Patient Arrives
 ↓
Service Completed
 ↓
Back Referral
 ↓
Follow-up
 ↓
Close Care Journey
```

---

### Frontend Quality Checks

```text
ESLint
TypeScript Compiler
```

The frontend must pass:

```bash
npm run lint
npm run build
```

TypeScript must compile without errors.

---

# 8.6 AI

AI is an **assistive layer**, not the core decision-making system.

RAHAT must remain fully functional even if the AI service is unavailable.

### LLM API Use Cases

The LLM API may be used for:

```text
Referral summarization
Structured extraction
Recommendation explanation
Administrative assistance
```

---

## Referral Summarization

Convert lengthy frontline notes into a concise structured summary.

Example:

```text
Input:
Free-text referral notes

Output:
Patient summary
Required service
Relevant observations
Urgency indicators
Referral reason
```

---

## Structured Extraction

Convert unstructured text into structured care-request fields.

Example:

```text
Free-text notes
       ↓
      LLM
       ↓
Structured fields
       ↓
Healthcare worker reviews
       ↓
Care Request
```

The healthcare worker must be able to modify the extracted information before submission.

---

## Recommendation Explanation

The deterministic recommendation engine calculates the facility score.

AI may explain the existing recommendation in simple language.

The AI must **not modify the recommendation score**.

Architecture:

```text
Care Request
     │
     ▼
Deterministic Recommendation Engine
     │
     ▼
Facility Ranking
     │
     ▼
AI Explanation
```

---

## Administrative Assistance

AI may assist with non-clinical tasks such as:

```text
Summarizing referral queues
Drafting administrative notes
Explaining dashboard trends
Creating concise status summaries
```

---

# 8.7 AI Safety Boundaries

The AI system must NOT:

```text
Diagnose patients
Prescribe medicines
Replace doctors
Make autonomous clinical decisions
Override emergency protocols
Override healthcare professionals
Guarantee treatment outcomes
```

The core recommendation engine must remain deterministic and explainable.

---

# 8.8 Government Integration Architecture

RAHAT should use integration adapters rather than directly coupling the application to external systems.

```text
backend/app/integrations/

├── abdm/
├── esanjeevani/
├── ncd/
├── hmis/
└── emergency/
```

For the SIH prototype:

```text
RAHAT
  │
  ▼
Integration Interface
  │
  ▼
Mock Adapter
  │
  ▼
Synthetic Data
```

If authorized government APIs become available in a production deployment:

```text
RAHAT
  │
  ▼
Integration Interface
  │
  ▼
Official Government API
```

The prototype must not invent or falsely claim live government API integrations.

---

# 8.9 Overall Technology Architecture

```text
┌─────────────────────────────────────────────────────────┐
│                       RAHAT                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  FRONTEND                                               │
│  Next.js + TypeScript + Tailwind CSS                   │
│  shadcn/ui + TanStack Query + Dexie.js                 │
│                                                         │
└───────────────────────┬─────────────────────────────────┘
                        │
                     REST API
                        │
┌───────────────────────▼─────────────────────────────────┐
│                     BACKEND                             │
│              Python + FastAPI                          │
│                                                         │
│ Authentication │ Patients │ Referrals │ Follow-ups    │
│ Facilities     │ Analytics│ Notifications              │
│ Recommendation Engine │ Integration Adapters          │
│ AI Service                                                │
└───────────────┬───────────────────────┬─────────────────┘
                │                       │
                ▼                       ▼
┌────────────────────────┐    ┌──────────────────────────┐
│       PostgreSQL       │    │          Redis           │
│         + PostGIS      │    │                          │
│                        │    │ Cache / Queues / Jobs    │
└────────────────────────┘    └──────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────┐
│              External Integration Layer                 │
│                                                         │
│ ABDM │ eSanjeevani │ NCD │ HMIS │ Emergency Services │
│                                                         │
│ Prototype: Mock/Synthetic Adapters                     │
└─────────────────────────────────────────────────────────┘
```

---

# 8.10 Deployment Stack

For the SIH functional prototype:

```text
Frontend:
Next.js → Vercel

Backend:
FastAPI → Render / Railway / equivalent cloud service

Database:
Managed PostgreSQL + PostGIS

Redis:
Managed Redis

Source Control:
GitHub

Containerization:
Docker
```

The architecture should remain portable so that a future production deployment can move to:

```text
AWS
Azure
Government Cloud
NIC infrastructure
```

without requiring a complete rewrite.

---

# 8.11 Technology Selection Principle

The team should avoid unnecessary technologies.

The preferred approach is:

```text
Next.js
      +
FastAPI
      +
PostgreSQL/PostGIS
      +
Redis
      +
Docker
      +
Optional LLM
```

The application must prioritize:

```text
Reliability
Security
Maintainability
Explainability
Offline capability
Scalability
Fast development
```

over adding technologies simply to make the project appear complex.

**This version is better for the coding agent** because it tells it not only *what technologies to use*, but also **why each one exists and where it belongs**.

For now, don't start coding yet. **Save this replacement Section 8 → commit it → then we'll initialize the actual Next.js + FastAPI project.**


---

# 9. Repository Structure

The repository MUST follow this structure:

```text
swasthyasetu/
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── features/
│   ├── hooks/
│   ├── lib/
│   ├── services/
│   ├── types/
│   ├── public/
│   ├── tests/
│   ├── package.json
│   └── ...
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── permissions.py
│   │   │
│   │   ├── db/
│   │   │   ├── session.py
│   │   │   └── base.py
│   │   │
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── repositories/
│   │   ├── services/
│   │   ├── recommendation/
│   │   ├── integrations/
│   │   │   ├── abdm/
│   │   │   ├── esanjeevani/
│   │   │   ├── ncd/
│   │   │   ├── hmis/
│   │   │   └── emergency/
│   │   │
│   │   └── api/
│   │       └── v1/
│   │
│   ├── tests/
│   ├── alembic/
│   ├── requirements.txt
│   └── Dockerfile
│
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── database.md
│   └── demo.md
│
├── data/
│   ├── facilities.json
│   ├── services.json
│   ├── villages.json
│   └── demo_patients.json
│
├── scripts/
│   ├── seed_database.py
│   └── create_admin.py
│
├── docker/
│
├── tests/
│
├── .env.example
├── .gitignore
├── docker-compose.yml
├── PROJECT_SPEC.md
├── README.md
└── LICENSE
```

---

# 10. Core Modules

The application consists of these modules.

```text
1. Authentication
2. User Management
3. Patient Management
4. Care Requests
5. Facility Management
6. Facility Capability Management
7. Recommendation Engine
8. Referral Management
9. Referral Tracking
10. Back Referral
11. Follow-up Management
12. Notifications
13. District Dashboard
14. Facility Dashboard
15. Offline Synchronization
16. Government Integration Adapters
17. AI Referral Assistant
18. Audit Logging
```

---

# 11. Database Design

The main entities are:

```text
User
Role
Patient
Village
Facility
FacilityCapability
HealthcareProfessional
CareRequest
Referral
ReferralEvent
FollowUp
Notification
AuditLog
```

---

# 12. User Entity

Fields:

```text
id
full_name
phone
email
password_hash
role
facility_id
district
is_active
created_at
updated_at
```

---

# 13. Patient Entity

Fields:

```text
id
patient_code
full_name
age
gender
phone
village_id
address
emergency_contact
abha_reference
created_at
updated_at
```

Important:

For the prototype, `abha_reference` should contain a synthetic/demo identifier.

Never use real ABHA numbers.

---

# 14. Village Entity

Fields:

```text
id
name
district
state
latitude
longitude
population
connectivity_status
created_at
```

---

# 15. Facility Entity

Fields:

```text
id
name
facility_type
district
address
latitude
longitude
phone
operating_hours
is_active
created_at
updated_at
```

Facility types:

```text
AAM
SUB_CENTER
PHC
CHC
RURAL_HOSPITAL
DISTRICT_HOSPITAL
SPECIALTY_HOSPITAL
DIAGNOSTIC_CENTER
```

---

# 16. Facility Capability

Each facility can provide multiple capabilities.

Fields:

```text
id
facility_id
service_name
service_category
available
availability_status
capacity
current_load
specialist_required
diagnostic_required
operating_hours
updated_at
```

Examples:

```text
Emergency Care
Obstetrics
General Medicine
Pediatrics
Cardiology
Orthopedics
Laboratory
X-Ray
Ultrasound
CT
Dialysis
Mental Health
Eye Care
ENT
```

---

# 17. Healthcare Professional

Fields:

```text
id
user_id
facility_id
name
specialization
qualification
availability_status
created_at
updated_at
```

---

# 18. Care Request

A care request represents the patient's healthcare requirement before a formal referral.

Fields:

```text
id
patient_id
created_by
symptoms_summary
care_category
required_service
urgency
diagnostic_requirements
specialist_required
notes
created_at
updated_at
```

Urgency:

```text
LOW
MEDIUM
HIGH
EMERGENCY
```

---

# 19. Referral

Fields:

```text
id
patient_id
care_request_id
source_facility_id
target_facility_id
created_by
reason
urgency
status
expected_service
arrival_time
completion_time
back_referral_required
created_at
updated_at
```

---

# 20. Referral Event

Every state change must create an event.

Fields:

```text
id
referral_id
event_type
previous_status
new_status
performed_by
notes
timestamp
```

This creates an auditable timeline.

---

# 21. Follow-Up

Fields:

```text
id
patient_id
referral_id
assigned_to
scheduled_date
followup_type
instructions
status
completed_at
notes
created_at
updated_at
```

Status:

```text
PENDING
COMPLETED
MISSED
CANCELLED
```

---

# 22. Notification

Fields:

```text
id
user_id
referral_id
type
title
message
is_read
created_at
```

Prototype notification channels:

```text
IN_APP
```

Optional future channels:

```text
SMS
IVR
WHATSAPP
```

---

# 23. Audit Log

Fields:

```text
id
user_id
action
entity_type
entity_id
metadata
timestamp
ip_address
```

Do not store unnecessary sensitive information.

---

# 24. Database Relationships

```text
Village
   │
   └──< Patient

Facility
   │
   ├──< User
   ├──< HealthcareProfessional
   └──< FacilityCapability

Patient
   │
   ├──< CareRequest
   ├──< Referral
   └──< FollowUp

CareRequest
   │
   └──< Referral

Referral
   │
   ├──< ReferralEvent
   └──< FollowUp

User
   │
   ├──< CareRequest
   ├──< Referral
   └──< AuditLog
```

---

# 25. Referral State Machine

The referral lifecycle is the heart of RAHAT.

```text
CREATED
   ↓
PENDING_ACCEPTANCE
   ↓
ACCEPTED
   ↓
PATIENT_NOTIFIED
   ↓
DEPARTED
   ↓
ARRIVED
   ↓
IN_SERVICE
   ↓
COMPLETED
   ↓
BACK_REFERRED
   ↓
FOLLOW_UP
   ↓
CLOSED
```

Alternative path:

```text
PENDING_ACCEPTANCE
        ↓
     REJECTED
        ↓
     REROUTED
        ↓
NEW FACILITY
```

---

# 26. Referral Rules

### CREATED

Referral has been generated.

### PENDING_ACCEPTANCE

Receiving facility must review the referral.

### ACCEPTED

Receiving facility confirms it can handle the patient.

### PATIENT_NOTIFIED

Patient/frontline worker has been informed.

### DEPARTED

Patient has started travelling.

### ARRIVED

Patient reached the receiving facility.

### IN_SERVICE

Required healthcare service is being provided.

### COMPLETED

Required service has been completed.

### BACK_REFERRED

Patient is sent back to a local facility for continuing care.

### FOLLOW_UP

Local follow-up is required.

### CLOSED

Care journey has been completed.

---

# 27. Referral Event Rules

Every status transition must:

1. Validate current state.
2. Validate user permission.
3. Update referral.
4. Create ReferralEvent.
5. Create notification where applicable.
6. Create AuditLog.
7. Return updated referral.

No state change should happen silently.

---

# 28. Smart Facility Recommendation Engine

RAHAT must recommend facilities based on the patient's care requirement.

It must NOT diagnose the patient.

The recommendation engine receives:

```text
required_service
urgency
diagnostic_requirements
specialist_required
patient_location
facility_capabilities
facility_distance
facility_availability
facility_workload
```

---

# 29. Recommendation Algorithm

Use a deterministic weighted scoring system for the prototype.

Example:

```text
Service Match       = 30%
Distance            = 20%
Diagnostic Match    = 20%
Specialist Match    = 15%
Availability        = 10%
Workload             = 5%
```

Total:

```text
100%
```

---

# 30. Recommendation Score

Conceptually:

```text
score =
    service_match * 0.30
  + distance_score * 0.20
  + diagnostic_match * 0.20
  + specialist_match * 0.15
  + availability_score * 0.10
  + workload_score * 0.05
```

Normalize all components between:

```text
0 and 100
```

Final score:

```text
0–100
```

---

# 31. Recommendation Output

The API should return:

```json
{
  "facility_id": "facility-001",
  "facility_name": "District Hospital Demo",
  "score": 87.5,
  "reasons": [
    "Required service available",
    "Required diagnostic available",
    "Specialist available",
    "Within acceptable travel distance"
  ]
}
```

Return the top 3 facilities.

---

# 32. Recommendation Safety Rules

The engine must:

* never claim to diagnose,
* never guarantee treatment,
* never override an emergency protocol,
* never recommend an inactive facility,
* never recommend a facility that lacks the required service,
* clearly show why a facility was recommended.

For emergencies, the prototype should prioritize:

```text
Emergency capability
+
Availability
+
Distance
```

over ordinary scoring.

---

# 33. Explainable Recommendations

The frontend must show:

```text
Why this facility?
```

Example:

```text
✓ Required service available
✓ Diagnostic capability available
✓ Specialist available
✓ 18 km away
✓ Currently accepting referrals
```

Avoid presenting the recommendation as an opaque AI decision.

---

# 34. API Design

Base URL:

```text
/api/v1
```

---

## Authentication

```http
POST /auth/login
POST /auth/logout
GET /auth/me
POST /auth/refresh
```

---

## Users

```http
GET /users
GET /users/{id}
POST /users
PATCH /users/{id}
```

---

## Patients

```http
POST /patients
GET /patients
GET /patients/{id}
PATCH /patients/{id}
```

---

## Care Requests

```http
POST /care-requests
GET /care-requests
GET /care-requests/{id}
PATCH /care-requests/{id}
```

---

## Facilities

```http
GET /facilities
GET /facilities/{id}
GET /facilities/nearby
POST /facilities
PATCH /facilities/{id}
```

---

## Recommendations

```http
POST /recommendations
```

Request:

```json
{
  "care_request_id": "request-id"
}
```

Response:

```json
{
  "recommendations": [
    {
      "facility_id": "facility-001",
      "score": 87.5,
      "reasons": []
    }
  ]
}
```

---

## Referrals

```http
POST /referrals
GET /referrals
GET /referrals/{id}
POST /referrals/{id}/accept
POST /referrals/{id}/reject
POST /referrals/{id}/notify
POST /referrals/{id}/depart
POST /referrals/{id}/arrive
POST /referrals/{id}/start-service
POST /referrals/{id}/complete
POST /referrals/{id}/back-referral
POST /referrals/{id}/close
```

---

## Follow-Up

```http
POST /followups
GET /followups
GET /followups/{id}
PATCH /followups/{id}
POST /followups/{id}/complete
```

---

## Dashboard

```http
GET /dashboard/overview
GET /dashboard/referrals
GET /dashboard/facilities
GET /dashboard/bottlenecks
GET /dashboard/followups
```

---

## Notifications

```http
GET /notifications
POST /notifications/{id}/read
```

---

# 35. API Standards

All APIs must:

* use JSON,
* use HTTP status codes correctly,
* validate request bodies,
* return structured errors,
* use Pydantic schemas,
* use authentication where required,
* enforce RBAC,
* never expose password hashes.

Example error:

```json
{
  "detail": "Referral cannot be completed before arrival."
}
```

---

# 36. Frontend Architecture

Use Next.js App Router.

Main route structure:

```text
/app
  /login
  /dashboard
  /patients
  /patients/[id]
  /care-requests
  /referrals
  /referrals/[id]
  /facilities
  /facilities/[id]
  /followups
  /analytics
  /settings
```

---

# 37. Frontend Layout

The application should have:

```text
┌──────────────────────────────────────────────┐
│ RAHAT                  Notifications  User  │
├──────────────┬───────────────────────────────┤
│              │                               │
│ Dashboard    │                               │
│ Patients     │         Main Content          │
│ Care         │                               │
│ Requests     │                               │
│ Referrals    │                               │
│ Facilities   │                               │
│ Follow-ups   │                               │
│ Analytics    │                               │
│              │                               │
└──────────────┴───────────────────────────────┘
```

The UI must be:

* clean,
* professional,
* healthcare-oriented,
* responsive,
* accessible,
* easy for low-digital-literacy users.

---

# 38. Frontline Dashboard

Display:

```text
Today's Tasks
Active Referrals
Pending Follow-ups
Patients
Urgent Cases
Offline Sync Status
```

Primary actions:

```text
+ Register Patient
+ Create Care Request
+ Start Referral
```

---

# 39. Patient Screen

Show:

```text
Patient Information
Village
Contact
Care Requests
Active Referrals
Previous Referrals
Follow-ups
```

Do not overload the interface with unnecessary clinical information.

---

# 40. Care Request Screen

Fields:

```text
Patient
Care Category
Required Service
Urgency
Symptoms Summary
Diagnostic Requirements
Specialist Required
Additional Notes
```

Button:

```text
Find Suitable Facilities
```

---

# 41. Recommendation Screen

Show top 3 facilities.

Each card should contain:

```text
Facility Name
Distance
Service Match
Diagnostics
Specialist
Availability
Recommendation Score
Reasons
```

Primary CTA:

```text
Create Referral
```

---

# 42. Referral Tracking Screen

Show a visual timeline:

```text
✓ Referral Created
      ↓
✓ Hospital Accepted
      ↓
✓ Patient Notified
      ↓
✓ Patient Departed
      ↓
● Patient Arrived
      ↓
○ Service
      ↓
○ Completed
      ↓
○ Follow-up
```

This is one of the most important screens for the SIH demo.

---

# 43. Receiving Facility Dashboard

Sections:

```text
Pending Referrals
Accepted Referrals
Today's Arrivals
Active Services
Completed Referrals
Back Referrals
```

Each referral should have:

```text
Patient
Source Facility
Required Service
Urgency
Referral Time
Status
```

Actions:

```text
Accept
Reject
Mark Arrived
Start Service
Complete
Back Refer
```

---

# 44. District Dashboard

Display KPI cards:

```text
Active Referrals
Completed Referrals
Delayed Referrals
Care Completion Rate
Follow-ups Due
Facilities with High Load
```

Charts:

```text
Referral Status Distribution
Referral Completion Trend
Facility Workload
Average Referral Time
Follow-up Completion
```

Map:

```text
Facility locations
Referral hotspots
Underserved villages
```

Use synthetic data for the prototype.

---

# 45. Offline-First Architecture

The frontline application should support offline operations.

Technology:

```text
IndexedDB
+
Dexie.js
```

When offline:

```text
User action
    ↓
Local database
    ↓
Pending sync queue
```

When online:

```text
Internet restored
       ↓
Sync queue
       ↓
Backend API
       ↓
Server confirms
       ↓
Local record marked synced
```

---

# 46. Sync Queue

Each offline operation should contain:

```text
id
operation_type
entity_type
entity_id
payload
created_at
sync_status
retry_count
```

Statuses:

```text
PENDING
SYNCING
SYNCED
FAILED
```

---

# 47. Offline UI

The frontend must clearly display:

```text
● Online
```

or

```text
● Offline — Changes will sync automatically
```

Also show:

```text
3 items waiting to sync
```

---

# 48. Government Integration Architecture

RAHAT must use adapters.

Structure:

```text
integrations/
├── abdm/
├── esanjeevani/
├── ncd/
├── hmis/
└── emergency/
```

Each adapter should expose an internal interface.

Example:

```python
class HealthSystemAdapter:
    async def get_patient(...):
        pass

    async def create_referral(...):
        pass

    async def get_facility(...):
        pass
```

---

# 49. Prototype Integration Rule

For SIH:

```text
Real Government API unavailable
        ↓
Mock Adapter
        ↓
Synthetic Response
```

Do not invent real API endpoints.

Do not claim that the prototype has live government integration unless actual authorized connectivity exists.

---

# 50. ABDM Adapter

Prototype responsibilities:

```text
Mock patient identity reference
Mock facility lookup
Mock health record reference
```

Future production integration:

```text
Authorized ABDM APIs
```

---

# 51. eSanjeevani Adapter

Prototype responsibilities:

```text
Mock teleconsultation referral
Mock specialist routing
Mock consultation status
```

RAHAT should not attempt to recreate eSanjeevani.

---

# 52. NCD Adapter

Prototype responsibilities:

```text
Mock screening result
Mock referral source
Mock follow-up information
```

RAHAT should coordinate the referral rather than replace the NCD system.

---

# 53. Emergency Adapter

Prototype:

```text
Mock emergency transport availability
```

Future:

```text
Authorized emergency service integration
```

---

# 54. AI Referral Assistant

AI is an optional assistance layer.

It should NOT control the referral engine.

Architecture:

```text
User Input
    ↓
Structured Care Request
    ↓
Deterministic Recommendation Engine
    ↓
Facility Recommendations
    ↓
AI Explanation Layer
```

Not:

```text
Symptoms
   ↓
LLM
   ↓
Diagnosis
```

---

# 55. AI Features

## Feature 1 — Referral Summary

Input:

```text
Free-text notes
```

Output:

```text
Patient summary
Required service
Urgency indicators
Relevant information
```

The output must be clearly marked as AI-generated assistance.

---

## Feature 2 — Structured Extraction

Convert:

```text
"Patient has been having severe abdominal pain since yesterday..."
```

into structured fields such as:

```text
care_category
required_service
urgency
diagnostic_requirements
```

A healthcare worker must be able to review/edit the result.

---

## Feature 3 — Recommendation Explanation

AI may explain an already-calculated recommendation.

It must never modify the score.

---

# 56. AI Safety

The AI system must:

* not diagnose,
* not prescribe,
* not invent medical facts,
* not override healthcare professionals,
* not override emergency protocols,
* clearly indicate uncertainty,
* allow human review,
* log AI-assisted actions.

---

# 57. Authentication

Use JWT-based authentication.

Login:

```text
POST /auth/login
```

Response:

```json
{
  "access_token": "...",
  "token_type": "bearer"
}
```

Frontend should store authentication securely according to the chosen deployment architecture.

---

# 58. Password Security

Passwords must:

* never be stored in plaintext,
* be hashed using bcrypt/Argon2,
* never be returned by APIs.

---

# 59. Authorization

Every protected API must verify:

```text
Authentication
+
Role
+
Resource permission
```

Example:

An ASHA should not be able to:

```text
modify facility capacity
```

A district administrator should not be able to:

```text
change a patient's clinical treatment
```

---

# 60. Privacy

The prototype must use synthetic data.

Never include:

```text
Real patient names
Real phone numbers
Real ABHA IDs
Real medical records
```

in GitHub.

---

# 61. Environment Variables

Use:

```text
.env
```

Never commit `.env`.

Provide:

```text
.env.example
```

Example:

```text
DATABASE_URL=
REDIS_URL=
JWT_SECRET=
AI_API_KEY=
NEXT_PUBLIC_API_URL=
```

---

# 62. Logging

Backend logs should include:

```text
timestamp
request
endpoint
status
duration
error
```

Never log:

```text
passwords
tokens
sensitive patient information
```

---

# 63. Testing Strategy

Testing must happen throughout development.

## Backend

Use:

```text
Pytest
HTTPX
```

Test:

```text
Authentication
RBAC
Patient creation
Care request creation
Facility search
Recommendation scoring
Referral transitions
Invalid transitions
Follow-up
Dashboard
```

---

# 64. Recommendation Tests

Test cases:

### Case 1

Facility has all required services and is nearby.

Expected:

```text
High score
```

### Case 2

Facility lacks required service.

Expected:

```text
Facility excluded
```

### Case 3

Facility unavailable.

Expected:

```text
Facility excluded or heavily penalized
```

### Case 4

Emergency request.

Expected:

```text
Emergency-capable facility prioritized
```

---

# 65. Referral State Tests

Valid:

```text
CREATED → PENDING_ACCEPTANCE
PENDING_ACCEPTANCE → ACCEPTED
ACCEPTED → PATIENT_NOTIFIED
PATIENT_NOTIFIED → DEPARTED
DEPARTED → ARRIVED
ARRIVED → IN_SERVICE
IN_SERVICE → COMPLETED
COMPLETED → BACK_REFERRED
BACK_REFERRED → FOLLOW_UP
FOLLOW_UP → CLOSED
```

Invalid:

```text
CREATED → COMPLETED
```

must fail.

---

# 66. Frontend Testing

Use:

```text
Playwright
```

Main end-to-end test:

```text
Login
 ↓
Create patient
 ↓
Create care request
 ↓
Get recommendations
 ↓
Create referral
 ↓
Hospital accepts
 ↓
Patient arrives
 ↓
Service completed
 ↓
Back referral
 ↓
Follow-up
 ↓
Close care journey
```

This is the **golden path**.

---

# 67. UI Quality Requirements

The frontend must pass:

```text
npm run lint
npm run build
```

No TypeScript errors.

No obvious console errors.

No broken navigation.

All loading states must be handled.

All API errors must show user-friendly messages.

---

# 68. Accessibility

The frontend should support:

```text
Keyboard navigation
Readable typography
High contrast
Clear labels
Accessible buttons
Accessible forms
ARIA where required
```

Use simple language wherever possible.

---

# 69. Error Handling

Frontend should display meaningful messages.

Bad:

```text
500 Internal Server Error
```

Better:

```text
Unable to submit the referral right now.
Your information is saved locally and will sync when the connection is restored.
```

---

# 70. Loading States

Use:

```text
Skeletons
Spinners
Disabled buttons
Progress indicators
```

Never leave users wondering whether an action worked.

---

# 71. Notification System

Notifications should be generated for important events.

Examples:

```text
Referral accepted
Referral rejected
Patient arrived
Service completed
Follow-up due
Referral delayed
```

---

# 72. Delay Detection

A referral should be considered delayed when it remains in an expected state beyond its configured threshold.

Example:

```text
PENDING_ACCEPTANCE > threshold
```

creates:

```text
DELAYED
```

The threshold must be configurable.

Do not hard-code medical response times without a validated policy.

---

# 73. District Bottleneck Detection

The dashboard should identify:

```text
Facilities receiving unusually high referral volume
Facilities with repeated rejection
Facilities with long pending times
Services with limited availability
Villages with repeated referral delays
```

Use analytics/rules rather than AI for the prototype.

---

# 74. Data Seeding

The prototype must include realistic synthetic data.

Seed:

```text
1 district
5–10 villages
5–10 facilities
10–20 users
20–50 patients
30+ care requests
30+ referrals
follow-up records
facility capabilities
```

The exact numbers can be adjusted for demo performance.

---

# 75. Demo Data

Use recognizable but fictional names.

Example:

```text
District: Demo District
Village: Rampur
Village: Shivnagar
Village: Devgaon
```

Facilities:

```text
Rampur AAM
Shivnagar PHC
Central CHC
Demo Rural Hospital
District Hospital Demo
```

Do not represent fictional facilities as real government facilities.

---

# 76. Demo Scenario

The primary SIH demonstration should follow one patient.

Example:

```text
Patient:
Ramesh Kumar

Village:
Rampur

Initial Facility:
Rampur AAM

Requirement:
Specialist evaluation + diagnostic service
```

Flow:

```text
ASHA logs in
       ↓
Finds patient
       ↓
Creates care request
       ↓
Medical Officer reviews
       ↓
RAHAT recommends facilities
       ↓
District Hospital selected
       ↓
Referral created
       ↓
Hospital accepts
       ↓
Patient notified
       ↓
Patient departs
       ↓
Patient arrives
       ↓
Service begins
       ↓
Service completed
       ↓
Back referral
       ↓
Follow-up assigned
       ↓
Follow-up completed
       ↓
Referral closed
```

---

# 77. SIH Demo Dashboard

At the end of the demonstration, show:

```text
Care Completion Rate
Active Referrals
Completed Referrals
Delayed Referrals
Follow-ups Due
Facility Bottlenecks
```

The dashboard should visibly demonstrate the impact of the platform.

---

# 78. Core Product KPI

Primary KPI:

```text
Care Completion Rate
```

Formula:

```text
Completed Care Journeys
----------------------- × 100
Eligible Referrals
```

---

# 79. Secondary KPIs

```text
Referral Acceptance Rate
Referral Completion Rate
Average Referral Completion Time
Average Acceptance Time
Back-Referral Rate
Follow-up Completion Rate
Referral Rejection Rate
Delayed Referral Rate
```

---

# 80. Impact Metrics

The prototype should demonstrate:

```text
Reduced referral uncertainty
Reduced manual coordination
Improved referral visibility
Improved follow-up tracking
Better facility selection
Better district-level visibility
```

Do not claim actual real-world percentage improvements unless supported by measured pilot data.

---

# 81. Docker Architecture

Docker services:

```text
frontend
backend
postgres
redis
```

Example:

```text
docker-compose.yml
```

Conceptual architecture:

```text
Browser
   ↓
Frontend Container
   ↓
Backend Container
   ↓
PostgreSQL Container

Backend
   ↓
Redis
```

---

# 82. Docker Requirements

Each service must have:

```text
Dockerfile
Health check
Environment configuration
```

Backend must wait for the database to become available.

Database migrations should run before application startup where appropriate.

---

# 83. Local Development

The project should eventually run using:

```bash
docker compose up --build
```

Frontend:

```text
http://localhost:3000
```

Backend:

```text
http://localhost:8000
```

API documentation:

```text
http://localhost:8000/docs
```

---

# 84. Deployment Architecture

Prototype deployment:

```text
                     Internet
                         │
                         ▼
                    Frontend
                    Vercel
                         │
                         ▼
                     FastAPI
               Render / Railway
                         │
              ┌──────────┴─────────┐
              ▼                    ▼
         PostgreSQL              Redis
       Managed Database      Managed Redis
```

Production could later move to:

```text
AWS
Azure
Government Cloud
NIC infrastructure
```

depending on official deployment requirements.

---

# 85. Deployment Requirements

Frontend:

```text
Production build
Environment variables
API URL
```

Backend:

```text
Production ASGI server
Database URL
JWT secret
CORS configuration
Environment variables
```

Database:

```text
PostgreSQL
Automated backups
Migration management
```

---

# 86. CORS

Only configured frontend domains should be allowed in production.

Do not use:

```text
allow_origins=["*"]
```

for production authentication APIs.

---

# 87. HTTPS

Production deployment must use HTTPS.

Never send authentication credentials over unencrypted HTTP.

---

# 88. API Versioning

All APIs must be versioned:

```text
/api/v1/
```

Future breaking changes can use:

```text
/api/v2/
```

---

# 89. Git Development Strategy

Do not build the entire application in one AI coding-agent prompt.

Use incremental vertical slices.

Development sequence:

```text
Specification
 ↓
Repository Setup
 ↓
Frontend Shell
 ↓
Backend Shell
 ↓
Database
 ↓
Authentication
 ↓
Patients
 ↓
Care Requests
 ↓
Facilities
 ↓
Recommendation Engine
 ↓
Referral Lifecycle
 ↓
Facility Dashboard
 ↓
Follow-ups
 ↓
District Dashboard
 ↓
Offline Support
 ↓
AI Assistant
 ↓
Testing
 ↓
Docker
 ↓
Deployment
```

---

# 90. Development Chunk Rules

For every implementation chunk:

```text
1. Read PROJECT_SPEC.md
2. Understand current chunk
3. Inspect existing code
4. Implement only requested scope
5. Run tests
6. Run lint
7. Run build
8. Fix errors
9. Review changes
10. Commit
```

The AI coding agent must NOT redesign the architecture without permission.

---

# 91. AI Coding Agent Instructions

The coding agent must follow this rule:

> PROJECT_SPEC.md is the source of truth.

Before implementing any feature:

```text
Read PROJECT_SPEC.md.
```

The agent must:

* follow the defined architecture,
* avoid unnecessary dependencies,
* avoid creating duplicate systems,
* avoid inventing government APIs,
* use synthetic data,
* preserve existing functionality,
* write tests,
* run validation commands,
* report changed files.

---

# 92. Implementation Prompt Template

Use this structure when giving work to an AI coding agent:

```text
Read PROJECT_SPEC.md before making any changes.

You are implementing only the current development chunk.

Do not redesign the architecture.

Do not invent government APIs.

Use synthetic/demo data where integrations are unavailable.

Keep the implementation minimal but production-quality.

After implementation:

1. Run relevant tests.
2. Run lint.
3. Run type checking.
4. Run build where applicable.
5. Fix any errors.
6. Summarize changed files.
7. Summarize tests performed.
8. Do not modify unrelated modules.
```

---

# 93. Development Phases

## Phase 0 — Specification

Deliverables:

```text
PROJECT_SPEC.md
README.md
architecture documentation
```

---

## Phase 1 — Repository Setup

Deliver:

```text
Git repository
Next.js app
FastAPI app
Docker setup
environment templates
```

---

## Phase 2 — Database

Deliver:

```text
PostgreSQL
SQLAlchemy
Alembic
Models
Relationships
Seed data
```

---

## Phase 3 — Authentication

Deliver:

```text
Login
JWT
RBAC
Protected routes
```

---

## Phase 4 — Patient Management

Deliver:

```text
Patient creation
Patient search
Patient profile
```

---

## Phase 5 — Care Requests

Deliver:

```text
Care request form
Care request API
Urgency
Service requirements
```

---

## Phase 6 — Facility Management

Deliver:

```text
Facility list
Facility profile
Capabilities
Diagnostics
Specialists
Availability
```

---

## Phase 7 — Recommendation Engine

Deliver:

```text
Weighted scoring
Top 3 recommendations
Explainable reasons
```

---

## Phase 8 — Referral Lifecycle

Deliver:

```text
Create referral
Accept
Reject
Notify
Depart
Arrive
Service
Complete
Back-referral
Follow-up
Close
```

---

## Phase 9 — Dashboards

Deliver:

```text
Frontline dashboard
Facility dashboard
District dashboard
```

---

## Phase 10 — Offline Support

Deliver:

```text
IndexedDB
Sync queue
Offline indicator
Automatic synchronization
```

---

## Phase 11 — AI

Deliver:

```text
Referral summarization
Structured extraction
Recommendation explanation
```

AI must remain optional.

The core application must work without AI.

---

## Phase 12 — Testing

Deliver:

```text
Unit tests
API tests
Recommendation tests
State machine tests
E2E tests
```

---

## Phase 13 — Docker

Deliver:

```text
Dockerfiles
docker-compose.yml
health checks
environment configuration
```

---

## Phase 14 — Deployment

Deliver:

```text
Frontend deployment
Backend deployment
PostgreSQL
Redis
Environment variables
HTTPS
```

---

# 94. Definition of Done

A feature is NOT considered complete until:

```text
✓ Code implemented
✓ API works
✓ Frontend connected
✓ Validation added
✓ Error handling added
✓ Tests written
✓ Tests passing
✓ Lint passing
✓ Build passing
✓ No obvious console errors
✓ Documentation updated
```

---

# 95. Minimum Viable Prototype

The absolute minimum functional prototype must support:

```text
Login
 ↓
Patient
 ↓
Care Request
 ↓
Facility Recommendation
 ↓
Referral
 ↓
Hospital Acceptance
 ↓
Referral Tracking
 ↓
Service Completion
 ↓
Back Referral
 ↓
Follow-up
 ↓
District Dashboard
```

If time becomes limited, prioritize this flow over secondary features.

---

# 96. Feature Priority

## P0 — Must Have

```text
Authentication
Patients
Care Requests
Facilities
Recommendation Engine
Referral Lifecycle
Facility Dashboard
Follow-up
District Dashboard
Synthetic Data
```

## P1 — Should Have

```text
Offline Mode
Maps
Notifications
Audit Logs
Docker
E2E Tests
```

## P2 — Nice to Have

```text
AI Assistant
SMS
IVR
Advanced Government Integrations
Advanced Analytics
Predictive Models
```

---

# 97. What NOT to Build

RAHAT should NOT become:

```text
✗ Generic hospital finder
✗ Generic telemedicine application
✗ Generic health-record application
✗ New ABHA system
✗ New NCD screening platform
✗ New ambulance tracking platform
✗ AI diagnosis application
✗ AI doctor
✗ Online pharmacy
✗ Generic symptom checker
```

The core product is:

> **Healthcare referral coordination and care completion.**

---

# 98. Prototype Data Policy

All data must be:

```text
Synthetic
Non-identifiable
Demo-safe
```

Example patient:

```text
RAHAT-P-0001
```

not an actual government identifier.

---

# 99. Performance Goals

For the prototype:

```text
API response target:
< 500 ms for ordinary database requests

Recommendation response:
< 1 second

Dashboard initial load:
< 3 seconds under normal demo conditions
```

These are prototype engineering targets, not government service-level commitments.

---

# 100. Security Checklist

Before deployment:

```text
[ ] Password hashing
[ ] JWT security
[ ] RBAC
[ ] HTTPS
[ ] CORS configured
[ ] Environment secrets
[ ] No secrets in Git
[ ] No real patient data
[ ] Audit logs
[ ] Input validation
[ ] SQL injection protection
[ ] Authentication on protected endpoints
[ ] Authorization checks
```

---

# 101. Git Ignore Requirements

`.gitignore` must include:

```text
.env
.env.*
!.env.example

__pycache__/
*.pyc

node_modules/

.next/

.venv/
venv/

.pytest_cache/

coverage/

.DS_Store

*.log
```

---

# 102. README Requirements

README.md should explain:

```text
Project
Problem
Solution
Architecture
Features
Tech Stack
Installation
Environment Variables
Running Locally
API Documentation
Testing
Docker
Deployment
Demo Credentials
SIH Context
```

README should not replace PROJECT_SPEC.md.

PROJECT_SPEC.md is the detailed technical source of truth.

---

# 103. Documentation Requirements

Maintain:

```text
docs/architecture.md
docs/api.md
docs/database.md
docs/demo.md
```

Documentation must be updated when major architecture changes occur.

---

# 104. SIH Presentation Narrative

The presentation should follow:

```text
Existing healthcare ecosystem
        ↓
Multiple services already exist
        ↓
Coordination remains difficult
        ↓
Referral is created
        ↓
But care completion is not guaranteed
        ↓
RAHAT coordinates the journey
        ↓
Existing systems remain intact
        ↓
Referral becomes trackable
        ↓
Care completion becomes measurable
```

---

# 105. SIH Differentiator

RAHAT's central differentiator:

> **A coordination and continuity layer across existing rural healthcare services, focused on completing the referral journey rather than creating another standalone healthcare service.**

---

# 106. Judge Demonstration Story

During the demonstration, explain:

```text
"Suppose a patient in a remote village needs a service
that is not available at the local facility."

"The frontline worker creates a care request."

"RAHAT evaluates the required service and available
facility capabilities."

"It recommends suitable facilities based on capability,
distance, diagnostics, specialist availability and
operational status."

"The referral is sent to the receiving facility."

"The receiving facility accepts it."

"The patient journey can now be tracked."

"When treatment is completed, the patient can be
back-referred."

"The local healthcare worker receives the follow-up task."

"Once follow-up is completed, the care journey is closed."

"The district administrator can see where referrals are
getting delayed and where bottlenecks exist."
```

---

# 107. Critical SIH Claim Boundary

Never say:

```text
"We have integrated all government systems."
```

unless real authorized APIs have actually been connected.

Instead say:

```text
"The architecture is integration-ready and uses mock
connectors for the prototype. Production deployment can
connect authorized government APIs through these adapters."
```

---

# 108. Critical AI Claim Boundary

Never say:

```text
"AI decides where the patient should go."
```

Say:

```text
"The recommendation engine uses transparent deterministic
rules. AI is used only as an assistive layer for referral
summarization, structured extraction and explanation."
```

---

# 109. Critical Healthcare Claim Boundary

RAHAT is:

```text
A coordination platform.
```

RAHAT is NOT:

```text
A diagnostic system.
```

Clinical decisions remain with qualified healthcare professionals.

---

# 110. Final Product Architecture

The final prototype should conceptually operate as:

```text
                    RAHAT
                      │
        ┌─────────────┼──────────────┐
        │             │              │
        ▼             ▼              ▼
   Frontline       Facility       District
   Interface       Interface      Dashboard
        │             │              │
        └─────────────┼──────────────┘
                      │
                      ▼
                FastAPI Backend
                      │
       ┌──────────────┼──────────────┐
       │              │              │
       ▼              ▼              ▼
   PostgreSQL      Redis       Recommendation
   + PostGIS                    Engine
       │
       └──────────────────────────────┐
                                      │
                                      ▼
                             Integration Adapters
                                      │
                    ┌─────────────────┼────────────────┐
                    ▼                 ▼                ▼
                  ABDM           eSanjeevani        NCD/HMIS
                  Mock              Mock             Mock

                                      │
                                      ▼
                               AI Assistant
                               (Optional)
```

---

# 111. Final Success Criteria

RAHAT is successful as an SIH functional prototype if a judge can see:

```text
1. A rural patient exists
2. A care requirement is created
3. Suitable facilities are identified
4. A referral is generated
5. A facility receives it
6. The facility accepts it
7. The patient's journey is tracked
8. The service is completed
9. Back-referral is generated
10. Follow-up is completed
11. The referral is closed
12. District administrators can see the outcome
```

The complete golden-path demo must work using synthetic data without requiring external government systems.

---

# 112. Golden Rule for Development

> **Build the smallest complete healthcare journey first.**

Do not build 50 disconnected features.

Build:

```text
Patient
  ↓
Care Request
  ↓
Recommendation
  ↓
Referral
  ↓
Acceptance
  ↓
Arrival
  ↓
Service
  ↓
Completion
  ↓
Back Referral
  ↓
Follow-up
  ↓
Closure
```

Once this works end-to-end, add:

```text
Offline
Analytics
Maps
Notifications
AI
Government adapters
Deployment
```

---

# END OF PROJECT SPECIFICATION
