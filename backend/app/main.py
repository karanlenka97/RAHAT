"""Main FastAPI application entrypoint."""
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.api import api_router
from app.schemas.health import HealthCheckResponse

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="RAHAT - Rural Assistance & Healthcare Access Tele-network API Foundation",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
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
    summary="Root Health Check",
    tags=["Health"],
)
async def health_check() -> HealthCheckResponse:
    """Primary health check endpoint."""
    return HealthCheckResponse(
        status="ok",
        service="rahat-backend",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc),
    )


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint providing service metadata."""
    return {
        "service": "RAHAT API",
        "version": settings.VERSION,
        "status": "online",
        "documentation": "/docs",
        "health": "/health",
    }
