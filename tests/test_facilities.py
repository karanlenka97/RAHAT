"""Automated tests for Phase 6: Facility Management & Facility Capabilities."""
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.api.deps import get_db
from app.models import Base, Role, User, Village, Patient, CareRequest, Facility, FacilityCapability, AuditLog
from app.db.seed import (
    seed_roles,
    seed_dev_users,
    seed_villages,
    seed_facilities,
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
    Facility.__table__.create(engine)
    FacilityCapability.__table__.create(engine)
    AuditLog.__table__.create(engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    # Seed foundation
    seed_roles(session)
    seed_dev_users(session)
    seed_villages(session)
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


@pytest.fixture
def admin_token(client):
    """Obtain JWT for ADMIN."""
    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "admin@rahat.local", "password": DEV_PASSWORD_PLAIN},
    )
    return res.json()["access_token"]


@pytest.fixture
def district_admin_token(client):
    """Obtain JWT for DISTRICT_ADMIN."""
    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "district.admin@rahat.local", "password": DEV_PASSWORD_PLAIN},
    )
    return res.json()["access_token"]


@pytest.fixture
def facility_admin_token(client):
    """Obtain JWT for FACILITY_ADMIN."""
    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "facility.admin@rahat.local", "password": DEV_PASSWORD_PLAIN},
    )
    return res.json()["access_token"]


@pytest.fixture
def doctor_token(client):
    """Obtain JWT for DOCTOR."""
    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "doctor@rahat.local", "password": DEV_PASSWORD_PLAIN},
    )
    return res.json()["access_token"]


@pytest.fixture
def asha_token(client):
    """Obtain JWT for ASHA worker."""
    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "asha@rahat.local", "password": DEV_PASSWORD_PLAIN},
    )
    return res.json()["access_token"]


# ---------------------------------------------------------------------------
# Facility Tests
# ---------------------------------------------------------------------------


def test_create_facility_success(client, admin_token, test_db_session):
    """Admin successfully creates a new facility and audit log is recorded."""
    payload = {
        "name": "Community Health Centre - Bonai",
        "code": "FAC-OR-SNG-CHC02",
        "facility_type": "CHC",
        "district": "Sundargarh",
        "state": "Odisha",
        "address": "Main Road, Bonai",
        "pincode": "770038",
        "latitude": 21.7500,
        "longitude": 84.9700,
        "phone": "+916628200010",
        "operating_hours": "24x7",
        "is_active": True,
        "total_beds": 30,
        "available_beds": 12,
        "icu_beds": 2,
        "available_icu_beds": 1,
    }
    response = client.post(
        "/api/v1/facilities",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["facility_type"] == "CHC"
    assert data["tier_level"] == 3
    assert data["district"] == "Sundargarh"
    assert data["latitude"] == 21.7500
    assert data["longitude"] == 84.9700

    # Verify audit log
    audit = test_db_session.query(AuditLog).filter(
        AuditLog.action == "FACILITY_CREATED",
        AuditLog.entity_id == data["id"],
    ).first()
    assert audit is not None
    assert audit.entity_type == "Facility"


def test_create_facility_invalid_type(client, admin_token):
    """Creating a facility with an invalid facility_type fails validation."""
    payload = {
        "name": "Invalid Center",
        "facility_type": "MEGA_HOSPITAL_INVALID",
        "district": "Sundargarh",
        "latitude": 22.0,
        "longitude": 84.0,
    }
    response = client.post(
        "/api/v1/facilities",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422


def test_list_facilities_pagination_and_filter(client, doctor_token):
    """Doctor can list facilities with pagination, district filter, and type filter."""
    response = client.get(
        "/api/v1/facilities?page=1&page_size=3&district=Sundargarh",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 3
    assert len(data["items"]) == 3
    assert data["total"] >= 8

    # Filter by facility_type
    res_phc = client.get(
        "/api/v1/facilities?facility_type=PHC",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert res_phc.status_code == 200
    phc_data = res_phc.json()
    assert all(item["facility_type"] == "PHC" for item in phc_data["items"])


def test_list_facilities_search(client, asha_token):
    """Search facilities by name keyword."""
    response = client.get(
        "/api/v1/facilities?search=Kansbahal",
        headers={"Authorization": f"Bearer {asha_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 1
    assert "Kansbahal" in data["items"][0]["name"]


def test_get_facility_by_id(client, doctor_token, test_db_session):
    """Retrieve facility details including its capabilities."""
    fac = test_db_session.query(Facility).filter(Facility.facility_type == "SPECIALTY_HOSPITAL").first()
    assert fac is not None

    response = client.get(
        f"/api/v1/facilities/{fac.id}",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(fac.id)
    assert data["facility_type"] == "SPECIALTY_HOSPITAL"
    assert len(data["capabilities"]) > 0


def test_update_facility(client, district_admin_token, test_db_session):
    """District admin updates facility beds and operating hours."""
    fac = test_db_session.query(Facility).first()
    payload = {
        "available_beds": 18,
        "operating_hours": "24x7 Emergency",
    }
    response = client.patch(
        f"/api/v1/facilities/{fac.id}",
        json=payload,
        headers={"Authorization": f"Bearer {district_admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["available_beds"] == 18
    assert data["operating_hours"] == "24x7 Emergency"

    # Verify audit log
    audit = test_db_session.query(AuditLog).filter(
        AuditLog.action == "FACILITY_UPDATED",
        AuditLog.entity_id == str(fac.id),
    ).first()
    assert audit is not None


# ---------------------------------------------------------------------------
# Nearby Facility Lookup Tests
# ---------------------------------------------------------------------------


def test_nearby_facility_lookup(client, doctor_token):
    """Geographic lookup within 15km of Rourkela center (22.2499, 84.8828)."""
    # Coordinates in Rourkela
    lat = 22.2499
    lon = 84.8828
    radius = 15.0

    response = client.get(
        f"/api/v1/facilities/nearby?latitude={lat}&longitude={lon}&radius_km={radius}",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] > 0
    assert len(data["items"]) == data["count"]

    # Verify items are sorted ascending by distance_km and <= radius
    distances = [item["distance_km"] for item in data["items"]]
    assert distances == sorted(distances)
    assert all(d <= radius for d in distances)


def test_nearby_facility_excludes_inactive(client, admin_token, test_db_session):
    """Inactive facilities must not be returned in nearby lookup."""
    fac = test_db_session.query(Facility).first()
    fac.is_active = False
    test_db_session.commit()

    response = client.get(
        f"/api/v1/facilities/nearby?latitude={fac.latitude}&longitude={fac.longitude}&radius_km=50.0",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    returned_ids = [item["facility"]["id"] for item in data["items"]]
    assert str(fac.id) not in returned_ids


# ---------------------------------------------------------------------------
# Facility Capabilities Tests
# ---------------------------------------------------------------------------


def test_create_and_list_capability(client, facility_admin_token, test_db_session):
    """Add a new capability to an existing facility and verify via list."""
    fac = test_db_session.query(Facility).first()
    payload = {
        "service_name": "Emergency Ultrasound",
        "service_category": "ULTRASOUND",
        "available": True,
        "availability_status": "AVAILABLE",
        "capacity": 20,
        "current_load": 5,
        "specialist_required": True,
        "diagnostic_required": True,
        "operating_hours": "08:00 - 20:00",
    }
    response = client.post(
        f"/api/v1/facilities/{fac.id}/capabilities",
        json=payload,
        headers={"Authorization": f"Bearer {facility_admin_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["service_name"] == "Emergency Ultrasound"
    assert data["service_category"] == "ULTRASOUND"
    assert data["capacity"] == 20
    assert data["current_load"] == 5

    # List capabilities
    list_res = client.get(
        f"/api/v1/facilities/{fac.id}/capabilities",
        headers={"Authorization": f"Bearer {facility_admin_token}"},
    )
    assert list_res.status_code == 200
    caps = list_res.json()
    assert any(c["id"] == data["id"] for c in caps)


def test_update_capability_success(client, admin_token, test_db_session):
    """Update capability capacity, load, and availability."""
    cap = test_db_session.query(FacilityCapability).first()
    assert cap is not None

    payload = {
        "availability_status": "HIGH_LOAD",
        "capacity": 50,
        "current_load": 42,
    }
    response = client.patch(
        f"/api/v1/facilities/{cap.facility_id}/capabilities/{cap.id}",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["availability_status"] == "HIGH_LOAD"
    assert data["capacity"] == 50
    assert data["current_load"] == 42


def test_invalid_capability_validation(client, admin_token, test_db_session):
    """Test validation errors for negative capacity, negative load, load > capacity, and empty service name."""
    fac = test_db_session.query(Facility).first()

    # Negative capacity
    res_neg_cap = client.post(
        f"/api/v1/facilities/{fac.id}/capabilities",
        json={
            "service_name": "Test Service",
            "service_category": "GENERAL_MEDICINE",
            "capacity": -5,
            "current_load": 0,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_neg_cap.status_code == 422

    # Negative current load
    res_neg_load = client.post(
        f"/api/v1/facilities/{fac.id}/capabilities",
        json={
            "service_name": "Test Service",
            "service_category": "GENERAL_MEDICINE",
            "capacity": 10,
            "current_load": -2,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_neg_load.status_code == 422

    # Current load exceeds capacity
    res_load_exceed = client.post(
        f"/api/v1/facilities/{fac.id}/capabilities",
        json={
            "service_name": "Test Service",
            "service_category": "GENERAL_MEDICINE",
            "capacity": 10,
            "current_load": 25,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_load_exceed.status_code == 422

    # Empty service name
    res_empty_name = client.post(
        f"/api/v1/facilities/{fac.id}/capabilities",
        json={
            "service_name": "   ",
            "service_category": "GENERAL_MEDICINE",
            "capacity": 10,
            "current_load": 2,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_empty_name.status_code == 422


# ---------------------------------------------------------------------------
# RBAC Tests
# ---------------------------------------------------------------------------


def test_rbac_unauthorized_write(client, doctor_token, asha_token, test_db_session):
    """Doctors and ASHAs have read access but are forbidden from creating/modifying facilities and capabilities."""
    fac = test_db_session.query(Facility).first()

    # DOCTOR cannot create facility
    res_create_fac = client.post(
        "/api/v1/facilities",
        json={
            "name": "Unauthorized Clinic",
            "facility_type": "PHC",
            "district": "Sundargarh",
            "latitude": 22.0,
            "longitude": 84.0,
        },
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert res_create_fac.status_code == 403

    # ASHA cannot update facility
    res_update_fac = client.patch(
        f"/api/v1/facilities/{fac.id}",
        json={"name": "Tampered Name"},
        headers={"Authorization": f"Bearer {asha_token}"},
    )
    assert res_update_fac.status_code == 403

    # DOCTOR cannot create capability
    res_create_cap = client.post(
        f"/api/v1/facilities/{fac.id}/capabilities",
        json={
            "service_name": "Specialist Clinic",
            "service_category": "CARDIOLOGY",
        },
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert res_create_cap.status_code == 403
