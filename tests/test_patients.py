"""Automated tests for Patient Management and Village Registry."""
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.api.deps import get_db
from app.models import Base, Role, User, Village, Patient, AuditLog
from app.db.seed import seed_roles, seed_dev_users, seed_villages, seed_synthetic_patients, DEV_PASSWORD_PLAIN


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
    AuditLog.__table__.create(engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    # Seed foundation
    seed_roles(session)
    seed_dev_users(session)
    seed_villages(session)
    seed_synthetic_patients(session)

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


def test_create_patient_success(client, asha_token, test_db_session):
    """1, 4, 5, 16. Verify authenticated frontline worker creates patient with unique code & audit log."""
    village = test_db_session.query(Village).first()

    payload = {
        "full_name": "Sita Nayak",
        "age": 30,
        "gender": "FEMALE",
        "phone": "+919811122233",
        "village_id": str(village.id),
        "address": "Ward 3, Near Water Tank",
        "emergency_contact_name": "Gopal Nayak",
        "emergency_contact_phone": "+919811122244",
        "abha_reference": "91-9988-7766-5544",
        "blood_group": "A+",
        "chronic_conditions": ["Anemia"],
        "allergies": [],
    }

    response = client.post(
        "/api/v1/patients",
        json=payload,
        headers={"Authorization": f"Bearer {asha_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["full_name"] == "Sita Nayak"
    assert data["gender"] == "FEMALE"
    assert data["patient_code"].startswith("RAHAT-P-")
    assert data["village"]["name"] == village.name
    assert "password" not in data

    # Verify audit log entry
    audit = test_db_session.query(AuditLog).filter(
        AuditLog.action == "PATIENT_CREATED",
        AuditLog.entity_id == data["id"],
    ).first()
    assert audit is not None
    assert audit.details["patient_code"] == data["patient_code"]


def test_create_patient_unauthenticated_fails(client):
    """2. Verify unauthenticated patient creation returns 401 Unauthorized."""
    response = client.post(
        "/api/v1/patients",
        json={"full_name": "Test Person", "gender": "MALE"},
    )
    assert response.status_code == 401


def test_create_patient_invalid_village_rejected(client, asha_token):
    """6. Verify nonexistent village ID returns 400 Bad Request."""
    fake_village_id = str(uuid.uuid4())
    payload = {
        "full_name": "Rani Sahu",
        "gender": "FEMALE",
        "village_id": fake_village_id,
    }

    response = client.post(
        "/api/v1/patients",
        json=payload,
        headers={"Authorization": f"Bearer {asha_token}"},
    )
    assert response.status_code == 400
    assert "does not exist" in response.json()["detail"].lower()


def test_create_patient_invalid_data_rejected(client, asha_token):
    """7. Verify invalid age and gender are rejected with 422."""
    # Invalid gender
    res1 = client.post(
        "/api/v1/patients",
        json={"full_name": "Rani Sahu", "gender": "UNKNOWN_GENDER"},
        headers={"Authorization": f"Bearer {asha_token}"},
    )
    assert res1.status_code == 422

    # Invalid age (>130)
    res2 = client.post(
        "/api/v1/patients",
        json={"full_name": "Rani Sahu", "gender": "FEMALE", "age": 200},
        headers={"Authorization": f"Bearer {asha_token}"},
    )
    assert res2.status_code == 422


def test_get_patient_by_id(client, asha_token, test_db_session):
    """8. Verify retrieving a patient profile by ID."""
    patient = test_db_session.query(Patient).first()
    response = client.get(
        f"/api/v1/patients/{patient.id}",
        headers={"Authorization": f"Bearer {asha_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(patient.id)
    assert data["patient_code"] == patient.anonymous_patient_code
    assert data["full_name"] == patient.full_name


def test_get_patient_nonexistent_returns_404(client, asha_token):
    """8b. Verify requesting a nonexistent patient ID returns 404."""
    random_id = str(uuid.uuid4())
    response = client.get(
        f"/api/v1/patients/{random_id}",
        headers={"Authorization": f"Bearer {asha_token}"},
    )
    assert response.status_code == 404


def test_list_patients_pagination(client, asha_token):
    """9. Verify patient list supports pagination (page, page_size, total)."""
    response = client.get(
        "/api/v1/patients?page=1&page_size=3",
        headers={"Authorization": f"Bearer {asha_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 3
    assert data["page"] == 1
    assert data["page_size"] == 3
    assert data["total"] >= 6
    assert data["total_pages"] >= 2


def test_patient_search(client, asha_token):
    """10. Verify searching patients by name and patient code."""
    # Search by name "Aarav"
    res_name = client.get(
        "/api/v1/patients?search=Aarav",
        headers={"Authorization": f"Bearer {asha_token}"},
    )
    assert res_name.status_code == 200
    items = res_name.json()["items"]
    assert len(items) >= 1
    assert "Aarav" in items[0]["full_name"]

    # Search by code "RAHAT-P-000002"
    res_code = client.get(
        "/api/v1/patients?search=RAHAT-P-000002",
        headers={"Authorization": f"Bearer {asha_token}"},
    )
    assert res_code.status_code == 200
    items = res_code.json()["items"]
    assert len(items) == 1
    assert items[0]["patient_code"] == "RAHAT-P-000002"


def test_patch_patient_success(client, doctor_token, test_db_session):
    """11, 13, 14, 16. Verify updating patient demographic fields, immutability of ID/code, and audit log."""
    patient = test_db_session.query(Patient).filter(
        Patient.anonymous_patient_code == "RAHAT-P-000001"
    ).first()
    original_code = patient.anonymous_patient_code

    payload = {
        "full_name": "Aarav Sharma Updated",
        "phone": "+919999988888",
        "chronic_conditions": ["Hypertension", "Mild Asthma"],
    }

    response = client.patch(
        f"/api/v1/patients/{patient.id}",
        json=payload,
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Aarav Sharma Updated"
    assert data["phone"] == "+919999988888"
    assert "Mild Asthma" in data["chronic_conditions"]
    # Patient code and ID must remain unchanged
    assert data["patient_code"] == original_code
    assert data["id"] == str(patient.id)

    # Verify audit log
    audit = test_db_session.query(AuditLog).filter(
        AuditLog.action == "PATIENT_UPDATED",
        AuditLog.entity_id == str(patient.id),
    ).order_by(AuditLog.timestamp.desc()).first()
    assert audit is not None
    assert "full_name" in audit.details["modified_fields"]


def test_patch_patient_unauthenticated_fails(client, test_db_session):
    """12. Verify unauthenticated update is rejected."""
    patient = test_db_session.query(Patient).first()
    response = client.patch(
        f"/api/v1/patients/{patient.id}",
        json={"full_name": "Hacker Attempt"},
    )
    assert response.status_code == 401


def test_list_villages_endpoint(client, asha_token):
    """Verify GET /api/v1/villages lists registered habitational units."""
    response = client.get(
        "/api/v1/villages",
        headers={"Authorization": f"Bearer {asha_token}"},
    )
    assert response.status_code == 200
    villages = response.json()
    assert len(villages) >= 3
    village_names = {v["name"] for v in villages}
    assert "Kansbahal" in village_names
    assert "Lathikata" in village_names
