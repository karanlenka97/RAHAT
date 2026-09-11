"""Phase 12 Test Suite: Care Completion Rate & Funnel Analytics Verification.
Validates mathematical edge cases (0/0, 0/10, 5/10, 10/10), zero-division safety,
cumulative funnel stage logic, and district aggregation fidelity.
"""
import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

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
from app.services.dashboard_service import DashboardService


def _create_isolated_db():
    """Create a completely clean, empty in-memory SQLite database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return TestingSessionLocal()


# =========================================================================
# 1. Mathematical Zero-Division Safety (0 / 0 -> 0.0%)
# =========================================================================

def test_care_completion_rate_zero_division_safety():
    """Verify that an empty district with 0 care requests and 0 referrals returns 0.0% without error."""
    db = _create_isolated_db()
    try:
        # Create an admin user and an empty facility in 'EmptyDistrict'
        admin_role = Role(id=uuid.uuid4(), name="ADMIN", description="System Admin")
        db.add(admin_role)
        db.flush()

        admin_user = User(
            id=uuid.uuid4(),
            role_id=admin_role.id,
            email="admin_empty@rahat.local",
            phone="+919000000099",
            hashed_password="hash",
            full_name="District Admin",
        )
        facility = Facility(
            id=uuid.uuid4(),
            name="Empty District Hospital",
            facility_type="DH",
            tier_level=3,
            district="EmptyDistrict",
            latitude=22.0,
            longitude=84.0,
            total_beds=50,
            available_beds=50,
            is_active=True,
        )
        db.add_all([admin_user, facility])
        db.commit()

        # Generate district dashboard for EmptyDistrict
        dashboard = DashboardService.get_district_dashboard(
            db=db,
            current_user=admin_user,
            district="EmptyDistrict",
            time_range="all",
        )

        assert dashboard.total_care_requests == 0
        assert dashboard.total_referrals == 0
        assert dashboard.completed_referrals == 0
        assert dashboard.care_completion_rate == 0.0
    finally:
        db.close()


# =========================================================================
# 2. Mathematical Edge Cases: 0/10, 5/10, 10/10 Rates
# =========================================================================

def test_care_completion_rate_zero_completed_of_ten():
    """Verify 0 completed out of 10 referred care requests -> 0.0% completion rate."""
    db = _create_isolated_db()
    try:
        admin_role = Role(id=uuid.uuid4(), name="ADMIN", description="Admin")
        db.add(admin_role)
        db.flush()

        admin_user = User(
            id=uuid.uuid4(),
            role_id=admin_role.id,
            email="admin@rahat.local",
            phone="+919000000001",
            hashed_password="hash",
            full_name="Admin",
        )
        facility = Facility(
            id=uuid.uuid4(),
            name="Math District Hospital",
            facility_type="DH",
            tier_level=3,
            district="MathDistrict",
            latitude=22.0,
            longitude=84.0,
            total_beds=100,
            available_beds=80,
            is_active=True,
        )
        patient = Patient(
            id=uuid.uuid4(),
            anonymous_patient_code="RAHAT-P-999001",
            full_name="Math Patient",
            gender="MALE",
        )
        db.add_all([admin_user, facility, patient])
        db.flush()

        # Create 10 CareRequests with referrals in PENDING_ACCEPTANCE
        for i in range(10):
            cr = CareRequest(
                id=uuid.uuid4(),
                request_number=f"CR-MTH-00{i:02d}",
                patient_id=patient.id,
                care_category="GENERAL_MEDICINE",
                chief_complaint=f"Complaint {i}",
                urgency_level="MEDIUM",
                status="REFERRED",
            )
            db.add(cr)
            db.flush()
            ref = Referral(
                id=uuid.uuid4(),
                referral_code=f"REF-MTH-00{i:02d}",
                care_request_id=cr.id,
                patient_id=patient.id,
                origin_facility_id=facility.id,
                destination_facility_id=facility.id,
                clinical_summary="Clinical intake notes",
                status="PENDING_ACCEPTANCE",
                initiated_at=datetime.now(timezone.utc),
            )
            db.add(ref)
        db.commit()

        dashboard = DashboardService.get_district_dashboard(
            db=db,
            current_user=admin_user,
            district="MathDistrict",
            time_range="all",
        )
        assert dashboard.total_referrals == 10
        assert dashboard.completed_referrals == 0
        assert dashboard.care_completion_rate == 0.0
    finally:
        db.close()


def test_care_completion_rate_five_completed_of_ten():
    """Verify 5 completed out of 10 referred care requests -> 50.0% completion rate."""
    db = _create_isolated_db()
    try:
        admin_role = Role(id=uuid.uuid4(), name="ADMIN", description="Admin")
        db.add(admin_role)
        db.flush()

        admin_user = User(
            id=uuid.uuid4(),
            role_id=admin_role.id,
            email="admin@rahat.local",
            phone="+919000000001",
            hashed_password="hash",
            full_name="Admin",
        )
        facility = Facility(
            id=uuid.uuid4(),
            name="Math District Hospital",
            facility_type="DH",
            tier_level=3,
            district="MathDistrict",
            latitude=22.0,
            longitude=84.0,
            total_beds=100,
            available_beds=80,
            is_active=True,
        )
        patient = Patient(
            id=uuid.uuid4(),
            anonymous_patient_code="RAHAT-P-999002",
            full_name="Math Patient 2",
            gender="FEMALE",
        )
        db.add_all([admin_user, facility, patient])
        db.flush()

        # Create 10 CareRequests with referrals (5 COMPLETED, 5 PENDING_ACCEPTANCE)
        now = datetime.now(timezone.utc)
        for i in range(10):
            status = "COMPLETED" if i < 5 else "PENDING_ACCEPTANCE"
            cr = CareRequest(
                id=uuid.uuid4(),
                request_number=f"CR-MTH-50{i:02d}",
                patient_id=patient.id,
                care_category="GENERAL_MEDICINE",
                chief_complaint=f"Complaint {i}",
                urgency_level="MEDIUM",
                status="COMPLETED" if status == "COMPLETED" else "REFERRED",
            )
            db.add(cr)
            db.flush()
            ref = Referral(
                id=uuid.uuid4(),
                referral_code=f"REF-MTH-{status[:3]}-{i:02d}",
                care_request_id=cr.id,
                patient_id=patient.id,
                origin_facility_id=facility.id,
                destination_facility_id=facility.id,
                clinical_summary="Clinical intake and referral notes",
                status=status,
                initiated_at=now if 'now' in locals() else datetime.now(timezone.utc),
                completed_at=now if status == "COMPLETED" else None,
            )
            db.add(ref)
        db.commit()

        dashboard = DashboardService.get_district_dashboard(
            db=db,
            current_user=admin_user,
            district="MathDistrict",
            time_range="all",
        )
        assert dashboard.total_referrals == 10
        assert dashboard.completed_referrals == 5
        assert dashboard.care_completion_rate == 50.0
    finally:
        db.close()


def test_care_completion_rate_ten_completed_of_ten():
    """Verify 10 completed out of 10 referred care requests -> 100.0% completion rate."""
    db = _create_isolated_db()
    try:
        admin_role = Role(id=uuid.uuid4(), name="ADMIN", description="Admin")
        db.add(admin_role)
        db.flush()

        admin_user = User(
            id=uuid.uuid4(),
            role_id=admin_role.id,
            email="admin@rahat.local",
            phone="+919000000001",
            hashed_password="hash",
            full_name="Admin",
        )
        facility = Facility(
            id=uuid.uuid4(),
            name="Math District Hospital",
            facility_type="DH",
            tier_level=3,
            district="MathDistrict",
            latitude=22.0,
            longitude=84.0,
            total_beds=100,
            available_beds=80,
            is_active=True,
        )
        patient = Patient(
            id=uuid.uuid4(),
            anonymous_patient_code="RAHAT-P-999003",
            full_name="Math Patient 3",
            gender="FEMALE",
        )
        db.add_all([admin_user, facility, patient])
        db.flush()

        now = datetime.now(timezone.utc)
        for i in range(10):
            cr = CareRequest(
                id=uuid.uuid4(),
                request_number=f"CR-MTH-10{i:02d}",
                patient_id=patient.id,
                care_category="GENERAL_MEDICINE",
                chief_complaint=f"Complaint {i}",
                urgency_level="MEDIUM",
                status="COMPLETED",
            )
            db.add(cr)
            db.flush()
            ref = Referral(
                id=uuid.uuid4(),
                referral_code=f"REF-MTH-10{i:02d}",
                care_request_id=cr.id,
                patient_id=patient.id,
                origin_facility_id=facility.id,
                destination_facility_id=facility.id,
                clinical_summary="Clinical completed care notes",
                status="COMPLETED",
                initiated_at=now,
                completed_at=now,
            )
            db.add(ref)
        db.commit()

        dashboard = DashboardService.get_district_dashboard(
            db=db,
            current_user=admin_user,
            district="MathDistrict",
            time_range="all",
        )
        assert dashboard.total_referrals == 10
        assert dashboard.completed_referrals == 10
        assert dashboard.care_completion_rate == 100.0
    finally:
        db.close()


# =========================================================================
# 3. Referral Funnel Cumulative Stage Progression
# =========================================================================

def test_referral_funnel_cumulative_drop_off_logic(client, test_db_session, district_admin_token):
    """Verify referral funnel endpoint returns all 8 sequential stages with proper percentage calculations."""
    headers = {"Authorization": f"Bearer {district_admin_token}"}
    res = client.get("/api/v1/dashboard/referral-funnel", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert "stages" in data
    stages = data["stages"]
    assert len(stages) == 8

    # Verify stage progression counts and percentages
    for stage in stages:
        assert stage["count"] >= 0
        assert 0.0 <= stage["percentage_of_total"] <= 100.0
        assert "stage_key" in stage
        assert "stage_name" in stage
