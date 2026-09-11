#!/bin/sh
# =========================================================================
# RAHAT Production Backend Entrypoint
# 1. Verifies Database Connectivity & Readiness
# 2. Executes Alembic Database Migrations
# 3. Executes Optional Seed Operations
# 4. Launches Production ASGI Server (Uvicorn)
# =========================================================================
set -e

echo "=================================================="
echo " Starting RAHAT Backend Service (Env: ${ENVIRONMENT:-development})"
echo "=================================================="

# Wait for PostgreSQL to become ready
echo "Waiting for PostgreSQL database to accept connections..."
python - <<'EOF'
import os
import sys
import time
import socket
from urllib.parse import urlparse

db_url = os.environ.get("DATABASE_URL")
if db_url:
    parsed = urlparse(db_url)
    host = parsed.hostname or "postgres"
    port = parsed.port or 5432
else:
    host = os.environ.get("POSTGRES_SERVER", "postgres")
    port = int(os.environ.get("POSTGRES_PORT", "5432"))

max_attempts = 30
for attempt in range(1, max_attempts + 1):
    try:
        with socket.create_connection((host, port), timeout=2):
            print(f"PostgreSQL is reachable at {host}:{port}")
            sys.exit(0)
    except (socket.error, OSError) as e:
        print(f"Attempt {attempt}/{max_attempts}: Waiting for {host}:{port}... ({e})")
        time.sleep(2)

print(f"ERROR: Could not connect to PostgreSQL at {host}:{port} after {max_attempts} attempts.")
sys.exit(1)
EOF

# Execute database migrations
echo "Executing Alembic database migrations (alembic upgrade head)..."
alembic upgrade head
echo "Database migrations completed successfully."

# Execute database seed if enabled
if [ "${RUN_DB_SEED}" = "true" ] || [ "${RUN_DB_SEED}" = "1" ]; then
    echo "RUN_DB_SEED is enabled. Seeding reference data..."
    python -m app.db.seed || echo "Seed execution finished."
fi

# Determine worker count based on environment
WORKERS="${UVICORN_WORKERS:-1}"
PORT="${BACKEND_PORT:-8000}"

echo "Starting Uvicorn ASGI Server on port ${PORT} with ${WORKERS} worker(s)..."

# If arguments were passed to entrypoint, execute them; otherwise execute standard server
if [ "$#" -gt 0 ]; then
    exec "$@"
else
    exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}" --workers "${WORKERS}"
fi
