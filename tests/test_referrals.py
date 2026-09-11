"""Automated test suite for Phase 8: Referral Lifecycle & Tracking."""
import uuid
from datetime import datetime, timezone
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
    """Obtain JWT for ADMIN."""
    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "admin@rahat.local", "password": DEV_PASSWORD_PLAIN},
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
def cho_token(client):
    """Obtain JWT for CHO."""
    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": "cho@rahat.local", "password": DEV_PASSWORD_PLAIN},
    )
    return res.json()["access_token"]


# -------------------------------------------------------------------------
# Test Cases
# -------------------------------------------------------------------------

def test_create_referral_success(client, test_db_session, doctor_token):
    """Test creating a referral from Care Request to active Facility."""
    care_req = test_db_session.query(CareRequest).first()
    facility = test_db_session.query(Facility).filter(Facility.is_active == True).first()

    payload = {
        "care_request_id": str(care_req.id),
        "receiving_facility_id": str(facility.id),
        "referral_reason": "Acute cardiac evaluation requiring specialty intervention.",
        "urgency": "HIGH",
        "transport_mode": "108_AMBULANCE",
    }

    res = client.post(
        "/api/v1/referrals",
        json=payload,
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["referral_code"].startswith("REF-RAHAT-")
    assert data["status"] == "PENDING_ACCEPTANCE"
    assert data["urgency"] == "HIGH"
    assert data["receiving_facility_id"] == str(facility.id)
    assert data["care_request_id"] == str(care_req.id)
    assert data["patient_id"] == str(care_req.patient_id)

    # Check Care Request was updated to REFERRED
    test_db_session.refresh(care_req)
    assert care_req.status == "REFERRED"

    # Check Initial Event Created
    events = test_db_session.query(ReferralEvent).filter(ReferralEvent.referral_id == uuid.UUID(data["id"])).all()
    assert len(events) >= 1
    assert events[0].event_type == "REFERRAL_CREATED"
    assert events[0].to_status == "PENDING_ACCEPTANCE"


def test_create_referral_unauthenticated_fails(client, test_db_session):
    """Test referral creation requires valid auth token."""
    care_req = test_db_session.query(CareRequest).first()
    facility = test_db_session.query(Facility).first()

    res = client.post(
        "/api/v1/referrals",
        json={"care_request_id": str(care_req.id), "receiving_facility_id": str(facility.id)},
    )
    assert res.status_code == 401


def test_create_referral_invalid_care_request(client, test_db_session, doctor_token):
    """Test 404 when care request ID is non-existent."""
    facility = test_db_session.query(Facility).first()
    res = client.post(
        "/api/v1/referrals",
        json={"care_request_id": str(uuid.uuid4()), "receiving_facility_id": str(facility.id)},
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert res.status_code == 404
    assert "Care Request" in res.json()["detail"]


def test_create_referral_invalid_facility(client, test_db_session, doctor_token):
    """Test 404 when target facility does not exist."""
    care_req = test_db_session.query(CareRequest).first()
    res = client.post(
        "/api/v1/referrals",
        json={"care_request_id": str(care_req.id), "receiving_facility_id": str(uuid.uuid4())},
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert res.status_code == 404
    assert "Receiving Facility" in res.json()["detail"]


def test_create_referral_inactive_facility_rejected(client, test_db_session, doctor_token):
    """Test 400 error when attempting to refer to an inactive facility."""
    care_req = test_db_session.query(CareRequest).first()
    inactive_fac = Facility(
        id=uuid.uuid4(),
        name="Closed Rural Clinic",
        facility_type="PHC",
        tier_level=2,
        district="Sundargarh",
        state="Odisha",
        latitude=22.1,
        longitude=84.1,
        is_active=False,
    )
    test_db_session.add(inactive_fac)
    test_db_session.commit()

    res = client.post(
        "/api/v1/referrals",
        json={"care_request_id": str(care_req.id), "receiving_facility_id": str(inactive_fac.id)},
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert res.status_code == 400
    assert "inactive" in res.json()["detail"].lower()


def test_accept_referral_success(client, test_db_session, admin_token):
    """Test receiving facility accepting a referral."""
    care_req = test_db_session.query(CareRequest).first()
    facility = test_db_session.query(Facility).first()

    create_res = client.post(
        "/api/v1/referrals",
        json={"care_request_id": str(care_req.id), "receiving_facility_id": str(facility.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    ref_id = create_res.json()["id"]

    accept_res = client.post(
        f"/api/v1/referrals/{ref_id}/accept",
        json={"notes": "Bed reserved in emergency observation ward."},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert accept_res.status_code == 200
    data = accept_res.json()
    assert data["status"] == "ACCEPTED"
    assert data["accepted_at"] is not None


def test_reject_referral_with_reason_success(client, test_db_session, admin_token):
    """Test receiving facility rejecting a referral with a structured reason."""
    care_req = test_db_session.query(CareRequest).first()
    facility = test_db_session.query(Facility).first()

    create_res = client.post(
        "/api/v1/referrals",
        json={"care_request_id": str(care_req.id), "receiving_facility_id": str(facility.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    ref_id = create_res.json()["id"]

    reject_res = client.post(
        f"/api/v1/referrals/{ref_id}/reject",
        json={
            "rejection_reason": "CAPACITY_UNAVAILABLE",
            "rejection_notes": "ICU beds currently at full occupancy.",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert reject_res.status_code == 200
    data = reject_res.json()
    assert data["status"] == "REJECTED"
    assert data["rejection_reason"] == "CAPACITY_UNAVAILABLE"
    assert "ICU beds" in data["rejection_notes"]


def test_reject_referral_invalid_reason_rejected(client, test_db_session, admin_token):
    """Test rejection fails with 400 when reason is not in controlled enum."""
    care_req = test_db_session.query(CareRequest).first()
    facility = test_db_session.query(Facility).first()

    create_res = client.post(
        "/api/v1/referrals",
        json={"care_request_id": str(care_req.id), "receiving_facility_id": str(facility.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    ref_id = create_res.json()["id"]

    reject_res = client.post(
        f"/api/v1/referrals/{ref_id}/reject",
        json={"rejection_reason": "INVALID_REASON_CODE"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert reject_res.status_code == 400
    assert "Invalid rejection reason" in reject_res.json()["detail"]


def test_complete_primary_lifecycle(client, test_db_session, admin_token):
    """Test full journey from CREATED -> PENDING_ACCEPTANCE -> ACCEPTED -> PATIENT_NOTIFIED -> DEPARTED -> ARRIVED -> IN_SERVICE -> COMPLETED -> BACK_REFERRED."""
    care_req = test_db_session.query(CareRequest).first()
    facility = test_db_session.query(Facility).first()

    # 1. Create
    c_res = client.post(
        "/api/v1/referrals",
        json={"care_request_id": str(care_req.id), "receiving_facility_id": str(facility.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert c_res.status_code == 201
    ref_id = c_res.json()["id"]
    assert c_res.json()["status"] == "PENDING_ACCEPTANCE"

    # 2. Accept
    a_res = client.post(
        f"/api/v1/referrals/{ref_id}/accept",
        json={"notes": "Facility acceptance confirmed."},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert a_res.status_code == 200
    assert a_res.json()["status"] == "ACCEPTED"
    assert a_res.json()["accepted_at"] is not None

    # 3. Notify Patient
    n_res = client.post(
        f"/api/v1/referrals/{ref_id}/notify-patient",
        json={"notes": "ASHA worker briefed patient and arranged transport."},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert n_res.status_code == 200
    assert n_res.json()["status"] == "PATIENT_NOTIFIED"
    assert n_res.json()["notified_at"] is not None

    # 4. Depart
    d_res = client.post(
        f"/api/v1/referrals/{ref_id}/depart",
        json={"transport_mode": "108_AMBULANCE", "estimated_transit_minutes": 35},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert d_res.status_code == 200
    assert d_res.json()["status"] == "DEPARTED"
    assert d_res.json()["departed_at"] is not None
    assert d_res.json()["transport_status"] == "IN_TRANSIT"

    # 5. Arrive
    arr_res = client.post(
        f"/api/v1/referrals/{ref_id}/arrive",
        json={"notes": "Patient admitted to triage bay."},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert arr_res.status_code == 200
    assert arr_res.json()["status"] == "ARRIVED"
    assert arr_res.json()["arrived_at"] is not None

    # 6. Start Service
    s_res = client.post(
        f"/api/v1/referrals/{ref_id}/start-service",
        json={"notes": "Attending physician started ECG and stabilization."},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert s_res.status_code == 200
    assert s_res.json()["status"] == "IN_SERVICE"
    assert s_res.json()["in_service_at"] is not None

    # 7. Complete Service
    comp_res = client.post(
        f"/api/v1/referrals/{ref_id}/complete",
        json={"clinical_summary": "Condition stabilized. Prescribed medications for primary clinic follow-up."},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert comp_res.status_code == 200
    assert comp_res.json()["status"] == "COMPLETED"
    assert comp_res.json()["completed_at"] is not None

    # 8. Back-Refer
    br_res = client.post(
        f"/api/v1/referrals/{ref_id}/back-refer",
        json={"back_referral_notes": "Monitor BP twice weekly at local Sub-Center. Return in 14 days."},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert br_res.status_code == 200
    assert br_res.json()["status"] == "BACK_REFERRED"
    assert br_res.json()["back_referred_at"] is not None
    assert "Monitor BP" in br_res.json()["back_referral_notes"]

    # 9. Verify full timeline event log
    ev_res = client.get(
        f"/api/v1/referrals/{ref_id}/events",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert ev_res.status_code == 200
    events = ev_res.json()
    assert len(events) >= 8
    event_types = [e["event_type"] for e in events]
    assert "REFERRAL_CREATED" in event_types
    assert "FACILITY_ACCEPTED" in event_types
    assert "PATIENT_NOTIFIED" in event_types
    assert "PATIENT_DEPARTED" in event_types
    assert "PATIENT_ARRIVED" in event_types
    assert "SERVICE_STARTED" in event_types
    assert "SERVICE_COMPLETED" in event_types
    assert "BACK_REFERRED" in event_types


def test_reroute_rejected_referral_success(client, test_db_session, admin_token):
    """Test rejecting a referral and rerouting to a new facility."""
    care_req = test_db_session.query(CareRequest).first()
    facilities = test_db_session.query(Facility).filter(Facility.is_active == True).limit(2).all()
    fac1, fac2 = facilities[0], facilities[1]

    # Create referral to fac1
    c_res = client.post(
        "/api/v1/referrals",
        json={"care_request_id": str(care_req.id), "receiving_facility_id": str(fac1.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    ref1_id = c_res.json()["id"]

    # Reject by fac1
    client.post(
        f"/api/v1/referrals/{ref1_id}/reject",
        json={"rejection_reason": "SPECIALIST_UNAVAILABLE", "rejection_notes": "Cardiologist on leave."},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Reroute to fac2
    reroute_res = client.post(
        f"/api/v1/referrals/{ref1_id}/reroute",
        json={
            "new_receiving_facility_id": str(fac2.id),
            "reason": "Rerouted to District Hospital with on-duty specialist.",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert reroute_res.status_code == 201
    child_data = reroute_res.json()
    assert child_data["receiving_facility_id"] == str(fac2.id)
    assert child_data["parent_referral_id"] == ref1_id
    assert child_data["status"] == "PENDING_ACCEPTANCE"

    # Verify original referral is marked REROUTED
    orig_res = client.get(f"/api/v1/referrals/{ref1_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert orig_res.json()["status"] == "REROUTED"


def test_reroute_to_same_rejected_facility_fails(client, test_db_session, admin_token):
    """Test 400 error when trying to reroute back to the same facility that rejected."""
    care_req = test_db_session.query(CareRequest).first()
    facility = test_db_session.query(Facility).first()

    c_res = client.post(
        "/api/v1/referrals",
        json={"care_request_id": str(care_req.id), "receiving_facility_id": str(facility.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    ref_id = c_res.json()["id"]

    client.post(
        f"/api/v1/referrals/{ref_id}/reject",
        json={"rejection_reason": "FACILITY_CLOSED"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    reroute_res = client.post(
        f"/api/v1/referrals/{ref_id}/reroute",
        json={"new_receiving_facility_id": str(facility.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert reroute_res.status_code == 400
    assert "Cannot reroute to the same facility" in reroute_res.json()["detail"]


def test_invalid_state_transitions_rejected(client, test_db_session, admin_token):
    """Test state machine rejects illegal state jumps."""
    care_req = test_db_session.query(CareRequest).first()
    facility = test_db_session.query(Facility).first()

    c_res = client.post(
        "/api/v1/referrals",
        json={"care_request_id": str(care_req.id), "receiving_facility_id": str(facility.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    ref_id = c_res.json()["id"]

    # 1. CREATED/PENDING_ACCEPTANCE -> COMPLETED (Illegal jump)
    comp_res = client.post(
        f"/api/v1/referrals/{ref_id}/complete",
        json={"notes": "Trying to complete early."},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert comp_res.status_code == 400
    assert "Invalid referral state transition" in comp_res.json()["detail"]

    # 2. CREATED/PENDING_ACCEPTANCE -> ARRIVED (Illegal jump)
    arr_res = client.post(
        f"/api/v1/referrals/{ref_id}/arrive",
        json={"notes": "Arriving before departing."},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert arr_res.status_code == 400


def test_list_referrals_and_filtering(client, test_db_session, admin_token):
    """Test listing referrals with pagination and status filters."""
    care_req = test_db_session.query(CareRequest).first()
    facility = test_db_session.query(Facility).first()

    # Create referral
    client.post(
        "/api/v1/referrals",
        json={"care_request_id": str(care_req.id), "receiving_facility_id": str(facility.id), "urgency": "EMERGENCY"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    list_res = client.get(
        "/api/v1/referrals?status=PENDING_ACCEPTANCE&urgency=EMERGENCY",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert list_res.status_code == 200
    data = list_res.json()
    assert data["total"] >= 1
    assert data["items"][0]["status"] == "PENDING_ACCEPTANCE"
    assert data["items"][0]["urgency"] == "EMERGENCY"


def test_audit_log_created_for_referral_actions(client, test_db_session, admin_token):
    """Test that AuditLog captures referral lifecycle actions."""
    care_req = test_db_session.query(CareRequest).first()
    facility = test_db_session.query(Facility).first()

    c_res = client.post(
        "/api/v1/referrals",
        json={"care_request_id": str(care_req.id), "receiving_facility_id": str(facility.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    ref_id = c_res.json()["id"]

    logs = test_db_session.query(AuditLog).filter(
        AuditLog.entity_type == "Referral",
        AuditLog.entity_id == ref_id,
    ).all()
    assert len(logs) >= 1
    assert logs[0].action == "REFERRAL_CREATED"


def test_get_referral_by_id_and_events_endpoint(client, test_db_session, admin_token):
    """Test single referral detail endpoint and events timeline endpoint."""
    care_req = test_db_session.query(CareRequest).first()
    facility = test_db_session.query(Facility).first()

    c_res = client.post(
        "/api/v1/referrals",
        json={"care_request_id": str(care_req.id), "receiving_facility_id": str(facility.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    ref_id = c_res.json()["id"]

    get_res = client.get(f"/api/v1/referrals/{ref_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert get_res.status_code == 200
    assert get_res.json()["id"] == ref_id
    assert get_res.json()["care_request_id"] == str(care_req.id)

    ev_res = client.get(f"/api/v1/referrals/{ref_id}/events", headers={"Authorization": f"Bearer {admin_token}"})
    assert ev_res.status_code == 200
    assert len(ev_res.json()) >= 1


def test_receiving_facility_rbac_restrictions(client, test_db_session, doctor_token):
    """Test that a healthcare worker assigned to a different facility is forbidden from accepting/rejecting."""
    facilities = test_db_session.query(Facility).filter(Facility.is_active == True).limit(2).all()
    fac1, fac2 = facilities[0], facilities[1]
    care_req = test_db_session.query(CareRequest).first()

    # Assign doctor user to fac1
    doctor = test_db_session.query(User).filter(User.email == "doctor@rahat.local").first()
    doctor.facility_id = fac1.id
    test_db_session.commit()

    # Create referral destination is fac2
    ref = Referral(
        id=uuid.uuid4(),
        referral_code="REF-RAHAT-999999",
        care_request_id=care_req.id,
        patient_id=care_req.patient_id,
        origin_facility_id=fac1.id,
        destination_facility_id=fac2.id,
        referred_by_user_id=doctor.id,
        priority="HIGH",
        clinical_summary="Urgent referral.",
        status="PENDING_ACCEPTANCE",
    )
    test_db_session.add(ref)
    test_db_session.commit()

    # Doctor at fac1 tries to accept referral destined for fac2 -> 403 Forbidden
    accept_res = client.post(
        f"/api/v1/referrals/{ref.id}/accept",
        json={"notes": "Illegal acceptance attempt."},
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert accept_res.status_code == 403
    assert "receiving facility" in accept_res.json()["detail"].lower()


def test_additional_invalid_transitions(client, test_db_session, admin_token):
    """Test additional invalid state transitions: COMPLETED -> ARRIVED, REJECTED -> COMPLETED, etc."""
    care_req = test_db_session.query(CareRequest).first()
    facility = test_db_session.query(Facility).first()

    ref = Referral(
        id=uuid.uuid4(),
        referral_code="REF-RAHAT-888888",
        care_request_id=care_req.id,
        patient_id=care_req.patient_id,
        origin_facility_id=facility.id,
        destination_facility_id=facility.id,
        priority="MEDIUM",
        clinical_summary="Test transitions.",
        status="COMPLETED",
    )
    test_db_session.add(ref)
    test_db_session.commit()

    # 1. COMPLETED -> ARRIVED (Illegal)
    res1 = client.post(
        f"/api/v1/referrals/{ref.id}/arrive",
        json={"notes": "Arrive from completed."},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res1.status_code == 400

    # 2. REJECTED -> COMPLETED (Illegal)
    ref.status = "REJECTED"
    test_db_session.commit()

    res2 = client.post(
        f"/api/v1/referrals/{ref.id}/complete",
        json={"notes": "Complete from rejected."},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res2.status_code == 400

