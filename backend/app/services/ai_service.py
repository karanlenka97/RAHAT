"""AI Service orchestration layer for RAHAT.
Enforces privacy data minimization, RBAC, audit logging, rate limiting, and human-in-the-loop review.
"""
import uuid
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.care_request import CareRequest
from app.models.patient import Patient
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.ai import (
    ReferralAISummaryResponse,
    AIStructuredExtractionRequest,
    AIStructuredExtractionResponse,
    AIRecommendationExplanationRequest,
    AIRecommendationExplanationResponse,
    ApplyAISummaryRequest,
    ApplyAISummaryResponse,
)
from app.services.ai_provider import get_ai_provider

logger = logging.getLogger(__name__)

# Allowed RBAC roles for AI referral assistance
ALLOWED_AI_ROLES = {
    "ADMIN",
    "DISTRICT_ADMIN",
    "FACILITY_ADMIN",
    "DOCTOR",
    "MEDICAL_OFFICER",
    "CHO",
    "ANM",
    "ASHA",
}

# In-memory sliding window rate limiter: (user_id, operation) -> list of timestamp floats
_RATE_LIMIT_STORE: Dict[Tuple[str, str], list] = {}
RATE_LIMIT_WINDOW_SECONDS = 60
MAX_REQUESTS_PER_MINUTE = 30


def _check_rate_limit(user_id: str, operation: str) -> None:
    """Enforce per-user sliding window rate limiting for AI operations."""
    now = time.time()
    key = (user_id, operation)
    timestamps = _RATE_LIMIT_STORE.get(key, [])
    # Filter out timestamps older than window
    valid_timestamps = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW_SECONDS]

    if len(valid_timestamps) >= MAX_REQUESTS_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="AI assistance rate limit exceeded. Please wait a moment before trying again.",
        )

    valid_timestamps.append(now)
    _RATE_LIMIT_STORE[key] = valid_timestamps


class AIService:
    """Service providing secure, privacy-preserving, assistive AI operations."""

    @staticmethod
    def _verify_user_access(user: User, care_request: CareRequest = None) -> None:
        """Verify that user role is permitted to use AI referral assistance."""
        if not user or not user.role:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required for AI referral assistance.",
            )
        role_name = user.role.name if hasattr(user.role, "name") else str(user.role)
        if role_name not in ALLOWED_AI_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role_name}' is not authorized to access AI referral assistance.",
            )

    @staticmethod
    async def generate_referral_summary(
        db: Session,
        care_request_id: uuid.UUID,
        user: User,
        client_ip: str = None,
        user_agent: str = None,
    ) -> ReferralAISummaryResponse:
        """Generate structured clinical administrative summary with strict PII data minimization."""
        AIService._verify_user_access(user)
        _check_rate_limit(str(user.id), "referral_summary")

        # 1. Fetch Care Request
        cr = db.query(CareRequest).filter(CareRequest.id == care_request_id).first()
        if not cr:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Care Request with ID '{care_request_id}' not found.",
            )

        # 2. Privacy & Data Minimization: Extract only demographic and clinical complaint attributes
        # Strict rule: DO NOT send full name, phone number, address, or government IDs to AI
        patient = db.query(Patient).filter(Patient.id == cr.patient_id).first() if cr.patient_id else None
        demographics = {}
        history = None
        if patient:
            demographics = {
                "age": patient.age,
                "gender": patient.gender,
            }
            if patient.chronic_conditions:
                history = f"Chronic conditions: {', '.join(patient.chronic_conditions)}"

        context = {
            "care_request_id": cr.id,
            "symptoms_summary": cr.symptoms_summary,
            "care_category": cr.care_category,
            "required_service": cr.required_service,
            "diagnostic_requirements": cr.diagnostic_requirements or [],
            "specialist_required": cr.specialist_required,
            "urgency": cr.urgency,
            "demographics": demographics,
            "relevant_history": history,
        }

        # 3. Call AI Provider
        provider = get_ai_provider()
        try:
            summary = await provider.generate_referral_summary(context)
        except Exception as e:
            logger.error(f"AI Referral summary generation failed: {e}")
            # Audit log failure
            db.add(
                AuditLog(
                    id=uuid.uuid4(),
                    user_id=user.id,
                    action="AI_OPERATION_FAILED",
                    entity_type="CareRequest",
                    entity_id=str(cr.id),
                    details={"operation": "referral_summary", "error": str(e)},
                    ip_address=client_ip,
                    user_agent=user_agent,
                )
            )
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI Referral Assistant is temporarily unavailable. Please proceed manually.",
            )

        # 4. Audit Log Success (Metadata only - no sensitive PII stored in log details)
        db.add(
            AuditLog(
                id=uuid.uuid4(),
                user_id=user.id,
                action="AI_SUMMARY_REQUESTED",
                entity_type="CareRequest",
                entity_id=str(cr.id),
                details={
                    "operation": "referral_summary",
                    "model_used": summary.model_used,
                    "is_ai_assisted": True,
                },
                ip_address=client_ip,
                user_agent=user_agent,
            )
        )
        db.commit()

        return summary

    @staticmethod
    async def extract_structured_intake(
        db: Session,
        request: AIStructuredExtractionRequest,
        user: User,
        client_ip: str = None,
        user_agent: str = None,
    ) -> AIStructuredExtractionResponse:
        """Extract structured fields from raw complaint notes."""
        AIService._verify_user_access(user)
        _check_rate_limit(str(user.id), "extract_intake")

        provider = get_ai_provider()
        try:
            extraction = await provider.extract_structured_intake(
                raw_text=request.raw_text,
                existing_category=request.existing_care_category,
                existing_urgency=request.existing_urgency,
            )
        except Exception as e:
            logger.error(f"AI Structured extraction failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI Intake Extraction is temporarily unavailable.",
            )

        db.add(
            AuditLog(
                id=uuid.uuid4(),
                user_id=user.id,
                action="AI_EXTRACTION_REQUESTED",
                entity_type="CareRequest",
                entity_id=None,
                details={"operation": "extract_intake", "category": extraction.care_category},
                ip_address=client_ip,
                user_agent=user_agent,
            )
        )
        db.commit()

        return extraction

    @staticmethod
    async def explain_recommendation(
        db: Session,
        request: AIRecommendationExplanationRequest,
        user: User,
        client_ip: str = None,
        user_agent: str = None,
    ) -> AIRecommendationExplanationResponse:
        """Provide a plain-language assistive summary of deterministic recommendation factors."""
        AIService._verify_user_access(user)
        _check_rate_limit(str(user.id), "explain_recommendation")

        provider = get_ai_provider()
        explanation = await provider.explain_recommendation(request)

        db.add(
            AuditLog(
                id=uuid.uuid4(),
                user_id=user.id,
                action="AI_EXPLANATION_REQUESTED",
                entity_type="Facility",
                entity_id=str(request.facility_id),
                details={
                    "operation": "explain_recommendation",
                    "care_request_id": str(request.care_request_id),
                    "overall_score": request.overall_score,
                },
                ip_address=client_ip,
                user_agent=user_agent,
            )
        )
        db.commit()

        return explanation

    @staticmethod
    def apply_ai_summary(
        db: Session,
        request: ApplyAISummaryRequest,
        user: User,
        client_ip: str = None,
        user_agent: str = None,
    ) -> ApplyAISummaryResponse:
        """Apply human-reviewed and confirmed AI summary text to Care Request administrative notes."""
        AIService._verify_user_access(user)

        if not request.confirmed_by_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Applying AI summary requires explicit human review and confirmation.",
            )

        cr = db.query(CareRequest).filter(CareRequest.id == request.care_request_id).first()
        if not cr:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Care Request with ID '{request.care_request_id}' not found.",
            )

        # Update permitted administrative fields
        if request.notes is not None:
            cr.notes = request.notes
        if request.symptoms_summary is not None:
            cr.symptoms_summary = request.symptoms_summary

        cr.updated_at = datetime.now(timezone.utc)

        db.add(
            AuditLog(
                id=uuid.uuid4(),
                user_id=user.id,
                action="AI_SUMMARY_APPLIED",
                entity_type="CareRequest",
                entity_id=str(cr.id),
                details={
                    "confirmed_by_user": True,
                    "notes_updated": bool(request.notes),
                    "symptoms_updated": bool(request.symptoms_summary),
                },
                ip_address=client_ip,
                user_agent=user_agent,
            )
        )
        db.commit()
        db.refresh(cr)

        return ApplyAISummaryResponse(
            care_request_id=cr.id,
            status="applied",
            message="Care request administrative notes updated with AI-assisted summary after human review.",
            updated_at=cr.updated_at,
        )
