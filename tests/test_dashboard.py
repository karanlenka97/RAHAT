"""Automated test suite for Phase 9: Frontline, Facility & District Dashboards."""
import uuid
from datetime import datetime, timezone, timedelta
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
    Referral.__table__.create(engine)
    ReferralEvent.__table__.create(engine)
    AuditLog.__table__.create(engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    # Seed foundation
    seed_roles(session)
    seed_facilities(session)
    seed_villages(session)
    seed_dev_users(session)
    seed_synthetic_patients(session)
    seed_synthetic_care_requests(session)

    yield session
    session.close()


@pytest.fixture
def client(test_db_session):
    """Create a FastAPI TestClient using the isolated database fixture."""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def get_auth_token(client: TestClient, identifier: str, password: str = DEV_PASSWORD_PLAIN) -> str:
    """Helper to authenticate and obtain a valid JWT access token."""
    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": identifier, "password": password},
    )
    assert response.status_code == 200, f"Login failed for {identifier}: {response.text}"
    return response.json()["access_token"]


# ---------------------------------------------------------------------------
# 1. Frontline Dashboard Tests
# ---------------------------------------------------------------------------

def test_frontline_dashboard_metrics_and_action_queue(client: TestClient, test_db_session):
    """Verify frontline dashboard returns valid metrics, accessible patients, and sorted action queue."""
    token = get_auth_token(client, "asha@rahat.local")  # ASHA user

    response = client.get(
        "/api/v1/dashboard/frontline",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["role"] in ("ASHA", "CHO", "ANM", "ADMIN")
    assert "total_patients" in data
    assert "active_care_requests" in data
    assert "urgent_care_requests" in data
    assert "action_queue" in data
    assert "recent_activity" in data
    assert isinstance(data["action_queue"], list)

    # If action queue has items, verify priority sorting (EMERGENCY ranked before MEDIUM/LOW)
    if len(data["action_queue"]) > 1:
        urg_map = {"EMERGENCY": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        first_item = data["action_queue"][0]
        last_item = data["action_queue"][-1]
        assert urg_map.get(first_item["urgency"].upper(), 1) >= urg_map.get(last_item["urgency"].upper(), 1)


def test_frontline_dashboard_with_referral_actions(client: TestClient, test_db_session):
    """Verify frontline action queue includes pending and in-transit referrals."""
    admin_token = get_auth_token(client, "admin@rahat.local")
    cr = test_db_session.query(CareRequest).first()
    facility = test_db_session.query(Facility).filter(Facility.is_active == True).first()

    # Create referral
    ref_res = client.post(
        "/api/v1/referrals",
        json={
            "care_request_id": str(cr.id),
            "receiving_facility_id": str(facility.id),
            "urgency": "EMERGENCY",
            "clinical_summary": "Frontline dashboard referral test",
            "referral_reason": "Emergency escalation",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert ref_res.status_code == 201

    # Check frontline dashboard as admin
    response = client.get(
        "/api/v1/dashboard/frontline",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["pending_referrals"] >= 1
    # Verify action item exists for referral
    ref_actions = [item for item in data["action_queue"] if item["item_type"] == "REFERRAL"]
    assert len(ref_actions) >= 1
    assert ref_actions[0]["urgency"] == "EMERGENCY"


# ---------------------------------------------------------------------------
# 2. Facility Dashboard Tests
# ---------------------------------------------------------------------------

def test_facility_dashboard_metrics_and_capacity(client: TestClient, test_db_session):
    """Verify facility dashboard returns live bed occupancy, status breakdowns, and capability loads."""
    admin_token = get_auth_token(client, "admin@rahat.local")
    facility = test_db_session.query(Facility).filter(Facility.is_active == True).first()

    response = client.get(
        f"/api/v1/dashboard/facility?facility_id={facility.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["facility_id"] == str(facility.id)
    assert data["facility_name"] == facility.name
    assert "total_beds" in data
    assert "available_beds" in data
    assert "bed_utilization_percent" in data
    assert "status_breakdown" in data
    assert "capabilities" in data
    assert isinstance(data["capabilities"], list)
    assert isinstance(data["operational_queue"], list)


def test_facility_dashboard_zero_capacity_safe_handling(client: TestClient, test_db_session):
    """Verify facility dashboard handles zero beds or zero capability capacity safely without division error."""
    admin_token = get_auth_token(client, "admin@rahat.local")
    zero_fac = Facility(
        id=uuid.uuid4(),
        name="Zero Bed Clinic",
        facility_type="SUB_CENTER",
        tier_level=1,
        district="Cuttack",
        state="Odisha",
        latitude=20.46,
        longitude=85.88,
        total_beds=0,
        available_beds=0,
        icu_beds=0,
        available_icu_beds=0,
        is_active=True,
    )
    test_db_session.add(zero_fac)
    zero_cap = FacilityCapability(
        id=uuid.uuid4(),
        facility_id=zero_fac.id,
        service_name="Outpatient Only",
        service_category="GENERAL_MEDICINE",
        availability_status="AVAILABLE",
        capacity=0,
        current_load=0,
    )
    test_db_session.add(zero_cap)
    test_db_session.commit()

    response = client.get(
        f"/api/v1/dashboard/facility?facility_id={zero_fac.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["bed_utilization_percent"] == 0.0
    assert data["icu_utilization_percent"] == 0.0
    assert len(data["capabilities"]) == 1
    assert data["capabilities"][0]["utilization_percent"] == 0.0


def test_facility_dashboard_isolation(client: TestClient, test_db_session):
    """Verify non-admin facility users cannot access foreign facilities."""
    fac_a = test_db_session.query(Facility).first()
    fac_b = test_db_session.query(Facility).offset(1).first()

    # Doctor assigned to fac_a
    doc_user = test_db_session.query(User).join(Role).filter(Role.name == "DOCTOR").first()
    doc_user.facility_id = fac_a.id
    test_db_session.commit()

    token = get_auth_token(client, "doctor@rahat.local")

    # Querying own facility should succeed
    res_own = client.get(
        f"/api/v1/dashboard/facility?facility_id={fac_a.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_own.status_code == 200

    # Querying foreign facility should be rejected with 403
    res_foreign = client.get(
        f"/api/v1/dashboard/facility?facility_id={fac_b.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_foreign.status_code == 403


# ---------------------------------------------------------------------------
# 3. District Dashboard Tests
# ---------------------------------------------------------------------------

def test_district_dashboard_metrics_and_performance(client: TestClient, test_db_session):
    """Verify district dashboard returns aggregate KPIs, care completion rate, and facility table."""
    admin_token = get_auth_token(client, "admin@rahat.local")

    response = client.get(
        "/api/v1/dashboard/district?district=Sundargarh&time_range=all",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["district_name"] == "Sundargarh"
    assert "total_care_requests" in data
    assert "total_referrals" in data
    assert "care_completion_rate" in data
    assert isinstance(data["care_completion_rate"], float)
    assert "care_requests_by_category" in data
    assert "facility_performance" in data
    assert isinstance(data["facility_performance"], list)


def test_district_dashboard_care_completion_calculation(client: TestClient, test_db_session):
    """Verify care completion rate calculation and zero denominator safety."""
    admin_token = get_auth_token(client, "admin@rahat.local")

    # Empty district with zero care requests
    response = client.get(
        "/api/v1/dashboard/district?district=NonexistentDistrict",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_care_requests"] == 0
    assert data["care_completion_rate"] == 0.0


# ---------------------------------------------------------------------------
# 4. Referral Funnel & Care Completion Endpoints
# ---------------------------------------------------------------------------

def test_referral_funnel_endpoint(client: TestClient, test_db_session):
    """Verify referral funnel endpoint returns all 8 stages and drop-offs."""
    token = get_auth_token(client, "admin@rahat.local")

    response = client.get(
        "/api/v1/dashboard/referral-funnel?time_range=all",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()

    assert "total_initiated" in data
    assert "stages" in data
    assert len(data["stages"]) == 8

    stage_keys = [s["stage_key"] for s in data["stages"]]
    assert stage_keys == [
        "CREATED",
        "PENDING_ACCEPTANCE",
        "ACCEPTED",
        "PATIENT_NOTIFIED",
        "DEPARTED",
        "ARRIVED",
        "IN_SERVICE",
        "COMPLETED",
    ]

    assert "side_branches" in data
    assert "REJECTED" in data["side_branches"]
    assert "REROUTED" in data["side_branches"]


def test_care_completion_endpoint(client: TestClient, test_db_session):
    """Verify care completion KPI analytics endpoint returns breakdowns."""
    token = get_auth_token(client, "admin@rahat.local")

    response = client.get(
        "/api/v1/dashboard/care-completion?time_range=all",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()

    assert "overall_completion_rate" in data
    assert "formula_definition" in data
    assert "by_urgency" in data
    assert "by_category" in data
    assert len(data["by_urgency"]) == 4  # EMERGENCY, HIGH, MEDIUM, LOW


# ---------------------------------------------------------------------------
# 5. Time Range & Parameter Validation Tests
# ---------------------------------------------------------------------------

def test_time_range_filtering(client: TestClient, test_db_session):
    """Verify time range filters ('today', '7d', '30d', 'all') execute cleanly."""
    token = get_auth_token(client, "admin@rahat.local")

    for tr in ["today", "7d", "30d", "all"]:
        res = client.get(
            f"/api/v1/dashboard/district?time_range={tr}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200

    # Invalid time range should return 400 Bad Request
    res_invalid = client.get(
        "/api/v1/dashboard/district?time_range=invalid_range",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_invalid.status_code == 400


# ---------------------------------------------------------------------------
# 6. Authentication & RBAC Tests
# ---------------------------------------------------------------------------

def test_dashboard_unauthenticated_fails(client: TestClient):
    """Verify all dashboard endpoints reject unauthenticated requests with 401."""
    endpoints = [
        "/api/v1/dashboard/frontline",
        "/api/v1/dashboard/facility",
        "/api/v1/dashboard/district",
        "/api/v1/dashboard/referral-funnel",
        "/api/v1/dashboard/care-completion",
    ]
    for ep in endpoints:
        res = client.get(ep)
        assert res.status_code == 401


def test_dashboard_unauthorized_role_fails(client: TestClient, test_db_session):
    """Verify roles without permission cannot access restricted dashboards (e.g. ASHA accessing District)."""
    asha_token = get_auth_token(client, "asha@rahat.local")  # ASHA

    # ASHA accessing district dashboard should return 403 Forbidden
    res = client.get(
        "/api/v1/dashboard/district",
        headers={"Authorization": f"Bearer {asha_token}"},
    )
    assert res.status_code == 403
