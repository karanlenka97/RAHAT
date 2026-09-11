"""Smart Facility Recommendation API endpoints."""
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.recommendation import RecommendationResponse
from app.services.recommendation_service import RecommendationEngineService

router = APIRouter()


@router.get(
    "/{care_request_id}",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get facility recommendations for care request",
    description="Calculate deterministic, explainable multi-factor suitability scores for healthcare facilities matching a clinical care request.",
)
def get_facility_recommendations(
    care_request_id: uuid.UUID,
    limit: int = Query(5, ge=1, le=20, description="Maximum number of top-ranked facilities to return (1-20)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecommendationResponse:
    """Generate and return ranked healthcare facility recommendations."""
    return RecommendationEngineService.get_recommendations_for_care_request(
        db=db,
        care_request_id=care_request_id,
        limit=limit,
    )
