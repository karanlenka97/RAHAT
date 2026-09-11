# RAHAT — Rural Healthcare Access & Referral Assistance Technology
## Phase 13: Docker & Production Configuration

---

## 1. Production Container Architecture

```xml
<svg viewBox="0 0 960 660" xmlns="http://www.w3.org/2000/svg" style="background:#0b1329; font-family:system-ui, sans-serif; border-radius:12px;">
  <!-- Header -->
  <rect width="960" height="60" fill="#1e293b" rx="12" />
  <text x="25" y="38" fill="#38bdf8" font-size="20" font-weight="bold">RAHAT Container Architecture &amp; Production Topology</text>
  <text x="760" y="38" fill="#94a3b8" font-size="14">Phase 13 Production Ready</text>

  <!-- Network Boundary -->
  <rect x="25" y="80" width="910" height="340" fill="#0f172a" stroke="#334155" stroke-width="2" stroke-dasharray="6,6" rx="10" />
  <text x="45" y="105" fill="#64748b" font-size="13" font-weight="bold">INTERNAL DOCKER NETWORK (rahat-network: bridge)</text>

  <!-- Service 1: Frontend -->
  <g transform="translate(50, 125)">
    <rect width="250" height="270" fill="#1e293b" stroke="#38bdf8" stroke-width="2" rx="8" />
    <rect x="0" y="0" width="250" height="36" fill="#0369a1" rx="8" />
    <text x="15" y="24" fill="#ffffff" font-weight="bold" font-size="14">rahat-frontend (Next.js 16)</text>
    <text x="15" y="60" fill="#cbd5e1" font-size="12">• Node.js 20 Alpine Multi-Stage</text>
    <text x="15" y="80" fill="#cbd5e1" font-size="12">• Next.js Standalone Runner</text>
    <text x="15" y="100" fill="#cbd5e1" font-size="12">• Non-Root: nextjs:nodejs (UID 1001)</text>
    <text x="15" y="120" fill="#cbd5e1" font-size="12">• Image Size: &lt;180 MB</text>
    <text x="15" y="140" fill="#cbd5e1" font-size="12">• Client Safe: Zero private keys</text>
    <text x="15" y="160" fill="#cbd5e1" font-size="12">• Port: 3000:3000</text>
    <rect x="15" y="185" width="220" height="32" fill="#0f172a" stroke="#38bdf8" rx="6" />
    <text x="25" y="206" fill="#38bdf8" font-size="11">Health: wget --spider :3000</text>
    <rect x="15" y="225" width="220" height="32" fill="#0284c7" rx="6" />
    <text x="35" y="246" fill="#ffffff" font-size="11" font-weight="bold">PWA / Offline Sync Built</text>
  </g>

  <!-- Service 2: Backend -->
  <g transform="translate(340, 125)">
    <rect width="270" height="270" fill="#1e293b" stroke="#10b981" stroke-width="2" rx="8" />
    <rect x="0" y="0" width="270" height="36" fill="#047857" rx="8" />
    <text x="15" y="24" fill="#ffffff" font-weight="bold" font-size="14">rahat-backend (FastAPI ASGI)</text>
    <text x="15" y="60" fill="#cbd5e1" font-size="12">• Python 3.11-slim Multi-Stage</text>
    <text x="15" y="80" fill="#cbd5e1" font-size="12">• Uvicorn Production Workers</text>
    <text x="15" y="100" fill="#cbd5e1" font-size="12">• Non-Root: rahat (UID 1000)</text>
    <text x="15" y="120" fill="#cbd5e1" font-size="12">• Automated Alembic on Boot</text>
    <text x="15" y="140" fill="#cbd5e1" font-size="12">• Spatial Libs: libpq5, libgeos</text>
    <text x="15" y="160" fill="#cbd5e1" font-size="12">• Port: 8000:8000</text>
    <rect x="15" y="185" width="240" height="32" fill="#0f172a" stroke="#10b981" rx="6" />
    <text x="25" y="206" fill="#10b981" font-size="11">Health: curl -f /health &amp; /ready</text>
    <rect x="15" y="225" width="240" height="32" fill="#059669" rx="6" />
    <text x="35" y="246" fill="#ffffff" font-size="11" font-weight="bold">Strict Production JWT Gate</text>
  </g>

  <!-- Service 3 & 4: Databases -->
  <g transform="translate(650, 125)">
    <!-- Postgres -->
    <rect width="260" height="125" fill="#1e293b" stroke="#6366f1" stroke-width="2" rx="8" />
    <rect x="0" y="0" width="260" height="32" fill="#4338ca" rx="8" />
    <text x="15" y="22" fill="#ffffff" font-weight="bold" font-size="13">rahat-postgres (PostGIS 16-3.4)</text>
    <text x="15" y="52" fill="#cbd5e1" font-size="11">• Volume: postgres_data</text>
    <text x="15" y="70" fill="#cbd5e1" font-size="11">• Health: pg_isready -U postgres</text>
    <text x="15" y="88" fill="#cbd5e1" font-size="11">• Port: 5432 (Internal/Host)</text>
    <text x="15" y="108" fill="#a5b4fc" font-size="11" font-weight="bold">Persistent Spatial Storage</text>

    <!-- Redis -->
    <g transform="translate(0, 145)">
      <rect width="260" height="125" fill="#1e293b" stroke="#ef4444" stroke-width="2" rx="8" />
      <rect x="0" y="0" width="260" height="32" fill="#b91c1c" rx="8" />
      <text x="15" y="22" fill="#ffffff" font-weight="bold" font-size="13">rahat-redis (Redis 7-alpine)</text>
      <text x="15" y="52" fill="#cbd5e1" font-size="11">• Volume: redis_data</text>
      <text x="15" y="70" fill="#cbd5e1" font-size="11">• Health: redis-cli ping</text>
      <text x="15" y="88" fill="#cbd5e1" font-size="11">• Port: 6379 (Internal)</text>
      <text x="15" y="108" fill="#fca5a5" font-size="11" font-weight="bold">In-Memory Cache &amp; Broker</text>
    </g>
  </g>

  <!-- Production Quality & Security Gates -->
  <g transform="translate(25, 440)">
    <rect width="910" height="200" fill="#1e293b" stroke="#f59e0b" stroke-width="2" rx="8" />
    <text x="20" y="30" fill="#f59e0b" font-weight="bold" font-size="15">Phase 13 Production Readiness &amp; Security Validation Matrix</text>

    <!-- Column 1 -->
    <g transform="translate(20, 50)">
      <rect width="270" height="130" fill="#0f172a" rx="6" stroke="#334155" />
      <text x="15" y="25" fill="#38bdf8" font-size="13" font-weight="bold">🔒 Security &amp; Isolation</text>
      <text x="15" y="50" fill="#e2e8f0" font-size="11">✔ Non-root container users (UID 1000/1001)</text>
      <text x="15" y="70" fill="#e2e8f0" font-size="11">✔ Production JWT Secret (&gt;32 chars)</text>
      <text x="15" y="90" fill="#e2e8f0" font-size="11">✔ DEBUG=False enforced in prod mode</text>
      <text x="15" y="110" fill="#e2e8f0" font-size="11">✔ AI API keys server-side only</text>
    </g>

    <!-- Column 2 -->
    <g transform="translate(315, 50)">
      <rect width="270" height="130" fill="#0f172a" rx="6" stroke="#334155" />
      <text x="15" y="25" fill="#10b981" font-size="13" font-weight="bold">⚙ Database &amp; Migrations</text>
      <text x="15" y="50" fill="#e2e8f0" font-size="11">✔ Automatic Alembic migration on boot</text>
      <text x="15" y="70" fill="#e2e8f0" font-size="11">✔ Socket connectivity retry loop</text>
      <text x="15" y="90" fill="#e2e8f0" font-size="11">✔ Named persistent Docker volumes</text>
      <text x="15" y="110" fill="#e2e8f0" font-size="11">✔ PostGIS spatial tables preserved</text>
    </g>

    <!-- Column 3 -->
    <g transform="translate(610, 50)">
      <rect width="280" height="130" fill="#0f172a" rx="6" stroke="#334155" />
      <text x="15" y="25" fill="#a855f7" font-size="13" font-weight="bold">🚀 Orchestration &amp; Probes</text>
      <text x="15" y="50" fill="#e2e8f0" font-size="11">✔ Liveness probe (/health)</text>
      <text x="15" y="70" fill="#e2e8f0" font-size="11">✔ Readiness probe (/ready with DB check)</text>
      <text x="15" y="90" fill="#e2e8f0" font-size="11">✔ Multi-worker Uvicorn ASGI execution</text>
      <text x="15" y="110" fill="#e2e8f0" font-size="11">✔ Next.js standalone runner &lt;180MB</text>
    </g>
  </g>
</svg>
```

---

## 2. Container Startup Sequence & Dependency Management

```
 ┌──────────────┐       ┌──────────────┐
 │  PostgreSQL  │       │    Redis     │
 │  (PostGIS)   │       │  (7-alpine)  │
 └──────┬───────┘       └──────┬───────┘
        │ pg_isready           │ ping
        └───────────┬──────────┘
                    ↓
        ┌──────────────────────┐
        │ rahat-backend Boot   │
        │ - TCP readiness wait │
        │ - alembic upgrade    │
        │ - optional DB seed   │
        │ - Uvicorn workers    │
        └───────────┬──────────┘
                    │ /health (HTTP 200)
                    ↓
        ┌──────────────────────┐
        │   rahat-frontend     │
        │ (Next.js Standalone) │
        │ - Node server.js     │
        │ - Port 3000          │
        └──────────────────────┘
```

---

## 3. Production Environment & Security Configuration

| Setting Key | Development Default | Production Requirement | Purpose |
| :--- | :--- | :--- | :--- |
| `ENVIRONMENT` | `development` | `production` | Enables production security validators & shields docs |
| `DEBUG` | `True` | `False` | Disables stack traces and internal debugging leakage |
| `JWT_SECRET` | Dev placeholder | High-entropy hex string $\ge 32$ chars | Secures authentication tokens (validated on startup) |
| `DATABASE_URL` | Local connection | Postgres container connection | Database connection pooling |
| `BACKEND_CORS_ORIGINS` | `localhost:3000, 127.0.0.1:3000` | Specific domain(s) | Prevents cross-origin unauthorized API calls |
| `UVICORN_WORKERS` | `1` | `2`–`4` | Parallel ASGI process handling |
| `RUN_DB_SEED` | `false` | `false` | Prevents overwriting production reference tables |
| `AI_API_KEY` | Optional | Kept server-side only | Never exposed to frontend client bundle |

---

## 4. Local Docker Operations & Runbook Commands

### Build & Start Stack
```bash
# 1. Create environment file from template
cp .env.example .env

# 2. Validate docker-compose configuration
docker compose config

# 3. Build optimized production multi-stage images
docker compose build

# 4. Start all services in detached mode
docker compose up -d

# 5. Check container statuses and health probes
docker compose ps

# 6. Stream logs
docker compose logs -f
```

### Stop & Restart Stack (Data Preservation)
```bash
# Gracefully stop containers without destroying volumes
docker compose down

# Start containers again (PostgreSQL data in postgres_data persists)
docker compose up -d
```

---

## 5. Production Readiness Checklist

### Security
- [x] All secrets externalized via `.env` (never committed to repository).
- [x] Insecure development JWT secret strictly rejected in production mode.
- [x] `DEBUG=False` enforced in production mode to shield stack traces.
- [x] CORS origins explicitly configurable via comma-separated string or JSON array.
- [x] AI credentials remain exclusively server-side.
- [x] `.dockerignore` filters all `.env`, `.git`, `node_modules`, and cache files from build contexts.

### Infrastructure & Containers
- [x] Backend multi-stage Dockerfile builds with non-root user `rahat` (UID 1000).
- [x] Frontend multi-stage Dockerfile uses Next.js standalone mode with non-root user `nextjs` (UID 1001).
- [x] PostGIS spatial database runs with named volume `postgres_data` persistence.
- [x] Redis runs with named volume `redis_data`.
- [x] Health checks configured for all 4 services (`pg_isready`, `redis-cli ping`, `curl /health`, `wget :3000`).
- [x] Container startup sequence uses `condition: service_healthy` to prevent premature API startup.

### Application & Migrations
- [x] Backend `entrypoint.sh` performs socket-level database wait and `alembic upgrade head`.
- [x] Health and readiness probes (`/health`, `/ready`, `/api/v1/health`, `/api/v1/health/ready`).
- [x] 100% test pass rate (158 backend tests + 7 Playwright E2E suites + clean Next.js build).
