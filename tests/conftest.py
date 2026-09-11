"""Pytest test fixtures, in-memory SQLite setup, and spatial mocks."""
import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add backend directory to sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Register SQLite dummy spatial functions for in-memory unit tests
@event.listens_for(Engine, "connect")
def set_sqlite_spatial_mock(dbapi_connection, connection_record):
    if hasattr(dbapi_connection, "create_function"):
        funcs = [
            "InitSpatialMetaData",
            "RecoverGeometryColumn",
            "AddGeometryColumn",
            "DiscardGeometryColumn",
            "CreateSpatialIndex",
            "DropSpatialIndex",
            "DisableSpatialIndex",
            "CheckSpatialIndex",
            "AsEWKB",
            "AsBinary",
            "ST_AsBinary",
            "GeomFromText",
            "GeomFromEWKT",
            "ST_GeomFromEWKT",
            "ST_GeomFromText",
            "GeomFromWKB",
            "ST_AsGeoJSON",
            "ST_Transform",
            "ST_Distance",
            "ST_DWithin",
        ]
        for name in funcs:
            try:
                dbapi_connection.create_function(
                    name,
                    -1,
                    lambda *args: None if len(args) == 0 else args[0] if isinstance(args[0], (bytes, memoryview, str)) else None,
                )
            except Exception:
                pass

from app.main import app
from app.api.deps import get_db
from app.models import (
    Base,
    Role,
    User,
    Village,
    Patient,
    CareRequest,
    Facility,
    FacilityCapability,
    Referral,
    ReferralEvent,
    AuditLog,
)
from app.db.seed import (
    seed_roles,
    seed_dev_users,
    seed_villages,
    seed_synthetic_patients,
    seed_synthetic_care_requests,
    seed_facilities,
    DEV_PASSWORD_PLAIN,
)


@pytest.fixture
def test_db_session():
    """Create an isolated, in-memory SQLite database session with seed data."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Role.__table__.create(engine)
    User.__table__.create(engine)
    Village.__table__.create(engine)
    Patient.__table__.create(engine)
    CareRequest.__table__.create(engine)
    Facility.__table__.create(engine)
    FacilityCapability.__table__.create(engine)
    Referral.__table__.create(engine)
    ReferralEvent.__table__.create(engine)
    AuditLog.__table__.create(engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    seed_roles(session)
    seed_dev_users(session)
    seed_villages(session)
    seed_synthetic_patients(session)
    seed_synthetic_care_requests(session)
    seed_facilities(session)

    yield session
    session.close()


@pytest.fixture
def client(test_db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _login_user(client, email: str) -> str:
    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": email, "password": DEV_PASSWORD_PLAIN},
    )
    return res.json()["access_token"]


@pytest.fixture
def admin_token(client):
    return _login_user(client, "admin@rahat.local")


@pytest.fixture
def district_admin_token(client):
    return _login_user(client, "district.admin@rahat.local")


@pytest.fixture
def facility_admin_token(client):
    return _login_user(client, "facility.admin@rahat.local")


@pytest.fixture
def doctor_token(client):
    return _login_user(client, "doctor@rahat.local")


@pytest.fixture
def medical_officer_token(client):
    return _login_user(client, "medical.officer@rahat.local")


@pytest.fixture
def cho_token(client):
    return _login_user(client, "cho@rahat.local")


@pytest.fixture
def anm_token(client):
    return _login_user(client, "anm@rahat.local")


@pytest.fixture
def asha_token(client):
    return _login_user(client, "asha@rahat.local")
