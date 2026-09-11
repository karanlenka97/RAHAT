# RAHAT Architecture Overview

## System Foundation (Phase 1 & Phase 2)

RAHAT (Rural Assistance & Healthcare Access Tele-network) / SwasthyaSetu is designed as a high-reliability, low-latency distributed healthcare referral and access platform.

### High-Level Architecture

```
                +-------------------------+
                |     Client Layer        |
                |   Next.js (App Router)  |
                +------------+------------+
                             |
                             | HTTP/REST
                             v
                +-------------------------+
                |     API Gateway / Core  |
                |     FastAPI (Python)    |
                +-----+-------------+-----+
                      |             |
           PostgreSQL |             | Redis Cache
             +PostGIS |             | & Queues
                      v             v
                +-----------+ +-----------+
                | Spatial DB| |   Redis   |
                +-----------+ +-----------+
```

### Database Entities & Domain Models (Phase 2)

| Entity | Model | Table | Key Description |
| :--- | :--- | :--- | :--- |
| **Role** | `Role` | `roles` | System RBAC with JSON permissions matrix |
| **User** | `User` | `users` | Clinical & operational accounts with hashed passwords |
| **Village** | `Village` | `villages` | Habitational units with PostGIS `POINT` GPS coordinates |
| **Facility** | `Facility` | `facilities` | Multi-tier hospitals/clinics with PostGIS location & bed tracking |
| **FacilityCapability** | `FacilityCapability` | `facility_capabilities` | Specialties, NICU, trauma care, and diagnostic availability |
| **HealthcareProfessional** | `HealthcareProfessional` | `healthcare_professionals` | Doctors, nurses, ASHAs, ANMs with councils and specialties |
| **Patient** | `Patient` | `patients` | Patient index with ABHA ID, anonymous code, and history |
| **CareRequest** | `CareRequest` | `care_requests` | Primary triage, chief complaints, and provisional diagnosis |
| **Referral** | `Referral` | `referrals` | Core inter-facility transfer workflow with priorities and status |
| **ReferralEvent** | `ReferralEvent` | `referral_events` | Immutable transition and dispatch logs |
| **FollowUp** | `FollowUp` | `follow_ups` | Post-discharge monitoring by ASHA / community health workers |
| **Notification** | `Notification` | `notifications` | Critical alerts, triage notifications, and system events |
| **AuditLog** | `AuditLog` | `audit_logs` | Tamper-evident compliance and security audit logs |

### Geospatial & PostGIS Capabilities

- **Spatial Indexing**: R-Tree spatial indexing on `villages.location` and `facilities.location` (SRID 4326).
- **Nearby Queries**: Native `ST_DWithin` and `ST_Distance` support for finding closest capable facilities.
