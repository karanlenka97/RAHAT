"""Pydantic schemas for Smart Facility Recommendation Engine."""
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class FactorScores(BaseModel):
    """Detailed score breakdown across the 6 deterministic factors (0.0 to 100.0)."""
    service_match: float = Field(..., ge=0.0, le=100.0, description="Service compatibility score (30% weight)")
    distance: float = Field(..., ge=0.0, le=100.0, description="Geographic proximity score (20% weight)")
    diagnostic_match: float = Field(..., ge=0.0, le=100.0, description="Diagnostic fulfillment score (20% weight)")
    specialist_match: float = Field(..., ge=0.0, le=100.0, description="Specialist availability score (15% weight)")
    availability: float = Field(..., ge=0.0, le=100.0, description="Operational readiness status score (10% weight)")
    workload: float = Field(..., ge=0.0, le=100.0, description="Bed/service capacity utilization score (5% weight)")


class FacilityRecommendationItem(BaseModel):
    """Individual ranked facility recommendation with factor breakdown and explanation."""
    facility_id: uuid.UUID
    facility_name: str
    facility_code: Optional[str] = None
    facility_type: str
    tier_level: int
    district: str
    state: str
    address: Optional[str] = None
    phone: Optional[str] = None
    distance_km: Optional[float] = None
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Composite weighted score (0-100)")
    factors: FactorScores
    matched_services: List[str] = Field(default_factory=list)
    availability_status: str
    specialist_available: bool
    diagnostics_available: List[str] = Field(default_factory=list)
    capacity: int = 0
    current_load: int = 0
    explanation: str

    model_config = ConfigDict(from_attributes=True)


class RecommendationResponse(BaseModel):
    """Output payload of the Smart Facility Recommendation Engine."""
    care_request_id: uuid.UUID
    patient_id: uuid.UUID
    patient_name: str
    care_category: Optional[str] = None
    required_service: Optional[str] = None
    urgency: str
    diagnostic_requirements: List[str] = Field(default_factory=list)
    specialist_required: bool
    total_candidates: int
    recommendations: List[FacilityRecommendationItem]
    generated_at: datetime
