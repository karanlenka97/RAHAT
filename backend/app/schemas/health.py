"""Health check schema."""
from datetime import datetime
from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    """Schema for health check endpoint responses."""

    status: str = Field(default="ok", description="Overall health status")
    service: str = Field(default="rahat-backend", description="Service identifier")
    version: str = Field(..., description="API Version")
    environment: str = Field(..., description="Deployment environment")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="UTC timestamp of the check")
