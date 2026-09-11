"""Pydantic schemas for AI Referral Assistant, Summarization, Extraction, and Explanations."""
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field

DEFAULT_AI_DISCLAIMER = "AI-assisted — requires human review. Not a clinical diagnosis or treatment recommendation."
DEFAULT_EXPLANATION_DISCLAIMER = "AI-assisted — requires human review. Deterministic match factors remain the authoritative basis for facility selection."


# ---------------------------------------------------------------------------
# Referral Summarization
# ---------------------------------------------------------------------------

class ReferralAISummaryRequest(BaseModel):
    """Input payload to generate an AI summary for a Care Request."""
    care_request_id: uuid.UUID = Field(..., description="ID of the Care Request to summarize")


class ReferralAISummaryResponse(BaseModel):
    """Structured, non-diagnostic administrative summary of a Care Request."""
    care_request_id: uuid.UUID
    concise_summary: str = Field(..., description="1-2 sentence executive clinical summary of recorded complaint")
    presenting_information: str = Field(..., description="Details of chief symptoms and recorded vitals")
    relevant_history: Optional[str] = Field(None, description="Reported chronic conditions or previous episodes")
    requested_service: str = Field(..., description="Clinical department or service required")
    diagnostic_requirements: List[str] = Field(default_factory=list, description="Associated diagnostics recorded")
    specialist_requirement: bool = Field(False, description="Whether specialist consultation was flagged")
    administrative_notes: Optional[str] = Field(None, description="Drafted administrative referral justification note")
    missing_information: List[str] = Field(default_factory=list, description="Explicitly identified missing fields")
    disclaimer: str = Field(default=DEFAULT_AI_DISCLAIMER, description="Mandatory assistive disclaimer")
    is_ai_assisted: bool = Field(True, description="Flag indicating AI assistance was used")
    model_used: Optional[str] = Field(None, description="AI model or provider identifier")


# ---------------------------------------------------------------------------
# Structured Intake Extraction
# ---------------------------------------------------------------------------

class AIStructuredExtractionRequest(BaseModel):
    """Raw clinical text or unstructured intake complaint for structured extraction."""
    raw_text: str = Field(..., min_length=5, max_length=5000, description="Unstructured clinical intake notes")
    existing_care_category: Optional[str] = Field(None, description="Previously selected category if any")
    existing_urgency: Optional[str] = Field(None, description="Existing recorded urgency (AI cannot alter)")


class AIStructuredExtractionResponse(BaseModel):
    """Extracted structured fields from unstructured intake text."""
    symptoms_summary: str = Field(..., description="Synthesized symptoms summary from raw text")
    care_category: Optional[str] = Field(None, description="Identified care category (e.g. MATERNAL_HEALTH, EMERGENCY)")
    required_service: Optional[str] = Field(None, description="Suggested standard service label")
    diagnostic_requirements: List[str] = Field(default_factory=list, description="Extracted diagnostic needs")
    specialist_required: bool = Field(False, description="Extracted specialist requirement")
    urgency_as_recorded: Optional[str] = Field(None, description="Existing recorded urgency (unchanged by AI)")
    missing_information: List[str] = Field(default_factory=list, description="Missing intake elements")
    disclaimer: str = Field(default=DEFAULT_AI_DISCLAIMER, description="Mandatory assistive disclaimer")
    is_ai_assisted: bool = Field(True, description="Flag indicating AI assistance")


# ---------------------------------------------------------------------------
# Recommendation Factor Explanation
# ---------------------------------------------------------------------------

class AIRecommendationExplanationRequest(BaseModel):
    """Deterministic recommendation metrics to be formatted into plain-language explanation."""
    care_request_id: uuid.UUID
    facility_id: uuid.UUID
    facility_name: str
    overall_score: float = Field(..., ge=0.0, le=100.0)
    service_score: float = Field(default=0.0, ge=0.0, le=100.0)
    distance_score: float = Field(default=0.0, ge=0.0, le=100.0)
    diagnostic_score: float = Field(default=0.0, ge=0.0, le=100.0)
    specialist_score: float = Field(default=0.0, ge=0.0, le=100.0)
    availability_score: float = Field(default=0.0, ge=0.0, le=100.0)
    workload_score: float = Field(default=0.0, ge=0.0, le=100.0)
    matched_services: List[str] = Field(default_factory=list)
    distance_km: Optional[float] = None
    available_beds: Optional[int] = None


class AIRecommendationExplanationResponse(BaseModel):
    """Plain-language explanation of already-calculated deterministic recommendation factors."""
    facility_id: uuid.UUID
    facility_name: str
    explanation_text: str = Field(..., description="Clear explanation of why this facility scored high")
    key_factors: List[str] = Field(default_factory=list, description="Key deterministic scoring reasons")
    overall_score: float = Field(..., description="Deterministic overall match score preserved exactly")
    disclaimer: str = Field(default=DEFAULT_EXPLANATION_DISCLAIMER)
    is_ai_assisted: bool = Field(True)


# ---------------------------------------------------------------------------
# Apply AI Summary with Human Confirmation
# ---------------------------------------------------------------------------

class ApplyAISummaryRequest(BaseModel):
    """Human-confirmed action to apply AI summary text into CareRequest administrative notes."""
    care_request_id: uuid.UUID
    notes: Optional[str] = Field(None, description="Proposed administrative notes to update")
    symptoms_summary: Optional[str] = Field(None, description="Proposed refined symptoms summary")
    confirmed_by_user: bool = Field(..., description="Explicit human confirmation flag")


class ApplyAISummaryResponse(BaseModel):
    """Response confirming update of CareRequest with AI assisted text."""
    care_request_id: uuid.UUID
    status: str = "applied"
    message: str = "Care request administrative notes updated with AI-assisted summary after human review."
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
