# Production Deployment Runbook
# RAHAT — Rural Healthcare Access & Referral Assistance Technology

> **Provider-Neutral Production Deployment & Operations Guide**

---

## 1. System Architecture & Prerequisites

RAHAT is composed of four decoupled, scalable tiers:
1. **Frontend Tier**: Next.js 16 (React 19, TypeScript) built in `standalone` output mode.
2. **Backend Tier**: FastAPI (Python 3.11) ASGI application served by Uvicorn multi-worker processes.
3. **Database Tier**: PostgreSQL 16 with PostGIS 3.4 spatial extensions and spatial R-Tree indices.
4. **Cache & Queue Tier**: Redis 7 for low-latency session caching and event buffering.

### Minimum Server Requirements
| Component | Minimum Specs | Recommended Production Specs |
| :--- | :--- | :--- |
| **Backend & Frontend** | 2 vCPU, 4 GB RAM, 20 GB SSD | 4 vCPU, 8 GB RAM, 50 GB SSD |
| **PostgreSQL + PostGIS** | 2 vCPU, 4 GB RAM, 50 GB SSD | 4 vCPU, 16 GB RAM, 200 GB SSD (NVMe) |
| **Redis** | 1 vCPU, 1 GB RAM | 2 vCPU, 4 GB RAM |

---

## 2. Production Environment Variables Checklist

Create a secure `.env` file on the production host based on `.env.example`:

```bash
# -------------------------------------------------------------------------
# Core Environment & Security
# -------------------------------------------------------------------------
ENVIRONMENT=production
DEBUG=false

# CRITICAL: Generate with: openssl rand -hex 32
JWT_SECRET=8f9c2d1e0a4b7c6d5e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# -------------------------------------------------------------------------
# Backend Server & CORS
# -------------------------------------------------------------------------
BACKEND_PORT=8000
API_V1_STR=/api/v1
PROJECT_NAME="RAHAT - Rural Assistance & Healthcare Access Tele-network"
BACKEND_CORS_ORIGINS=["https://rahat.health.gov.in","https://app.rahat.gov.in"]
UVICORN_WORKERS=4
RUN_DB_SEED=false

# -------------------------------------------------------------------------
# Frontend Application
# -------------------------------------------------------------------------
FRONTEND_PORT=3000
NEXT_PUBLIC_API_URL=https://api.rahat.gov.in
NEXT_PUBLIC_APP_NAME="RAHAT"

# -------------------------------------------------------------------------
# PostgreSQL + PostGIS Database
# -------------------------------------------------------------------------
POSTGRES_SERVER=rahat-postgres
POSTGRES_PORT=5432
POSTGRES_USER=rahat_admin
POSTGRES_PASSWORD=SECURE_DB_PASSWORD_HERE
POSTGRES_DB=rahat_production
DATABASE_URL=postgresql://rahat_admin:SECURE_DB_PASSWORD_HERE@rahat-postgres:5432/rahat_production

# -------------------------------------------------------------------------
# Redis Cache
# -------------------------------------------------------------------------
REDIS_PORT=6379
REDIS_URL=redis://rahat-redis:6379/0

# -------------------------------------------------------------------------
# AI Referral Assistant (Server-Side Only)
# -------------------------------------------------------------------------
AI_PROVIDER=mock
AI_MODEL=gemini-1.5-flash
AI_API_KEY=
AI_TIMEOUT_SECONDS=15
AI_RATE_LIMIT_PER_MINUTE=30
```

---

## 3. Database Migration & Initialization Runbook

### Step 1: Initialize Database & PostGIS Extension
On a clean PostgreSQL 16 database instance, ensure the PostGIS extension is installed:
```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### Step 2: Execute Alembic Migrations
Run versioned migrations to create all 13 tables, spatial columns, foreign keys, and indexes:
```bash
# Inside backend container or environment:
alembic upgrade head
```

### Step 3: Seed Reference Roles and Initial Seed Data (First Boot Only)
```bash
python -m app.db.seed
```

---

## 4. Containerized Production Deployment (Docker Compose)

### 1. Validate Docker Compose Configuration
```bash
docker compose config
```

### 2. Build Multi-Stage Production Images
```bash
docker compose build --no-cache
```

### 3. Launch Services in Detached Mode
```bash
docker compose up -d
```

### 4. Verify Service Health & Statuses
```bash
docker compose ps
```
Expected output:
```
NAME                IMAGE                  COMMAND                  SERVICE    STATUS
rahat-postgres      postgis/postgis:16     "docker-entrypoint.s…"   postgres   healthy
rahat-redis         redis:7-alpine         "docker-entrypoint.s…"   redis      healthy
rahat-backend       rahat-backend:latest   "/app/entrypoint.sh"     backend    healthy
rahat-frontend      rahat-frontend:latest  "node server.js"         frontend   healthy
```

---

## 5. Health Checks & Observability Runbook

### Liveness Probe (`GET /health`)
Lightweight operational check returning HTTP 200:
```bash
curl -f http://localhost:8000/health
```
Response:
```json
{
  "status": "ok",
  "service": "rahat-backend",
  "version": "0.1.0",
  "environment": "production",
  "database": null,
  "timestamp": "2026-09-12T04:30:00Z"
}
```

### Readiness Probe (`GET /ready` or `GET /api/v1/health/ready`)
Deep probe that tests database socket and query execution (`SELECT 1`):
```bash
curl -f http://localhost:8000/ready
```
Response:
```json
{
  "status": "ok",
  "service": "rahat-backend",
  "version": "0.1.0",
  "environment": "production",
  "database": "connected",
  "timestamp": "2026-09-12T04:30:00Z"
}
```

---

## 6. Zero-Downtime Rolling Update & Rollback Strategies

### Rolling Update
```bash
# 1. Pull latest Git commits
git pull origin main

# 2. Build new image versions
docker compose build backend frontend

# 3. Apply any new database migrations
docker compose exec backend alembic upgrade head

# 4. Re-create containers with zero downtime
docker compose up -d --no-deps backend frontend
```

### Emergency Rollback
```bash
# 1. Roll back database schema by 1 revision if required
docker compose exec backend alembic downgrade -1

# 2. Revert to previous Git release tag
git checkout <previous_stable_tag>

# 3. Rebuild and restart containers
docker compose up -d --build
```

---

## 7. Troubleshooting & Common Operational Errors

| Symptom | Probable Cause | Corrective Action |
| :--- | :--- | :--- |
| **Backend exits with `Production Security Error`** | Default development `JWT_SECRET` is used when `ENVIRONMENT=production` | Generate a 64-char random hex key via `openssl rand -hex 32` and set in `JWT_SECRET`. |
| **Backend fails on boot waiting for PostgreSQL** | Database container is still initializing or port is wrong | Check `docker compose logs postgres`; verify database credentials in `.env`. |
| **Frontend displays CORS network error** | `BACKEND_CORS_ORIGINS` does not match the frontend domain | Add the exact frontend origin (e.g. `https://app.rahat.gov.in`) to `BACKEND_CORS_ORIGINS`. |
| **PostGIS spatial query failure** | PostGIS extension not initialized in database | Run `CREATE EXTENSION postgis;` in PostgreSQL. |
