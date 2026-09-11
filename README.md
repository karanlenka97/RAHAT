# RAHAT (SwasthyaSetu)
## Rural Healthcare Access & Referral Assistance Technology

> **Smart India Hackathon (SIH 2026) Official Prototype**  
> An intelligent, offline-resilient, geospatial healthcare referral, dynamic bed-allocation, and closed-loop care completion platform for rural and tribal healthcare networks.

---

## 🌟 Overview & Problem Statement

In rural, tribal, and remote districts across India, inter-facility patient transfers frequently fail because frontline healthcare workers lack real-time visibility into receiving hospital capabilities, available beds, on-duty specialists, and diagnostic readiness. This causes fatal transit delays, duplicate referrals, and uncoordinated care.

### The RAHAT Differentiator
> *"RAHAT does not merely create a referral. RAHAT ensures that the referral becomes completed care."*

RAHAT connects **frontline workers (ASHA, ANM, CHO)**, **receiving facilities (PHC, CHC, SDH, DH)**, and **district administrators** into a synchronized, offline-resilient, deterministic care network.

---

## 🏗️ 14-Phase Implementation Summary

| Phase | Milestone Name | Key Deliverables | Status |
| :---: | :--- | :--- | :---: |
| **01** | **Foundation** | Technology stack selection, project architecture, FastAPI & Next.js skeleton | **COMPLETE** |
| **02** | **Database Foundation** | 13 SQLAlchemy domain models, Alembic migrations, PostGIS spatial setup | **COMPLETE** |
| **03** | **Authentication & RBAC** | JWT tokens, password hashing, 8-role authorization matrix, audit logs | **COMPLETE** |
| **04** | **Patient Management** | Patient registration, synthetic ABHA linkage, search, demographic profile | **COMPLETE** |
| **05** | **Care Request Management** | Frontline triage, urgency levels, chief complaints, diagnostic requirements | **COMPLETE** |
| **06** | **Facility & Capabilities** | Multi-tier facility inventory, bed tracking, specialty capabilities | **COMPLETE** |
| **07** | **Recommendation Engine** | 6-factor deterministic scoring algorithm (30/20/20/15/10/5 weights) | **COMPLETE** |
| **08** | **Referral Lifecycle** | 14-state referral state machine, rejection & rerouting, event timelines | **COMPLETE** |
| **09** | **Dashboards & Analytics** | Frontline, Facility, and District operational dashboards, Care Completion KPI | **COMPLETE** |
| **10** | **Offline-First & Sync** | PWA service worker, IndexedDB local buffering, idempotency auto-sync | **COMPLETE** |
| **11** | **AI Referral Assistant** | Privacy-sanitized administrative summary, missing info callouts, fallback | **COMPLETE** |
| **12** | **Testing & Golden Path** | 23-step Golden Path integration test, state machine matrix, E2E suites | **COMPLETE** |
| **13** | **Docker & Production** | Multi-stage Dockerfiles, Docker Compose, entrypoint migrations, security validator | **COMPLETE** |
| **14** | **Final Production & SIH Demo**| SIH Demo Runbook, Deployment Runbook, architecture docs, system verification | **COMPLETE** |

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | [Next.js 16](https://nextjs.org/) (App Router, React 19, TypeScript) | Responsive clinical UI with standalone production build |
| **Styling** | [Tailwind CSS](https://tailwindcss.com/) | Modular utility-first design system |
| **Offline Storage** | [Dexie.js](https://dexie.org/) (IndexedDB) | Client-side offline draft buffering & idempotency queue |
| **Backend API** | [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11+) | High-performance asynchronous REST API with Pydantic v2 |
| **ORM & Migrations** | [SQLAlchemy 2.0](https://www.sqlalchemy.org/) & [Alembic](https://alembic.sqlalchemy.org/) | Database model definitions and versioned migrations |
| **Spatial Database** | [PostgreSQL 16](https://www.postgresql.org/) + [PostGIS 3.4](https://postgis.net/) | Geospatial queries, distance calculation, spatial R-Tree indexing |
| **Cache & Queue** | [Redis 7](https://redis.io/) | Low-latency caching and rate limiting store |
| **Containerization** | [Docker](https://www.docker.com/) & Docker Compose | Multi-stage, non-root production orchestration |

---

## 🚀 Quickstart Guide

### Option A: Running with Docker Compose (Recommended)

1. **Clone the repository and copy the environment template**:
   ```bash
   git clone https://github.com/karanlenka97/RAHAT.git
   cd RAHAT
   cp .env.example .env
   ```

2. **Build and start all services**:
   ```bash
   docker compose up --build -d
   ```

3. **Check container health**:
   ```bash
   docker compose ps
   ```

4. **Access Applications**:
   - **Frontend UI**: [http://localhost:3000](http://localhost:3000)
   - **Backend API**: [http://localhost:8000](http://localhost:8000)
   - **Liveness Probe**: [http://localhost:8000/health](http://localhost:8000/health)
   - **Readiness Probe**: [http://localhost:8000/ready](http://localhost:8000/ready)
   - **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Option B: Running Locally for Development

#### 1. Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --reload --port 8000
```

#### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Testing and Quality Verification

### Run Backend Unit & Integration Tests (158 Tests)
```bash
pytest tests/
```

### Run Frontend Lint and Production Build
```bash
cd frontend
npm run lint
npm run build
```

---

## 📚 Technical Documentation & Runbooks

- **[SIH 2026 Live Demo Runbook](docs/SIH_DEMO_RUNBOOK.md)**: Step-by-step jury presentation script, demo accounts, and talking points.
- **[Production Deployment Runbook](docs/DEPLOYMENT_RUNBOOK.md)**: Provider-neutral deployment guide, database setup, migrations, and troubleshooting.
- **[Architecture Specification](docs/ARCHITECTURE.md)**: Complete 14-phase system architecture, database models, and algorithm definitions.
- **[Project Specification](PROJECT_SPEC.md)**: Complete functional requirements and system specifications.
- **[Visual Walkthrough & SVG Diagrams](svgwalkthrough.md)**: Interactive SVG architecture diagrams, state machines, and quality reports.

---

## 👥 Demo Personas & Test Credentials

Password for all accounts: `RahatDev@2026`

- **Frontline CHO**: `cho@rahat.local`
- **ASHA Worker**: `asha@rahat.local`
- **Facility Specialist Doctor**: `doctor@rahat.local`
- **Medical Officer**: `medical.officer@rahat.local`
- **Facility Administrator**: `facility.admin@rahat.local`
- **District Health Officer**: `district.admin@rahat.local`
- **System Administrator**: `admin@rahat.local`

---

## 🔒 Security & Data Privacy

- **100% Synthetic Data**: All demonstration patient records, facility names, ABHA references, and phone numbers are synthetic.
- **AI Safety**: The AI assistant operates strictly as an administrative drafting assistant. It **never diagnoses, prescribes, changes triage urgency, or selects facilities autonomously**.
- **Privacy Minimization**: PII is stripped prior to calling AI services or writing audit log details.
