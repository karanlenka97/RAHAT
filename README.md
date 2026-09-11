# RAHAT (Rural Assistance & Healthcare Access Tele-network)

> **SwasthyaSetu / RAHAT** is an intelligent, geospatial healthcare referral, dynamic bed-allocation, and emergency routing platform designed to streamline rural and regional healthcare access.

---

## 🌟 Overview

RAHAT bridges primary health centers (PHCs), community health centers (CHCs), and tertiary referral hospitals into a coordinated network. It enables real-time facility visibility, optimized patient routing, and transparent referral tracking to reduce delays during critical care transfers.

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | [Next.js](https://nextjs.org/) (App Router, React 19, TypeScript) | Modern, responsive interface with server-side rendering |
| **Styling** | [Tailwind CSS](https://tailwindcss.com/) | Modular utility-first design system |
| **Backend API** | [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11+) | High-performance asynchronous REST API |
| **ORM & Migrations** | [SQLAlchemy](https://www.sqlalchemy.org/) & [Alembic](https://alembic.sqlalchemy.org/) | Database model definitions and versioned migrations |
| **Spatial Database** | [PostgreSQL](https://www.postgresql.org/) + [PostGIS](https://postgis.net/) | Geospatial queries, distance calculation, facility mapping |
| **Cache & Message Broker** | [Redis](https://redis.io/) | Low-latency caching and real-time event queuing |
| **Containerization** | [Docker](https://www.docker.com/) & Docker Compose | Multi-container orchestration and consistent environments |

---

## 📁 Project Structure

```text
RAHAT/
├── frontend/                # Next.js frontend application (TypeScript, Tailwind CSS)
│   ├── src/
│   │   ├── app/             # Next.js App Router (layout, pages, styles)
│   │   ├── components/      # Reusable UI components
│   │   └── lib/             # Utility functions and API clients
│   ├── public/              # Static assets
│   ├── package.json         # Frontend dependencies and scripts
│   ├── tsconfig.json        # TypeScript configuration
│   └── .env.example         # Frontend environment template
├── backend/                 # FastAPI backend application
│   ├── alembic/             # Database migration environment and scripts
│   │   ├── versions/        # Versioned migration revisions
│   │   └── env.py           # Alembic runtime configuration
│   ├── app/
│   │   ├── api/             # Versioned API routes (v1 endpoints)
│   │   ├── core/            # App configuration and settings
│   │   ├── db/              # Database session, seeders, and PostGIS config
│   │   ├── models/          # 13 Core SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic data validation schemas
│   │   ├── services/        # Business logic layer
│   │   └── main.py          # FastAPI application entry point
│   ├── alembic.ini          # Alembic CLI configuration
│   ├── requirements.txt     # Python backend dependencies
│   ├── pyproject.toml       # Backend project metadata and tools
│   └── .env.example         # Backend environment template
├── docs/                    # Architecture and technical documentation
│   └── ARCHITECTURE.md      # Architecture and entity guide
├── data/                    # Seed data, spatial boundaries, and schemas
├── scripts/                 # Maintenance, setup, and seed scripts
│   ├── setup_dev.py         # Environment verification script
│   └── seed_db.py           # Database seeding runner
├── docker/                  # Dockerfiles and container configurations
│   ├── Dockerfile.frontend  # Multi-stage Next.js Dockerfile
│   ├── Dockerfile.backend   # FastAPI Dockerfile with PostGIS dependencies
│   └── .dockerignore        # Docker build exclusion rules
├── tests/                   # Automated test suites
│   ├── conftest.py          # Test configuration & client fixtures
│   ├── test_health.py       # Health check and endpoint tests
│   └── test_database.py     # Database models, PostGIS, and schema tests
├── .env.example             # Master environment configuration template
├── .gitignore               # Git exclusion rules
├── docker-compose.yml       # Docker Compose service orchestration
├── PROJECT_SPEC.md          # Complete project specification
└── README.md                # Project documentation
```

---

## 🗄️ Database Entities (Phase 2 Foundation)

The database schema includes 13 core models:
1. `Role`: System roles with JSON permissions matrix
2. `User`: Healthcare workers, admins, coordinators with hashed credentials
3. `Village`: Community units with PostGIS `POINT` GPS coordinates (SRID 4326)
4. `Facility`: Sub Centers to Tertiary Hospitals with PostGIS locations & bed tracking
5. `FacilityCapability`: Specialized capabilities (NICU, Trauma, Blood Bank, Specialties)
6. `HealthcareProfessional`: Clinical personnel with councils and specialties
7. `Patient`: Patient index with ABHA identifiers and medical history
8. `CareRequest`: Initial triage and consultation requests
9. `Referral`: Inter-facility transfer workflows with priority and transport tracking
10. `ReferralEvent`: Immutable state transition and dispatch logs
11. `FollowUp`: Post-discharge monitoring by community workers
12. `Notification`: Critical alerts and workflow notifications
13. `AuditLog`: Immutable audit trail for compliance and tracking

---

## 🚀 Running the Project

### Option A: Running with Docker Compose (Recommended)

1. **Copy the environment template**:
   ```bash
   cp .env.example .env
   ```

2. **Build and start all services**:
   ```bash
   docker compose up --build
   ```

3. **Run database migrations inside backend**:
   ```bash
   docker compose exec backend alembic upgrade head
   ```

4. **Seed initial system roles**:
   ```bash
   docker compose exec backend python -m app.db.seed
   ```

5. **Access Services**:
   - **Frontend Application**: [http://localhost:3000](http://localhost:3000)
   - **Backend API**: [http://localhost:8000](http://localhost:8000)
   - **Interactive API Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Backend Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

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

## 🧪 Testing and Verification

To run backend & database tests:
```bash
pytest tests/
```

To run frontend build & lint checks:
```bash
cd frontend
npm run lint
npm run build
```
