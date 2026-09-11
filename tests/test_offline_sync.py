"""Automated test suite for Phase 10: Offline-First Synchronization & Idempotency."""
import uuid
import time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.api.deps import get_db
from app.models import (
    Base,
    Role,
    User,
    Village,
    Patient,
    Facility,
    FacilityCapability,
    HealthcareProfessional,
    CareRequest,
    Referral,
    ReferralEvent,
    FollowUp,
    Notification,
    AuditLog,
)
from app.db.seed import run_seeds, DEV_PASSWORD_PLAIN
from app.core.idempotency import idempotency_cache, IdempotencyCache


@pytest.fixture
def test_db_session():
    """Create an isolated in-memory SQLite database session with StaticPool."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Create all required tables
    Role.__table__.create(engine)
    User.__table__.create(engine)
    Village.__table__.create(engine)
    Patient.__table__.create(engine)
    Facility.__table__.create(engine)
    FacilityCapability.__table__.create(engine)
    HealthcareProfessional.__table__.create(engine)
    CareRequest.__table__.create(engine)
    Referral.__table__.create(engine)
    ReferralEvent.__table__.create(engine)
    FollowUp.__table__.create(engine)
    Notification.__table__.create(engine)
    AuditLog.__table__.create(engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    # Seed foundation data
    run_seeds(session)

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


@pytest.fixture
def asha_token(client):
    """Login as ASHA worker and return JWT bearer token."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"identifier": "asha@rahat.local", "password": DEV_PASSWORD_PLAIN},
    )
    assert login_resp.status_code == 200
    return login_resp.json()["access_token"]


@pytest.fixture
def cho_token(client):
    """Login as CHO and return JWT bearer token."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"identifier": "cho@rahat.local", "password": DEV_PASSWORD_PLAIN},
    )
    assert login_resp.status_code == 200
    return login_resp.json()["access_token"]


def test_idempotency_cache_unit():
    """Unit tests for the memory IdempotencyCache."""
    cache = IdempotencyCache()
    key = "test-unit-key-1"
    cache.set(key, {"status": 201, "data": {"id": "123"}})

    # Retrieve
    cached = cache.get(key)
    assert cached is not None
    assert cached["status"] == 201
    assert cached["data"]["id"] == "123"

    # Non-existent key
    assert cache.get("non-existent-key") is None

    # Clear cache
    cache.clear()
    assert cache.get(key) is None


def test_health_probe_reachability(client):
    """Verify that GET /health returns 200 OK for frontend reachability probe."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "rahat-backend"


def test_patient_idempotency_key_replay(client, asha_token, test_db_session):
    """Verify that replaying a patient registration with the same X-Idempotency-Key returns cached result."""
    idempotency_key = f"patient-idem-{uuid.uuid4()}"
    village = test_db_session.query(Village).first()

    payload = {
        "full_name": "Offline Sync Test Patient",
        "gender": "FEMALE",
        "age": 34,
        "phone": "9876543210",
        "village_id": str(village.id) if village else None,
        "address": "House 12, Ward 3",
        "emergency_contact_name": "Ramesh Test",
        "emergency_contact_phone": "9876543211",
        "blood_group": "B_POSITIVE",
        "chronic_conditions": ["HYPERTENSION"],
        "allergies": ["PENICILLIN"],
    }

    initial_patient_count = test_db_session.query(Patient).count()

    # 1. First execution
    resp1 = client.post(
        "/api/v1/patients",
        json=payload,
        headers={
            "Authorization": f"Bearer {asha_token}",
            "X-Idempotency-Key": idempotency_key,
        },
    )
    assert resp1.status_code == 201
    data1 = resp1.json()
    patient_id_1 = data1["id"]
    patient_code_1 = data1["patient_code"]
    assert data1["full_name"] == "Offline Sync Test Patient"

    # Count should increment by 1
    assert test_db_session.query(Patient).count() == initial_patient_count + 1

    # 2. Second execution (replaying identical idempotency key - simulated retry on sync)
    resp2 = client.post(
        "/api/v1/patients",
        json=payload,
        headers={
            "Authorization": f"Bearer {asha_token}",
            "X-Idempotency-Key": idempotency_key,
        },
    )
    assert resp2.status_code == 201
    data2 = resp2.json()

    # Must return identical cached record
    assert data2["id"] == patient_id_1
    assert data2["patient_code"] == patient_code_1
    assert data2["full_name"] == "Offline Sync Test Patient"

    # Database count MUST NOT increase
    assert test_db_session.query(Patient).count() == initial_patient_count + 1


def test_patient_different_idempotency_keys_create_distinct_records(client, asha_token, test_db_session):
    """Verify that different idempotency keys create distinct patient records."""
    key1 = f"patient-idem-diff-{uuid.uuid4()}"
    key2 = f"patient-idem-diff-{uuid.uuid4()}"

    payload = {
        "full_name": "Distinct Patient Test",
        "gender": "MALE",
        "age": 42,
    }

    resp1 = client.post(
        "/api/v1/patients",
        json=payload,
        headers={
            "Authorization": f"Bearer {asha_token}",
            "X-Idempotency-Key": key1,
        },
    )
    assert resp1.status_code == 201
    id1 = resp1.json()["id"]

    resp2 = client.post(
        "/api/v1/patients",
        json=payload,
        headers={
            "Authorization": f"Bearer {asha_token}",
            "X-Idempotency-Key": key2,
        },
    )
    assert resp2.status_code == 201
    id2 = resp2.json()["id"]

    assert id1 != id2


def test_care_request_idempotency_key_replay(client, cho_token, test_db_session):
    """Verify that replaying care request creation with X-Idempotency-Key returns cached response."""
    patient = test_db_session.query(Patient).first()
    idempotency_key = f"cr-idem-{uuid.uuid4()}"

    payload = {
        "patient_id": str(patient.id),
        "care_category": "MATERNAL_HEALTH",
        "required_service": "Obstetrics & Gynecology",
        "urgency": "HIGH",
        "symptoms_summary": "Offline intake sync test for high-risk pregnancy.",
        "diagnostic_requirements": ["Obstetric Ultrasound", "CBC"],
        "specialist_required": True,
        "notes": "Queued offline by frontline ANM, now synchronizing.",
    }

    initial_cr_count = test_db_session.query(CareRequest).count()

    # 1. First execution
    resp1 = client.post(
        "/api/v1/care-requests",
        json=payload,
        headers={
            "Authorization": f"Bearer {cho_token}",
            "X-Idempotency-Key": idempotency_key,
        },
    )
    assert resp1.status_code == 201
    data1 = resp1.json()
    cr_id_1 = data1["id"]
    cr_number_1 = data1["request_number"]

    assert test_db_session.query(CareRequest).count() == initial_cr_count + 1

    # 2. Replay with identical idempotency key
    resp2 = client.post(
        "/api/v1/care-requests",
        json=payload,
        headers={
            "Authorization": f"Bearer {cho_token}",
            "X-Idempotency-Key": idempotency_key,
        },
    )
    assert resp2.status_code == 201
    data2 = resp2.json()

    # Returns same cached care request response
    assert data2["id"] == cr_id_1
    assert data2["request_number"] == cr_number_1
    assert data2["symptoms_summary"] == "Offline intake sync test for high-risk pregnancy."

    # Database count must not increase
    assert test_db_session.query(CareRequest).count() == initial_cr_count + 1
