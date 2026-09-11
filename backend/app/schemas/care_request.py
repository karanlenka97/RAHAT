"""Pydantic schemas for Care Request Management."""
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.patient import VillageSummary


class CareCategory(str, Enum):
    """Controlled set of clinical care categories."""
    GENERAL_MEDICINE = "GENERAL_MEDICINE"
    MATERNAL_HEALTH = "MATERNAL_HEALTH"
    CHILD_HEALTH = "CHILD_HEALTH"
    EMERGENCY = "EMERGENCY"
    NCD = "NCD"
    MENTAL_HEALTH = "MENTAL_HEALTH"
    EYE_CARE = "EYE_CARE"
    ENT = "ENT"
    DENTAL = "DENTAL"
    DIAGNOSTIC = "DIAGNOSTIC"
    OTHER = "OTHER"


class UrgencyLevel(str, Enum):
    """Clinical urgency level selected by healthcare provider."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EMERGENCY = "EMERGENCY"


class CareRequestStatus(str, Enum):
    """Lifecycle status of a care request."""
    SUBMITTED = "SUBMITTED"
    TRIAGED = "TRIAGED"
    REFERRED = "REFERRED"
    RESOLVED = "RESOLVED"


class PatientCareRequestSummary(BaseModel):
    """Embedded summary of the patient for care request display."""
    id: uuid.UUID
    patient_code: str
    full_name: str
    age: Optional[int] = None
    gender: str
    phone: Optional[str] = None
    village: Optional[VillageSummary] = None

    model_config = ConfigDict(from_attributes=True)


class CreatorSummary(BaseModel):
    """Embedded summary of the healthcare worker who created the request."""
    id: uuid.UUID
    full_name: str
    phone: Optional[str] = None
    role: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CareRequestCreate(BaseModel):
    """Schema for creating a new care request for an existing patient."""
    patient_id: uuid.UUID = Field(..., description="ID of the registered patient")
    care_category: CareCategory = Field(..., description="Controlled clinical care category")
    required_service: str = Field(..., min_length=1, max_length=100, description="Required healthcare service")
    urgency: UrgencyLevel = Field(default=UrgencyLevel.LOW, description="Healthcare provider assessed urgency level")
    symptoms_summary: str = Field(..., min_length=1, max_length=2000, description="Summary of chief symptoms/complaints")
    diagnostic_requirements: List[str] = Field(default_factory=list, description="Diagnostic services required")
    specialist_required: bool = Field(default=False, description="Whether specialist attention is required")
    notes: Optional[str] = Field(None, max_length=2000, description="Additional confidential clinical notes")


class CareRequestUpdate(BaseModel):
    """Schema for updating permitted care request details."""
    care_category: Optional[CareCategory] = None
    required_service: Optional[str] = Field(None, min_length=1, max_length=100)
    urgency: Optional[UrgencyLevel] = None
    symptoms_summary: Optional[str] = Field(None, min_length=1, max_length=2000)
    diagnostic_requirements: Optional[List[str]] = None
    specialist_required: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=2000)


class CareRequestResponse(BaseModel):
    """Public representation of a care request."""
    id: uuid.UUID
    request_number: str
    patient_id: uuid.UUID
    patient: Optional[PatientCareRequestSummary] = None
    created_by: Optional[uuid.UUID] = None
    creator: Optional[CreatorSummary] = None
    care_category: str
    required_service: str
    urgency: str
    symptoms_summary: str
    diagnostic_requirements: List[str] = Field(default_factory=list)
    specialist_required: bool = False
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CareRequestListResponse(BaseModel):
    """Paginated list of care requests."""
    items: List[CareRequestResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
