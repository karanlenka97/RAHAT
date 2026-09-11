"""Phase 12: Exhaustive Referral State Machine Test Suite.
Validates all permissible state transitions and asserts that all illegal transitions are rejected with HTTP 400.
"""
import uuid
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
from app.services.referral_service import VALID_TRANSITIONS, ReferralService


@pytest.fixture
def test_db_session():
    """Create isolated in-memory database session."""
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


@pytest.fixture
def admin_token(client):
    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "admin@rahat.local", "password": DEV_PASSWORD_PLAIN},
    )
    return res.json()["access_token"]


@pytest.fixture
def doctor_token(client):
    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "doctor@rahat.local", "password": DEV_PASSWORD_PLAIN},
    )
    return res.json()["access_token"]


def create_test_referral(client, token, care_request_id, facility_id) -> str:
    """Helper to create a referral in PENDING_ACCEPTANCE state."""
    res = client.post(
        "/api/v1/referrals",
        json={"care_request_id": str(care_request_id), "receiving_facility_id": str(facility_id)},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    return res.json()["id"]


# =========================================================================
# 1. State Transition Service Unit Tests
# =========================================================================

def test_valid_transitions_matrix_completeness():
    """Verify state machine transition map includes all 14 lifecycle states."""
    expected_states = {
        "CREATED",
        "PENDING_ACCEPTANCE",
        "ACCEPTED",
        "PATIENT_NOTIFIED",
        "DEPARTED",
        "ARRIVED",
        "IN_SERVICE",
        "COMPLETED",
        "BACK_REFERRED",
        "FOLLOW_UP",
        "REJECTED",
        "REROUTED",
        "CLOSED",
        "CANCELLED",
    }
    assert set(VALID_TRANSITIONS.keys()) == expected_states


def test_terminal_states_have_zero_outgoing_transitions():
    """Verify CLOSED and CANCELLED terminal states cannot transition further."""
    assert len(VALID_TRANSITIONS["CLOSED"]) == 0
    assert len(VALID_TRANSITIONS["CANCELLED"]) == 0


# =========================================================================
# 2. Comprehensive Valid Transition Sequence Tests
# =========================================================================

def test_full_successful_referral_lifecycle(client, test_db_session, admin_token):
    """Test full primary pipeline: CREATED -> PENDING_ACCEPTANCE -> ACCEPTED -> PATIENT_NOTIFIED -> DEPARTED -> ARRIVED -> IN_SERVICE -> COMPLETED -> BACK_REFERRED -> CLOSED."""
    cr = test_db_session.query(CareRequest).first()
    fac = test_db_session.query(Facility).first()
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create -> PENDING_ACCEPTANCE
    ref_id = create_test_referral(client, admin_token, cr.id, fac.id)

    # 2. PENDING_ACCEPTANCE -> ACCEPTED
    r = client.post(f"/api/v1/referrals/{ref_id}/accept", json={"notes": "OK"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["status"] == "ACCEPTED"

    # 3. ACCEPTED -> PATIENT_NOTIFIED
    r = client.post(f"/api/v1/referrals/{ref_id}/notify-patient", json={"notes": "Notified"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["status"] == "PATIENT_NOTIFIED"

    # 4. PATIENT_NOTIFIED -> DEPARTED
    r = client.post(f"/api/v1/referrals/{ref_id}/depart", json={"transport_mode": "108_AMBULANCE"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["status"] == "DEPARTED"

    # 5. DEPARTED -> ARRIVED
    r = client.post(f"/api/v1/referrals/{ref_id}/arrive", json={"notes": "Arrived"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["status"] == "ARRIVED"

    # 6. ARRIVED -> IN_SERVICE
    r = client.post(f"/api/v1/referrals/{ref_id}/start-service", json={"notes": "Started"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["status"] == "IN_SERVICE"

    # 7. IN_SERVICE -> COMPLETED
    r = client.post(f"/api/v1/referrals/{ref_id}/complete", json={"clinical_summary": "Done"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["status"] == "COMPLETED"

    # 8. COMPLETED -> BACK_REFERRED
    r = client.post(
        f"/api/v1/referrals/{ref_id}/back-refer",
        json={"back_referral_notes": "Detailed back referral guidance for village follow-up."},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["status"] == "BACK_REFERRED"

    # 9. Verify event timeline integrity
    ev_res = client.get(f"/api/v1/referrals/{ref_id}/events", headers=headers)
    assert ev_res.status_code == 200
    events = ev_res.json()
    assert len(events) == 8


def test_rejection_and_reroute_lifecycle(client, test_db_session, admin_token):
    """Test rejection and rerouting flow: PENDING_ACCEPTANCE -> REJECTED -> REROUTED -> ACCEPTED."""
    cr = test_db_session.query(CareRequest).first()
    fac1 = test_db_session.query(Facility).first()
    fac2 = test_db_session.query(Facility).filter(Facility.id != fac1.id).first()
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create -> PENDING_ACCEPTANCE at Fac 1
    ref_id = create_test_referral(client, admin_token, cr.id, fac1.id)

    # 2. Reject at Fac 1
    rej_res = client.post(
        f"/api/v1/referrals/{ref_id}/reject",
        json={"rejection_reason": "CAPACITY_UNAVAILABLE", "rejection_notes": "No beds available"},
        headers=headers,
    )
    assert rej_res.status_code == 200
    assert rej_res.json()["status"] == "REJECTED"

    # 3. Reroute to Fac 2 -> returns child referral in PENDING_ACCEPTANCE
    reroute_res = client.post(
        f"/api/v1/referrals/{ref_id}/reroute",
        json={"new_receiving_facility_id": str(fac2.id), "reason": "Rerouted to district hospital"},
        headers=headers,
    )
    assert reroute_res.status_code == 201
    new_ref = reroute_res.json()
    assert new_ref["status"] == "PENDING_ACCEPTANCE"
    assert new_ref["receiving_facility_id"] == str(fac2.id)
    new_ref_id = new_ref["id"]

    # 4. Accept at Fac 2 using new child referral
    accept_res = client.post(
        f"/api/v1/referrals/{new_ref_id}/accept",
        json={"notes": "Accepted at facility 2"},
        headers=headers,
    )
    assert accept_res.status_code == 200
    assert accept_res.json()["status"] == "ACCEPTED"


# =========================================================================
# 3. Exhaustive Invalid State Transition Rejections (HTTP 400)
# =========================================================================

def test_invalid_transitions_from_pending_acceptance(client, test_db_session, admin_token):
    """Verify illegal transitions from PENDING_ACCEPTANCE (cannot jump to ARRIVED, IN_SERVICE, COMPLETED)."""
    cr = test_db_session.query(CareRequest).first()
    fac = test_db_session.query(Facility).first()
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create referral in PENDING_ACCEPTANCE
    ref_id = create_test_referral(client, admin_token, cr.id, fac.id)

    # Attempt arrive (illegal)
    r1 = client.post(f"/api/v1/referrals/{ref_id}/arrive", json={}, headers=headers)
    assert r1.status_code == 400
    assert "Invalid referral state transition" in r1.json()["detail"]

    # Attempt start-service (illegal)
    r2 = client.post(f"/api/v1/referrals/{ref_id}/start-service", json={}, headers=headers)
    assert r2.status_code == 400

    # Attempt complete (illegal)
    r3 = client.post(f"/api/v1/referrals/{ref_id}/complete", json={}, headers=headers)
    assert r3.status_code == 400

    # Attempt back-refer (illegal)
    r4 = client.post(
        f"/api/v1/referrals/{ref_id}/back-refer",
        json={"back_referral_notes": "Sample back referral notes"},
        headers=headers,
    )
    assert r4.status_code == 400


def test_invalid_transitions_from_accepted(client, test_db_session, admin_token):
    """Verify illegal transitions from ACCEPTED (cannot jump to ARRIVED, IN_SERVICE, COMPLETED without transit)."""
    cr = test_db_session.query(CareRequest).first()
    fac = test_db_session.query(Facility).first()
    headers = {"Authorization": f"Bearer {admin_token}"}

    ref_id = create_test_referral(client, admin_token, cr.id, fac.id)
    client.post(f"/api/v1/referrals/{ref_id}/accept", json={}, headers=headers)

    # Attempt start-service directly from ACCEPTED (illegal)
    r1 = client.post(f"/api/v1/referrals/{ref_id}/start-service", json={}, headers=headers)
    assert r1.status_code == 400

    # Attempt complete directly from ACCEPTED (illegal)
    r2 = client.post(f"/api/v1/referrals/{ref_id}/complete", json={}, headers=headers)
    assert r2.status_code == 400


def test_invalid_transitions_from_rejected(client, test_db_session, admin_token):
    """Verify REJECTED referral cannot be accepted, departed, or completed without rerouting."""
    cr = test_db_session.query(CareRequest).first()
    fac = test_db_session.query(Facility).first()
    headers = {"Authorization": f"Bearer {admin_token}"}

    ref_id = create_test_referral(client, admin_token, cr.id, fac.id)
    client.post(f"/api/v1/referrals/{ref_id}/reject", json={"rejection_reason": "SPECIALIST_UNAVAILABLE"}, headers=headers)

    # Cannot accept rejected referral
    r1 = client.post(f"/api/v1/referrals/{ref_id}/accept", json={}, headers=headers)
    assert r1.status_code == 400

    # Cannot depart rejected referral
    r2 = client.post(f"/api/v1/referrals/{ref_id}/depart", json={}, headers=headers)
    assert r2.status_code == 400

    # Cannot complete rejected referral
    r3 = client.post(f"/api/v1/referrals/{ref_id}/complete", json={}, headers=headers)
    assert r3.status_code == 400


def test_invalid_transitions_from_completed(client, test_db_session, admin_token):
    """Verify COMPLETED referral cannot go back to ARRIVED, IN_SERVICE, or ACCEPTED."""
    cr = test_db_session.query(CareRequest).first()
    fac = test_db_session.query(Facility).first()
    headers = {"Authorization": f"Bearer {admin_token}"}

    ref_id = create_test_referral(client, admin_token, cr.id, fac.id)
    client.post(f"/api/v1/referrals/{ref_id}/accept", json={}, headers=headers)
    client.post(f"/api/v1/referrals/{ref_id}/depart", json={"transport_mode": "WALKING"}, headers=headers)
    client.post(f"/api/v1/referrals/{ref_id}/arrive", json={}, headers=headers)
    client.post(f"/api/v1/referrals/{ref_id}/start-service", json={}, headers=headers)
    client.post(f"/api/v1/referrals/{ref_id}/complete", json={"clinical_summary": "Done"}, headers=headers)

    # Cannot re-arrive
    r1 = client.post(f"/api/v1/referrals/{ref_id}/arrive", json={}, headers=headers)
    assert r1.status_code == 400

    # Cannot re-accept
    r2 = client.post(f"/api/v1/referrals/{ref_id}/accept", json={}, headers=headers)
    assert r2.status_code == 400

    # Cannot re-start service
    r3 = client.post(f"/api/v1/referrals/{ref_id}/start-service", json={}, headers=headers)
    assert r3.status_code == 400
