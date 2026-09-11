"""Health check schema."""
from datetime import datetime, timezone
from typing import Optional, Dict
from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    """Schema for health check endpoint responses."""

    status: str = Field(default="ok", description="Overall health status")
    service: str = Field(default="rahat-backend", description="Service identifier")
    version: str = Field(..., description="API Version")
    environment: str = Field(..., description="Deployment environment")
    database: Optional[str] = Field(default=None, description="Database readiness status")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC timestamp of the check")
