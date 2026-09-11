"""Automated tests for Phase 5: Care Request Management."""
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.api.deps import get_db
from app.models import Base, Role, User, Village, Patient, CareRequest, AuditLog
from app.db.seed import (
    seed_roles,
    seed_dev_users,
    seed_villages,
    seed_synthetic_patients,
    seed_synthetic_care_requests,
    DEV_PASSWORD_PLAIN,
)


@pytest.fixture
def test_db_session():
    """Create an isolated in-memory SQLite database session with StaticPool."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Create required tables
    Role.__table__.create(engine)
    User.__table__.create(engine)
    Village.__table__.create(engine)
    Patient.__table__.create(engine)
    CareRequest.__table__.create(engine)
    AuditLog.__table__.create(engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    # Seed foundation
    seed_roles(session)
    seed_dev_users(session)
    seed_villages(session)
    seed_synthetic_patients(session)
    seed_synthetic_care_requests(session)

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
    """Obtain valid JWT for frontline ASHA worker."""
    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "asha@rahat.local", "password": DEV_PASSWORD_PLAIN},
    )
    return res.json()["access_token"]


@pytest.fixture
def doctor_token(client):
    """Obtain valid JWT for Doctor."""
    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "doctor@rahat.local", "password": DEV_PASSWORD_PLAIN},
    )
    return res.json()["access_token"]


def test_create_care_request_success(client, asha_token, test_db_session):
    """1, 4, 8, 9, 10. Authenticated frontline worker creates care request with unique number & creator binding."""
    patient = test_db_session.query(Patient).first()
    asha_user = test_db_session.query(User).filter(User.email == "asha@rahat.local").first()

    payload = {
        "patient_id": str(patient.id),
        "care_category": "MATERNAL_HEALTH",
        "required_service": "Obstetrics & Gynecology",
        "urgency": "MEDIUM",
        "symptoms_summary": "Second trimester routine antenatal checkup with mild pedal edema",
        "diagnostic_requirements": ["Obstetric Ultrasound", "Urine Albumin"],
        "specialist_required": True,
        "notes": "Patient advised iron-folic acid supplementation and scheduled for follow-up.",
    }

    response = client.post(
        "/api/v1/care-requests",
        json=payload,
        headers={"Authorization": f"Bearer {asha_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["request_number"].startswith("CR-RAHAT-")
    assert data["patient_id"] == str(patient.id)
    assert data["care_category"] == "MATERNAL_HEALTH"
    assert data["required_service"] == "Obstetrics & Gynecology"
    assert data["urgency"] == "MEDIUM"
    assert data["specialist_required"] is True
    assert "Obstetric Ultrasound" in data["diagnostic_requirements"]
    assert data["created_by"] == str(asha_user.id)
    assert data["creator"]["full_name"] == asha_user.full_name

    # Check Audit Log
    audit = test_db_session.query(AuditLog).filter(
        AuditLog.action == "CARE_REQUEST_CREATED",
        AuditLog.entity_id == data["id"],
    ).first()
    assert audit is not None
    assert audit.details["request_number"] == data["request_number"]


def test_create_care_request_unauthenticated_fails(client, test_db_session):
    """2. Unauthenticated care request creation returns 401 Unauthorized."""
    patient = test_db_session.query(Patient).first()
    response = client.post(
        "/api/v1/care-requests",
        json={
            "patient_id": str(patient.id),
            "care_category": "GENERAL_MEDICINE",
            "required_service": "General Medicine",
            "symptoms_summary": "Headache",
        },
    )
    assert response.status_code == 401


def test_create_care_request_invalid_patient_rejected(client, asha_token):
    """3. Nonexistent patient ID is rejected with 404."""
    fake_patient_id = str(uuid.uuid4())
    payload = {
        "patient_id": fake_patient_id,
        "care_category": "GENERAL_MEDICINE",
        "required_service": "General Medicine",
        "symptoms_summary": "Fever for 2 days",
    }
    response = client.post(
        "/api/v1/care-requests",
        json=payload,
        headers={"Authorization": f"Bearer {asha_token}"},
    )
    assert response.status_code == 404
    assert "does not exist" in response.json()["detail"].lower()


def test_create_care_request_invalid_category_rejected(client, asha_token, test_db_session):
    """4. Invalid care category rejected with 422 Unprocessable Entity."""
    patient = test_db_session.query(Patient).first()
    payload = {
        "patient_id": str(patient.id),
        "care_category": "INVALID_CATEGORY_XYZ",
        "required_service": "General Medicine",
        "symptoms_summary": "Mild cough",
    }
    response = client.post(
        "/api/v1/care-requests",
        json=payload,
        headers={"Authorization": f"Bearer {asha_token}"},
    )
    assert response.status_code == 422


def test_create_care_request_invalid_urgency_rejected(client, asha_token, test_db_session):
    """5. Invalid urgency rejected with 422."""
    patient = test_db_session.query(Patient).first()
    payload = {
        "patient_id": str(patient.id),
        "care_category": "GENERAL_MEDICINE",
        "required_service": "General Medicine",
        "urgency": "SUPER_CRITICAL_EXTRA",
        "symptoms_summary": "Mild cough",
    }
    response = client.post(
        "/api/v1/care-requests",
        json=payload,
        headers={"Authorization": f"Bearer {asha_token}"},
    )
    assert response.status_code == 422


def test_get_care_request_by_id(client, asha_token, test_db_session):
    """10. Retrieve a care request by UUID."""
    care_req = test_db_session.query(CareRequest).first()
    response = client.get(
        f"/api/v1/care-requests/{care_req.id}",
        headers={"Authorization": f"Bearer {asha_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(care_req.id)
    assert data["request_number"] == care_req.request_number
    assert data["patient"]["id"] == str(care_req.patient_id)


def test_list_care_requests_pagination(client, asha_token):
    """11. Paginated list of care requests."""
    response = client.get(
        "/api/v1/care-requests?page=1&page_size=3",
        headers={"Authorization": f"Bearer {asha_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 3
    assert data["total"] >= 6
    assert data["page"] == 1
    assert data["total_pages"] >= 2


def test_filter_care_requests(client, asha_token):
    """12. Filter care requests by urgency, category, and patient."""
    # Filter by urgency EMERGENCY
    res_urg = client.get(
        "/api/v1/care-requests?urgency=EMERGENCY",
        headers={"Authorization": f"Bearer {asha_token}"},
    )
    assert res_urg.status_code == 200
    for item in res_urg.json()["items"]:
        assert item["urgency"] == "EMERGENCY"

    # Filter by care category MATERNAL_HEALTH
    res_cat = client.get(
        "/api/v1/care-requests?care_category=MATERNAL_HEALTH",
        headers={"Authorization": f"Bearer {asha_token}"},
    )
    assert res_cat.status_code == 200
    for item in res_cat.json()["items"]:
        assert item["care_category"] == "MATERNAL_HEALTH"


def test_patch_care_request_success(client, doctor_token, test_db_session):
    """14, 16. Update permitted fields, maintain immutable fields, and generate audit log."""
    care_req = test_db_session.query(CareRequest).filter(
        CareRequest.request_number == "CR-RAHAT-000001"
    ).first()
    original_id = str(care_req.id)
    original_patient_id = str(care_req.patient_id)
    original_creator_id = str(care_req.created_by_user_id)
    original_req_num = care_req.request_number

    payload = {
        "urgency": "HIGH",
        "required_service": "Pulmonology",
        "symptoms_summary": "Updated: Productive cough with worsening dyspnea on exertion",
        "specialist_required": True,
        "diagnostic_requirements": ["High-Resolution CT", "Sputum Culture"],
        "notes": "Escalated to specialist triage due to worsening oxygen saturation.",
    }

    response = client.patch(
        f"/api/v1/care-requests/{care_req.id}",
        json=payload,
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["urgency"] == "HIGH"
    assert data["required_service"] == "Pulmonology"
    assert data["specialist_required"] is True
    assert "High-Resolution CT" in data["diagnostic_requirements"]

    # Immutability validation
    assert data["id"] == original_id
    assert data["patient_id"] == original_patient_id
    assert data["created_by"] == original_creator_id
    assert data["request_number"] == original_req_num

    # Audit log validation
    audit = test_db_session.query(AuditLog).filter(
        AuditLog.action == "CARE_REQUEST_UPDATED",
        AuditLog.entity_id == original_id,
    ).order_by(AuditLog.timestamp.desc()).first()
    assert audit is not None
    assert "urgency" in audit.details["modified_fields"]


def test_patch_care_request_unauthenticated_fails(client, test_db_session):
    """15. Unauthenticated update is rejected."""
    care_req = test_db_session.query(CareRequest).first()
    response = client.patch(
        f"/api/v1/care-requests/{care_req.id}",
        json={"urgency": "HIGH"},
    )
    assert response.status_code == 401
