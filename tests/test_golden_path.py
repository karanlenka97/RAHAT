"""Phase 12: Comprehensive Automated Golden Path End-to-End Integration Suite."""
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


def login_user(client: TestClient, identifier: str) -> str:
    """Helper to authenticate and return JWT access token."""
    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": identifier, "password": DEV_PASSWORD_PLAIN},
    )
    assert res.status_code == 200, f"Login failed for {identifier}: {res.text}"
    return res.json()["access_token"]


def test_complete_golden_path_e2e(client, test_db_session):
    """Execute the full 23-step RAHAT Golden Path from patient registration to referral completion & analytics."""
    # -------------------------------------------------------------------------
    # STEP 1: Frontline User Login (CHO)
    # -------------------------------------------------------------------------
    cho_token = login_user(client, "cho@rahat.local")
    cho_headers = {"Authorization": f"Bearer {cho_token}"}

    # Verify Current User Profile
    me_res = client.get("/api/v1/auth/me", headers=cho_headers)
    assert me_res.status_code == 200
    assert me_res.json()["role"] == "CHO"

    # -------------------------------------------------------------------------
    # STEP 2: Create a Synthetic Patient
    # -------------------------------------------------------------------------
    village = test_db_session.query(Village).first()
    assert village is not None

    patient_payload = {
        "full_name": "Ramesh Kumar Pradhan",
        "gender": "MALE",
        "date_of_birth": "1978-05-14",
        "age": 48,
        "phone": "+919876543210",
        "village_id": str(village.id),
        "abha_reference": "ABHA-9876-5432-1098",
        "blood_group": "B_POSITIVE",
        "chronic_conditions": ["Hypertension", "Type 2 Diabetes"],
        "allergies": ["Penicillin"],
    }
    patient_res = client.post("/api/v1/patients", json=patient_payload, headers=cho_headers)
    assert patient_res.status_code == 201
    patient_data = patient_res.json()
    patient_id = patient_data["id"]
    assert patient_data["patient_code"].startswith("RAHAT-P-")
    assert patient_data["full_name"] == "Ramesh Kumar Pradhan"

    # -------------------------------------------------------------------------
    # STEP 3: Create a Care Request
    # -------------------------------------------------------------------------
    care_request_payload = {
        "patient_id": patient_id,
        "care_category": "GENERAL_MEDICINE",
        "required_service": "Cardiology",
        "urgency": "HIGH",
        "symptoms_summary": "Patient experiencing severe retrosternal chest pain radiating to left arm for 3 hours with diaphoresis.",
        "diagnostic_requirements": ["12-Lead ECG", "CBC", "Troponin I"],
        "specialist_required": True,
        "notes": "Field worker triage: pulse 104 bpm, BP 160/95 mmHg. Immediate tertiary cardiology referral indicated.",
    }
    care_req_res = client.post("/api/v1/care-requests", json=care_request_payload, headers=cho_headers)
    assert care_req_res.status_code == 201
    care_req_data = care_req_res.json()
    care_request_id = care_req_data["id"]
    assert "CR" in care_req_data["request_number"]
    assert care_req_data["status"] == "SUBMITTED"
    assert care_req_data["urgency"] == "HIGH"
    assert care_req_data["specialist_required"] is True

    # -------------------------------------------------------------------------
    # STEP 4: Open & Inspect the Care Request
    # -------------------------------------------------------------------------
    get_cr_res = client.get(f"/api/v1/care-requests/{care_request_id}", headers=cho_headers)
    assert get_cr_res.status_code == 200
    assert get_cr_res.json()["id"] == care_request_id
    assert get_cr_res.json()["patient"]["full_name"] == "Ramesh Kumar Pradhan"

    # -------------------------------------------------------------------------
    # STEP 5: Generate AI Referral Summary (Assistive Guardrails)
    # -------------------------------------------------------------------------
    ai_summary_res = client.post(
        "/api/v1/ai/referral-summary",
        json={"care_request_id": care_request_id},
        headers=cho_headers,
    )
    assert ai_summary_res.status_code == 200
    ai_data = ai_summary_res.json()

    # Verify Assistive AI Invariants
    assert "AI-assisted — requires human review" in ai_data["disclaimer"]
    assert ai_data["is_ai_assisted"] is True
    assert ai_data["concise_summary"] is not None
    assert "Cardiology" in ai_data["requested_service"] or "General" in ai_data["requested_service"]
    # Verify no diagnostic disease labels or prescription medications in summary
    assert "amoxicillin" not in ai_data["concise_summary"].lower()
    assert "aspirin" not in ai_data["concise_summary"].lower()

    # -------------------------------------------------------------------------
    # STEP 6: Apply AI Summary with Human-in-the-Loop Confirmation
    # -------------------------------------------------------------------------
    apply_ai_res = client.post(
        "/api/v1/ai/apply-summary",
        json={
            "care_request_id": care_request_id,
            "notes": ai_data["administrative_notes"],
            "confirmed_by_user": True,
        },
        headers=cho_headers,
    )
    assert apply_ai_res.status_code == 200
    assert apply_ai_res.json()["status"] == "applied"

    # -------------------------------------------------------------------------
    # STEP 7: Open Facility Recommendations & Verify Deterministic Scoring
    # -------------------------------------------------------------------------
    rec_res = client.get(
        f"/api/v1/recommendations/{care_request_id}?limit=5",
        headers=cho_headers,
    )
    assert rec_res.status_code == 200
    rec_data = rec_res.json()
    assert rec_data["total_candidates"] >= 1
    recommendations = rec_data["recommendations"]
    assert len(recommendations) >= 1

    # Verify deterministic factor breakdown on top recommendation
    top_rec = recommendations[0]
    selected_facility_id = top_rec["facility_id"]
    assert top_rec["overall_score"] > 0
    assert "service_match" in top_rec["factors"]
    assert "distance" in top_rec["factors"]
    assert "diagnostic_match" in top_rec["factors"]
    assert "specialist_match" in top_rec["factors"]
    assert "availability" in top_rec["factors"]
    assert "workload" in top_rec["factors"]

    # -------------------------------------------------------------------------
    # STEP 8: Create Referral targeting Recommended Facility
    # -------------------------------------------------------------------------
    referral_payload = {
        "care_request_id": care_request_id,
        "receiving_facility_id": selected_facility_id,
        "urgency": "HIGH",
        "transport_mode": "108_AMBULANCE",
        "referral_reason": "Emergency cardiology evaluation for unstable angina.",
        "clinical_summary": "48yo male, severe acute chest pain with diaphoresis.",
    }
    ref_res = client.post("/api/v1/referrals", json=referral_payload, headers=cho_headers)
    assert ref_res.status_code == 201
    ref_data = ref_res.json()
    referral_id = ref_data["id"]
    assert ref_data["referral_code"].startswith("REF-RAHAT-")
    assert ref_data["status"] == "PENDING_ACCEPTANCE"
    assert ref_data["receiving_facility_id"] == selected_facility_id

    # Verify Care Request status updated to REFERRED
    updated_cr = client.get(f"/api/v1/care-requests/{care_request_id}", headers=cho_headers).json()
    assert updated_cr["status"] == "REFERRED"

    # -------------------------------------------------------------------------
    # STEP 9: Facility User Login (DOCTOR / Specialist)
    # -------------------------------------------------------------------------
    doctor_token = login_user(client, "doctor@rahat.local")
    doctor_headers = {"Authorization": f"Bearer {doctor_token}"}

    # -------------------------------------------------------------------------
    # STEP 10: Receiving Facility Inspects Incoming Referral
    # -------------------------------------------------------------------------
    incoming_res = client.get(
        f"/api/v1/referrals/{referral_id}",
        headers=doctor_headers,
    )
    assert incoming_res.status_code == 200
    assert incoming_res.json()["status"] == "PENDING_ACCEPTANCE"

    # -------------------------------------------------------------------------
    # STEP 11: Accept Referral
    # -------------------------------------------------------------------------
    accept_res = client.post(
        f"/api/v1/referrals/{referral_id}/accept",
        json={"notes": "Cardiology ICU bed reserved. On-call cardiologist notified."},
        headers=doctor_headers,
    )
    assert accept_res.status_code == 200
    assert accept_res.json()["status"] == "ACCEPTED"
    assert accept_res.json()["accepted_at"] is not None

    # -------------------------------------------------------------------------
    # STEP 12: Notify Patient & Escort Dispatch
    # -------------------------------------------------------------------------
    notify_res = client.post(
        f"/api/v1/referrals/{referral_id}/notify-patient",
        json={"notes": "Patient and family informed; 108 Ambulance dispatched to village."},
        headers=cho_headers,
    )
    assert notify_res.status_code == 200
    assert notify_res.json()["status"] == "PATIENT_NOTIFIED"
    assert notify_res.json()["notified_at"] is not None

    # -------------------------------------------------------------------------
    # STEP 13: Mark Patient Departed (In Transit)
    # -------------------------------------------------------------------------
    depart_res = client.post(
        f"/api/v1/referrals/{referral_id}/depart",
        json={"transport_mode": "108_AMBULANCE", "estimated_transit_minutes": 30},
        headers=cho_headers,
    )
    assert depart_res.status_code == 200
    assert depart_res.json()["status"] == "DEPARTED"
    assert depart_res.json()["transport_status"] == "IN_TRANSIT"

    # -------------------------------------------------------------------------
    # STEP 14: Mark Patient Arrived at Facility
    # -------------------------------------------------------------------------
    arrive_res = client.post(
        f"/api/v1/referrals/{referral_id}/arrive",
        json={"notes": "Ambulance arrived at emergency bay. Patient triaged by nursing officer."},
        headers=doctor_headers,
    )
    assert arrive_res.status_code == 200
    assert arrive_res.json()["status"] == "ARRIVED"
    assert arrive_res.json()["arrived_at"] is not None

    # -------------------------------------------------------------------------
    # STEP 15: Start Clinical Service
    # -------------------------------------------------------------------------
    start_res = client.post(
        f"/api/v1/referrals/{referral_id}/start-service",
        json={"notes": "Immediate 12-Lead ECG conducted. Cath lab team mobilized for coronary angiogram."},
        headers=doctor_headers,
    )
    assert start_res.status_code == 200
    assert start_res.json()["status"] == "IN_SERVICE"
    assert start_res.json()["in_service_at"] is not None

    # -------------------------------------------------------------------------
    # STEP 16: Complete Clinical Care
    # -------------------------------------------------------------------------
    complete_res = client.post(
        f"/api/v1/referrals/{referral_id}/complete",
        json={
            "clinical_summary": "Angioplasty successfully performed with drug-eluting stent. Hemodynamically stable.",
            "notes": "Low-salt diet, continue antiplatelet therapy, local PHC follow-up in 7 days.",
        },
        headers=doctor_headers,
    )
    assert complete_res.status_code == 200
    assert complete_res.json()["status"] == "COMPLETED"
    assert complete_res.json()["completed_at"] is not None

    # -------------------------------------------------------------------------
    # STEP 17: Back-Refer Patient to Originating Community/HWC
    # -------------------------------------------------------------------------
    back_refer_res = client.post(
        f"/api/v1/referrals/{referral_id}/back-refer",
        json={
            "back_referral_notes": "Post-PCI care plan sent to Sub-Center / HWC. ASHA to monitor vitals bi-weekly.",
        },
        headers=doctor_headers,
    )
    assert back_refer_res.status_code == 200
    assert back_refer_res.json()["status"] == "BACK_REFERRED"
    assert back_refer_res.json()["back_referred_at"] is not None
    assert "Post-PCI" in back_refer_res.json()["back_referral_notes"]

    # -------------------------------------------------------------------------
    # STEP 18: Verify Complete Immutable Event Timeline
    # -------------------------------------------------------------------------
    events_res = client.get(f"/api/v1/referrals/{referral_id}/events", headers=doctor_headers)
    assert events_res.status_code == 200
    events = events_res.json()
    assert len(events) >= 7

    event_statuses = [e["new_status"] for e in events]
    assert "PENDING_ACCEPTANCE" in event_statuses
    assert "ACCEPTED" in event_statuses
    assert "PATIENT_NOTIFIED" in event_statuses
    assert "DEPARTED" in event_statuses
    assert "ARRIVED" in event_statuses
    assert "IN_SERVICE" in event_statuses
    assert "COMPLETED" in event_statuses
    assert "BACK_REFERRED" in event_statuses

    # -------------------------------------------------------------------------
    # STEP 19: Verify Tamper-Evident Audit Logging
    # -------------------------------------------------------------------------
    admin_token = login_user(client, "admin@rahat.local")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    audit_entries = (
        test_db_session.query(AuditLog)
        .filter(AuditLog.entity_id == str(referral_id))
        .all()
    )
    assert len(audit_entries) >= 5

    # -------------------------------------------------------------------------
    # STEP 20: Verify Frontline Dashboard Reflects Live State
    # -------------------------------------------------------------------------
    frontline_dash = client.get("/api/v1/dashboard/frontline", headers=cho_headers)
    assert frontline_dash.status_code == 200
    f_data = frontline_dash.json()
    assert "active_care_requests" in f_data
    assert "action_queue" in f_data
    assert f_data["total_patients"] >= 1

    # -------------------------------------------------------------------------
    # STEP 21: Verify Facility Dashboard Reflects Operational Metrics
    # -------------------------------------------------------------------------
    facility_dash = client.get(
        f"/api/v1/dashboard/facility?facility_id={selected_facility_id}",
        headers=doctor_headers,
    )
    assert facility_dash.status_code == 200
    fac_data = facility_dash.json()
    assert fac_data["facility_id"] == str(selected_facility_id)
    assert "total_beds" in fac_data
    assert "status_breakdown" in fac_data

    # -------------------------------------------------------------------------
    # STEP 22: Verify District Analytics & Care Completion Rate
    # -------------------------------------------------------------------------
    district_admin_token = login_user(client, "district.admin@rahat.local")
    dist_headers = {"Authorization": f"Bearer {district_admin_token}"}

    dist_dash = client.get("/api/v1/dashboard/district", headers=dist_headers)
    assert dist_dash.status_code == 200
    d_data = dist_dash.json()
    assert "total_referrals" in d_data
    assert "completed_referrals" in d_data
    assert "care_completion_rate" in d_data
    assert d_data["total_referrals"] >= 1

    # -------------------------------------------------------------------------
    # STEP 23: Verify Referral Funnel API Output
    # -------------------------------------------------------------------------
    funnel_res = client.get("/api/v1/dashboard/referral-funnel", headers=dist_headers)
    assert funnel_res.status_code == 200
    funnel = funnel_res.json()
    assert "total_initiated" in funnel
    assert "stages" in funnel
    assert "side_branches" in funnel
    assert funnel["total_initiated"] >= 1
    assert len(funnel["stages"]) >= 1
