"""AI Referral Assistant API endpoints."""
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.schemas.ai import (
    ReferralAISummaryRequest,
    ReferralAISummaryResponse,
    AIStructuredExtractionRequest,
    AIStructuredExtractionResponse,
    AIRecommendationExplanationRequest,
    AIRecommendationExplanationResponse,
    ApplyAISummaryRequest,
    ApplyAISummaryResponse,
)
from app.services.ai_service import AIService

router = APIRouter()


@router.post(
    "/referral-summary",
    response_model=ReferralAISummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate AI-assisted structured administrative summary for a Care Request",
    description="Generates an administrative summary, identifying required clinical services and missing information. Strictly non-diagnostic and assistive.",
)
async def generate_referral_summary(
    payload: ReferralAISummaryRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Generate structured AI summary for a Care Request with data minimization."""
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return await AIService.generate_referral_summary(
        db=db,
        care_request_id=payload.care_request_id,
        user=current_user,
        client_ip=client_ip,
        user_agent=user_agent,
    )


@router.post(
    "/extract-intake",
    response_model=AIStructuredExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract structured intake fields from unstructured clinical complaint notes",
    description="Identifies potential service categories and diagnostic needs from unstructured text without altering urgency.",
)
async def extract_structured_intake(
    payload: AIStructuredExtractionRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Extract structured intake fields from free-text notes."""
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return await AIService.extract_structured_intake(
        db=db,
        request=payload,
        user=current_user,
        client_ip=client_ip,
        user_agent=user_agent,
    )


@router.post(
    "/explain-recommendation",
    response_model=AIRecommendationExplanationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate plain-language explanation of deterministic recommendation scoring factors",
    description="Explains why a facility was recommended based strictly on deterministic service match, bed availability, and distance.",
)
async def explain_recommendation(
    payload: AIRecommendationExplanationRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Explain deterministic recommendation factors."""
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return await AIService.explain_recommendation(
        db=db,
        request=payload,
        user=current_user,
        client_ip=client_ip,
        user_agent=user_agent,
    )


@router.post(
    "/apply-summary",
    response_model=ApplyAISummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Apply human-reviewed AI summary text to Care Request administrative notes",
    description="Updates permitted administrative notes on a Care Request after explicit human verification.",
)
def apply_ai_summary(
    payload: ApplyAISummaryRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Apply confirmed AI summary text to Care Request."""
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return AIService.apply_ai_summary(
        db=db,
        request=payload,
        user=current_user,
        client_ip=client_ip,
        user_agent=user_agent,
    )
