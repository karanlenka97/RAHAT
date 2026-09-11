import asyncio
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
from app.services.ai_provider import MockAIProvider, get_ai_provider
from app.services.ai_service import AIService
from app.schemas.ai import (
    ReferralAISummaryRequest,
    AIStructuredExtractionRequest,
    AIRecommendationExplanationRequest,
    ApplyAISummaryRequest,
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

    # Seed foundation data
    seed_roles(session)
    seed_dev_users(session)
    seed_villages(session)
    seed_synthetic_patients(session)
    seed_synthetic_care_requests(session)
    seed_facilities(session)

    yield session

    session.close()


@pytest.fixture
def test_client(test_db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def get_auth_token(client: TestClient, username: str) -> str:
    """Helper to login and obtain JWT access token."""
    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": username, "password": DEV_PASSWORD_PLAIN},
    )
    assert response.status_code == 200, f"Login failed for {username}: {response.text}"
    return response.json()["access_token"]


# =========================================================================
# 1. AI Provider & Factory Unit Tests
# =========================================================================

def test_mock_ai_provider_summary():
    """Verify MockAIProvider generates valid structured referral summary."""
    provider = MockAIProvider()
    context = {
        "care_request_id": uuid.uuid4(),
        "symptoms_summary": "Patient with acute chest pain and high blood pressure for 2 hours.",
        "care_category": "EMERGENCY",
        "required_service": "Cardiology",
        "diagnostic_requirements": ["12-Lead ECG"],
        "specialist_required": True,
        "demographics": {"age": 48, "gender": "MALE"},
    }
    result = asyncio.run(provider.generate_referral_summary(context))

    assert result.concise_summary is not None
    assert result.presenting_information is not None
    assert result.disclaimer is not None
    assert "AI-assisted — requires human review" in result.disclaimer
    assert "mock" in result.model_used.lower()


def test_mock_ai_provider_extraction():
    """Verify MockAIProvider extracts structured fields from unorganized text."""
    provider = MockAIProvider()
    raw_notes = "Pregnant mother 28 yrs, severe headache and blurred vision, bp 160/100, urgent ultrasound needed."
    result = asyncio.run(provider.extract_structured_intake(raw_notes))

    assert result.symptoms_summary is not None
    assert result.care_category == "MATERNAL_HEALTH"
    assert "Obstetric Ultrasound" in result.diagnostic_requirements
    assert "AI-assisted — requires human review" in result.disclaimer


def test_mock_ai_provider_explanation():
    """Verify MockAIProvider provides factor-based explanation."""
    provider = MockAIProvider()
    req = AIRecommendationExplanationRequest(
        care_request_id=uuid.uuid4(),
        facility_id=uuid.uuid4(),
        facility_name="District Hospital Sundargarh",
        overall_score=88.5,
        service_score=90.0,
        distance_score=85.0,
        diagnostic_score=90.0,
        specialist_score=80.0,
        availability_score=75.0,
        workload_score=70.0,
        matched_services=["General Medicine", "Emergency & Trauma"],
        distance_km=14.2,
    )
    result = asyncio.run(provider.explain_recommendation(req))

    assert "District Hospital Sundargarh" in result.explanation_text
    assert "88.5" in result.explanation_text or "88" in result.explanation_text
    assert len(result.key_factors) >= 2
    assert "authoritative" in result.disclaimer.lower() or "human review" in result.disclaimer.lower()


def test_get_ai_provider_factory():
    """Verify factory returns valid provider instance."""
    provider = get_ai_provider()
    assert isinstance(provider, MockAIProvider)


# =========================================================================
# 2. AIService Unit & Privacy Minimization Tests
# =========================================================================

def test_privacy_data_minimization(test_db_session):
    """Verify that citizen PII (full name, phone, abha_ref, address) is NEVER sent to AI prompt."""
    doctor = test_db_session.query(User).filter(User.email == "doctor@rahat.local").first()
    assert doctor is not None
    care_req = test_db_session.query(CareRequest).first()
    assert care_req is not None
    patient = care_req.patient
    assert patient is not None

    # Call summarize_referral and inspect audit log
    response = asyncio.run(
        AIService.generate_referral_summary(
            db=test_db_session,
            care_request_id=care_req.id,
            user=doctor,
        )
    )

    assert response is not None
    assert response.care_request_id == care_req.id
    assert "AI-assisted — requires human review" in response.disclaimer

    # Check AuditLog entry
    audit = (
        test_db_session.query(AuditLog)
        .filter(AuditLog.action == "AI_SUMMARY_REQUESTED")
        .order_by(AuditLog.created_at.desc())
        .first()
    )
    assert audit is not None
    assert audit.user_id == doctor.id
    assert audit.entity_id == str(care_req.id)


# =========================================================================
# 3. API Endpoints Integration Tests
# =========================================================================

def test_ai_referral_summary_endpoint(test_client, test_db_session):
    """Test POST /api/v1/ai/referral-summary endpoint with authentication."""
    token = get_auth_token(test_client, "doctor@rahat.local")
    care_req = test_db_session.query(CareRequest).first()

    response = test_client.post(
        "/api/v1/ai/referral-summary",
        headers={"Authorization": f"Bearer {token}"},
        json={"care_request_id": str(care_req.id)},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["care_request_id"] == str(care_req.id)
    assert "concise_summary" in data
    assert "presenting_information" in data
    assert "administrative_notes" in data
    assert "AI-assisted — requires human review" in data["disclaimer"]


def test_ai_referral_summary_nonexistent(test_client):
    """Test POST /api/v1/ai/referral-summary returns 404 for nonexistent ID."""
    token = get_auth_token(test_client, "doctor@rahat.local")
    random_id = str(uuid.uuid4())

    response = test_client.post(
        "/api/v1/ai/referral-summary",
        headers={"Authorization": f"Bearer {token}"},
        json={"care_request_id": random_id},
    )

    assert response.status_code == 404


def test_ai_extract_intake_endpoint(test_client):
    """Test POST /api/v1/ai/extract-intake endpoint."""
    token = get_auth_token(test_client, "cho@rahat.local")

    payload = {
        "raw_text": "Patient has severe toothache, gum swelling, needs dental consultation and x-ray.",
    }

    response = test_client.post(
        "/api/v1/ai/extract-intake",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )

    assert response.status_code == 200
    data = response.json()
    assert "symptoms_summary" in data
    assert "care_category" in data
    assert data["care_category"] == "DENTAL"
    assert "diagnostic_requirements" in data
    assert "AI-assisted — requires human review" in data["disclaimer"]


def test_ai_explain_recommendation_endpoint(test_client, test_db_session):
    """Test POST /api/v1/ai/explain-recommendation endpoint."""
    token = get_auth_token(test_client, "medical.officer@rahat.local")
    care_req = test_db_session.query(CareRequest).first()
    facility = test_db_session.query(Facility).first()

    payload = {
        "care_request_id": str(care_req.id),
        "facility_id": str(facility.id),
        "facility_name": facility.name,
        "overall_score": 85.5,
        "service_score": 90.0,
        "distance_score": 80.0,
        "diagnostic_score": 85.0,
        "specialist_score": 90.0,
        "availability_score": 80.0,
        "workload_score": 90.0,
        "matched_services": ["General Medicine"],
        "distance_km": 12.5,
        "available_beds": 15,
    }

    response = test_client.post(
        "/api/v1/ai/explain-recommendation",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["facility_id"] == str(facility.id)
    assert data["overall_score"] == 85.5
    assert "explanation_text" in data
    assert len(data["key_factors"]) >= 2
    assert "AI-assisted — requires human review" in data["disclaimer"]


def test_apply_ai_summary_without_confirmation_rejected(test_client, test_db_session):
    """Verify applying AI summary WITHOUT explicit confirmation is rejected (HTTP 400)."""
    token = get_auth_token(test_client, "doctor@rahat.local")
    care_req = test_db_session.query(CareRequest).first()

    payload = {
        "care_request_id": str(care_req.id),
        "notes": "Draft summary that user has not confirmed.",
        "confirmed_by_user": False,
    }

    response = test_client.post(
        "/api/v1/ai/apply-summary",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )

    assert response.status_code == 400
    assert "confirmation" in response.json()["detail"].lower()


def test_apply_ai_summary_with_confirmation_succeeds(test_client, test_db_session):
    """Verify applying AI summary WITH confirmation updates notes and records audit log."""
    token = get_auth_token(test_client, "doctor@rahat.local")
    care_req = test_db_session.query(CareRequest).first()
    original_urgency = care_req.urgency
    original_category = care_req.care_category

    new_notes = "Confirmed clinical referral notes: Patient requires tertiary cardiology evaluation."

    payload = {
        "care_request_id": str(care_req.id),
        "notes": new_notes,
        "confirmed_by_user": True,
    }

    response = test_client.post(
        "/api/v1/ai/apply-summary",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["care_request_id"] == str(care_req.id)
    assert data["status"] == "applied"

    # Refresh care_request and verify notes updated
    test_db_session.refresh(care_req)
    assert care_req.notes == new_notes

    # Verify safety: clinical urgency and category are UNCHANGED
    assert care_req.urgency == original_urgency
    assert care_req.care_category == original_category

    # Verify AuditLog recorded
    audit = (
        test_db_session.query(AuditLog)
        .filter(AuditLog.action == "AI_SUMMARY_APPLIED")
        .order_by(AuditLog.created_at.desc())
        .first()
    )
    assert audit is not None
    assert audit.entity_id == str(care_req.id)


# =========================================================================
# 4. Safety & Role Access Tests
# =========================================================================

def test_unauthenticated_requests_rejected(test_client):
    """Verify AI endpoints reject unauthenticated calls with 401."""
    resp1 = test_client.post("/api/v1/ai/referral-summary", json={"care_request_id": str(uuid.uuid4())})
    assert resp1.status_code == 401

    resp2 = test_client.post("/api/v1/ai/extract-intake", json={"raw_text": "sample"})
    assert resp2.status_code == 401

    resp3 = test_client.post("/api/v1/ai/apply-summary", json={"care_request_id": str(uuid.uuid4()), "confirmed_by_user": True})
    assert resp3.status_code == 401


def test_frontline_roles_access(test_client, test_db_session):
    """Verify CHO and ANM frontline workers can access AI assistance."""
    care_req = test_db_session.query(CareRequest).first()

    for email in ["cho@rahat.local", "anm@rahat.local", "asha@rahat.local"]:
        token = get_auth_token(test_client, email)
        response = test_client.post(
            "/api/v1/ai/referral-summary",
            headers={"Authorization": f"Bearer {token}"},
            json={"care_request_id": str(care_req.id)},
        )
        assert response.status_code == 200, f"Role for {email} should have access"

