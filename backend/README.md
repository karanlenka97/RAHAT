# RAHAT - Backend Service

FastAPI-powered backend foundation for RAHAT (Rural Assistance & Healthcare Access Tele-network).

## Structure
```
backend/
├── alembic/
│   ├── versions/
│   │   └── 0001_initial_database_foundation.py
│   ├── env.py
│   └── script.py.mako
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   └── health.py
│   │       └── api.py
│   ├── core/
│   │   └── config.py
│   ├── db/
│   │   ├── seed.py
│   │   └── session.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── audit_log.py
│   │   ├── base.py
│   │   ├── care_request.py
│   │   ├── facility.py
│   │   ├── notification.py
│   │   ├── patient.py
│   │   ├── professional.py
│   │   ├── referral.py
│   │   ├── role.py
│   │   ├── user.py
│   │   └── village.py
│   ├── schemas/
│   │   └── health.py
│   ├── services/
│   └── main.py
├── alembic.ini
├── requirements.txt
├── pyproject.toml
└── .env.example
```

## Running Locally

1. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run Database Migrations (PostgreSQL + PostGIS):
```bash
alembic upgrade head
```

4. Run Seeders (Initial system roles):
```bash
python -m app.db.seed
```

5. Run FastAPI development server:
```bash
uvicorn app.main:app --reload --port 8000
```

6. Check Health & Documentation:
- API Docs: `http://localhost:8000/docs`
- Health Endpoint: `http://localhost:8000/health`
