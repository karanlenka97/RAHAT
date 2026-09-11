"""Main FastAPI application entrypoint."""
from datetime import datetime, timezone
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.config import settings
from app.api.v1.api import api_router
from app.api.deps import get_db
from app.schemas.health import HealthCheckResponse
from app.api.v1.endpoints.health import get_readiness

is_prod = settings.ENVIRONMENT.lower() == "production" and not settings.DEBUG

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="RAHAT - Rural Assistance & Healthcare Access Tele-network API Foundation",
    openapi_url=None if is_prod else f"{settings.API_V1_STR}/openapi.json",
    docs_url=None if is_prod else "/docs",
    redoc_url=None if is_prod else "/redoc",
)

# Set up CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include API routers
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Root Liveness Probe",
    tags=["Health"],
)
async def health_check() -> HealthCheckResponse:
    """Primary liveness check endpoint."""
    return HealthCheckResponse(
        status="ok",
        service="rahat-backend",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc),
    )


@app.get(
    "/ready",
    response_model=HealthCheckResponse,
    summary="Root Readiness Probe",
    tags=["Health"],
)
def readiness_check(db: Session = Depends(get_db)) -> HealthCheckResponse:
    """Primary database and service readiness check endpoint."""
    return get_readiness(db=db)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint providing service metadata."""
    return {
        "service": "RAHAT API",
        "version": settings.VERSION,
        "status": "online",
        "documentation": "/docs" if not is_prod else "Disabled in production",
        "health": "/health",
        "ready": "/ready",
    }
