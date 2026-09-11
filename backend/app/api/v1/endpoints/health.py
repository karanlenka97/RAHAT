"""Health check and readiness endpoint definitions."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.api.deps import get_db
from app.schemas.health import HealthCheckResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Liveness Health Check",
    description="Lightweight liveness probe checking operational responsiveness of RAHAT backend.",
    tags=["System"],
)
async def get_health() -> HealthCheckResponse:
    """Return the liveness health status of the application."""
    return HealthCheckResponse(
        status="ok",
        service="rahat-backend",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc),
    )


@router.get(
    "/health/ready",
    response_model=HealthCheckResponse,
    summary="Readiness Probe",
    description="Deep readiness probe checking database connectivity and system service health.",
    tags=["System"],
)
def get_readiness(db: Session = Depends(get_db)) -> HealthCheckResponse:
    """Verify backend and database connectivity readiness."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database readiness probe failed: {str(e)}",
        )

    return HealthCheckResponse(
        status="ok",
        service="rahat-backend",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        database=db_status,
        timestamp=datetime.now(timezone.utc),
    )
