"""Health check endpoint definition."""
from datetime import datetime, timezone
from fastapi import APIRouter
from app.core.config import settings
from app.schemas.health import HealthCheckResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health Check",
    description="Check the operational health of the RAHAT backend service.",
    tags=["System"],
)
async def get_health() -> HealthCheckResponse:
    """Return the health status of the application."""
    return HealthCheckResponse(
        status="ok",
        service="rahat-backend",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc),
    )
