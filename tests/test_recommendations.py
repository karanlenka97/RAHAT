"""Automated test suite for Phase 7: Smart Facility Recommendation Engine."""
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
    seed_synthetic_patients,
    seed_synthetic_care_requests,
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
# Test Cases
# ---------------------------------------------------------------------------


def test_recommendation_cardiology_emergency(client, doctor_token, test_db_session):
    """1, 5, 7, 8, 14, 16, 20. Cardiology emergency care request ranks Specialty Hospital top with high scores."""
    # CR-RAHAT-000003 is Cardiology Emergency with ECG, Echo, Troponin, and Specialist required
    cr = test_db_session.query(CareRequest).filter(CareRequest.request_number == "CR-RAHAT-000003").first()
    assert cr is not None

    response = client.get(
        f"/api/v1/recommendations/{cr.id}",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["care_request_id"] == str(cr.id)
    assert data["total_candidates"] > 0
    assert len(data["recommendations"]) > 0

    top_rec = data["recommendations"][0]
    # Specialty Hospital offers Cardiology & Cath Lab interventions
    assert "Specialty" in top_rec["facility_type"] or "Specialty Hospital" in top_rec["facility_name"]
    assert top_rec["overall_score"] > 80.0
    assert top_rec["factors"]["service_match"] == 100.0
    assert top_rec["specialist_available"] is True
    assert "Recommended because" in top_rec["explanation"]


def test_recommendation_obstetrics_maternal(client, asha_token, test_db_session):
    """Maternal Health / ANC care request ranks CHC / PHC with obstetrics capabilities."""
    cr = test_db_session.query(CareRequest).filter(CareRequest.request_number == "CR-RAHAT-000002").first()
    assert cr is not None

    response = client.get(
        f"/api/v1/recommendations/{cr.id}",
        headers={"Authorization": f"Bearer {asha_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["recommendations"]) > 0

    for rec in data["recommendations"]:
        assert rec["factors"]["service_match"] > 0.0
        assert rec["overall_score"] > 0.0
        assert rec["availability_status"] in ["AVAILABLE", "LIMITED", "HIGH_LOAD"]


def test_recommendation_top_n_limit(client, doctor_token, test_db_session):
    """17. Limit query parameter strictly constrains recommendation count."""
    cr = test_db_session.query(CareRequest).first()
    response = client.get(
        f"/api/v1/recommendations/{cr.id}?limit=2",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["recommendations"]) <= 2


def test_recommendation_nonexistent_care_request_404(client, doctor_token):
    """18. Nonexistent care request returns 404."""
    fake_id = uuid.uuid4()
    response = client.get(
        f"/api/v1/recommendations/{fake_id}",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert response.status_code == 404


def test_recommendation_unauthenticated_fails(client, test_db_session):
    """19. Unauthenticated request is rejected."""
    cr = test_db_session.query(CareRequest).first()
    response = client.get(f"/api/v1/recommendations/{cr.id}")
    assert response.status_code == 401


def test_recommendation_inactive_facility_filtered(client, doctor_token, test_db_session):
    """13. Inactive facilities are hard-filtered and never recommended."""
    # Deactivate Specialty Hospital
    fac = test_db_session.query(Facility).filter(Facility.facility_type == "SPECIALTY_HOSPITAL").first()
    fac.is_active = False
    test_db_session.commit()

    cr = test_db_session.query(CareRequest).filter(CareRequest.request_number == "CR-RAHAT-000003").first()
    response = client.get(
        f"/api/v1/recommendations/{cr.id}",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    rec_ids = [r["facility_id"] for r in data["recommendations"]]
    assert str(fac.id) not in rec_ids


def test_recommendation_unavailable_capability_filtered(client, doctor_token, test_db_session):
    """2. Capabilities marked UNAVAILABLE or available=False do not count towards match."""
    # Set all Cardiology capabilities to UNAVAILABLE
    caps = test_db_session.query(FacilityCapability).filter(
        FacilityCapability.service_category == "CARDIOLOGY"
    ).all()
    for cap in caps:
        cap.available = False
        cap.availability_status = "UNAVAILABLE"
    test_db_session.commit()

    cr = test_db_session.query(CareRequest).filter(CareRequest.request_number == "CR-RAHAT-000003").first()
    response = client.get(
        f"/api/v1/recommendations/{cr.id}",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    # No available cardiology facilities left
    assert len(data["recommendations"]) == 0


def test_recommendation_missing_coordinates_fallback(client, doctor_token, test_db_session):
    """4. Missing village / origin coordinates gracefully falls back to neutral 50.0 score."""
    cr = test_db_session.query(CareRequest).first()
    cr.village_id = None
    if cr.patient:
        cr.patient.village_id = None
    test_db_session.commit()

    response = client.get(
        f"/api/v1/recommendations/{cr.id}",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    if data["recommendations"]:
        rec = data["recommendations"][0]
        assert rec["distance_km"] is None
        assert rec["factors"]["distance"] == 50.0


def test_recommendation_no_diagnostic_requirements(client, doctor_token, test_db_session):
    """6. Care request without diagnostic requirements gets 100% diagnostic score."""
    cr = test_db_session.query(CareRequest).first()
    cr.diagnostic_requirements = []
    test_db_session.commit()

    response = client.get(
        f"/api/v1/recommendations/{cr.id}",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    if data["recommendations"]:
        assert data["recommendations"][0]["factors"]["diagnostic_match"] == 100.0


def test_recommendation_specialist_not_required(client, doctor_token, test_db_session):
    """8. Care request without specialist required gets 100% specialist score."""
    cr = test_db_session.query(CareRequest).first()
    cr.specialist_required = False
    test_db_session.commit()

    response = client.get(
        f"/api/v1/recommendations/{cr.id}",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    if data["recommendations"]:
        assert data["recommendations"][0]["factors"]["specialist_match"] == 100.0


def test_recommendation_workload_and_zero_capacity(client, doctor_token, test_db_session):
    """10, 11, 12. Capacity zero or high load calculates correct workload score without dividing by zero."""
    fac = test_db_session.query(Facility).filter(Facility.code == "FAC-OR-SNG-AAM01").first()
    assert fac is not None
    # Set capacity to 0 on capability
    for cap in fac.capabilities:
        cap.capacity = 0
        cap.current_load = 0
    test_db_session.commit()

    cr = test_db_session.query(CareRequest).filter(CareRequest.request_number == "CR-RAHAT-000001").first()
    response = client.get(
        f"/api/v1/recommendations/{cr.id}",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    for rec in data["recommendations"]:
        if rec["facility_id"] == str(fac.id):
            # Safe neutral fallback when capacity is 0
            assert rec["factors"]["workload"] == 50.0


def test_recommendation_sorting_and_tie_breaking(client, doctor_token, test_db_session):
    """14, 15, 16. Results are sorted overall_score DESC, then distance_km ASC."""
    cr = test_db_session.query(CareRequest).first()
    response = client.get(
        f"/api/v1/recommendations/{cr.id}?limit=10",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    recs = data["recommendations"]

    for i in range(len(recs) - 1):
        # Overall score must be >= next candidate
        assert recs[i]["overall_score"] >= recs[i + 1]["overall_score"]
        # If overall score is equal, distance must be <= next candidate
        if recs[i]["overall_score"] == recs[i + 1]["overall_score"]:
            d1 = recs[i]["distance_km"] or float("inf")
            d2 = recs[i + 1]["distance_km"] or float("inf")
            assert d1 <= d2
