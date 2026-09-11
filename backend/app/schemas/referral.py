"""Referral Management and Tracking Pydantic Schemas."""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class ReferralStatus(str, Enum):
    """Permitted states in the referral lifecycle state machine."""
    CREATED = "CREATED"
    PENDING_ACCEPTANCE = "PENDING_ACCEPTANCE"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    PATIENT_NOTIFIED = "PATIENT_NOTIFIED"
    DEPARTED = "DEPARTED"
    ARRIVED = "ARRIVED"
    IN_SERVICE = "IN_SERVICE"
    COMPLETED = "COMPLETED"
    BACK_REFERRED = "BACK_REFERRED"
    FOLLOW_UP = "FOLLOW_UP"
    CLOSED = "CLOSED"
    REROUTED = "REROUTED"
    CANCELLED = "CANCELLED"


class RejectionReason(str, Enum):
    """Controlled reasons for receiving facility referral rejection."""
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    CAPACITY_UNAVAILABLE = "CAPACITY_UNAVAILABLE"
    SPECIALIST_UNAVAILABLE = "SPECIALIST_UNAVAILABLE"
    FACILITY_CLOSED = "FACILITY_CLOSED"
    OTHER = "OTHER"


class ReferralUrgency(str, Enum):
    """Referral clinical urgency level."""
    EMERGENCY = "EMERGENCY"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# -------------------------------------------------------------------------
# Request Schemas
# -------------------------------------------------------------------------

class ReferralCreate(BaseModel):
    """Schema for initiating a new referral from a Care Request and Facility."""
    care_request_id: UUID = Field(..., description="Target Care Request UUID")
    receiving_facility_id: UUID = Field(..., description="Target Receiving Facility UUID")
    source_facility_id: Optional[UUID] = Field(None, description="Optional Origin Facility UUID")
    referral_reason: Optional[str] = Field(None, max_length=2000, description="Clinical reason for referral")
    clinical_summary: Optional[str] = Field(None, max_length=4000, description="Detailed clinical summary / provisional diagnosis")
    urgency: Optional[str] = Field("MEDIUM", description="Referral urgency level (EMERGENCY, HIGH, MEDIUM, LOW)")
    required_specialty: Optional[str] = Field(None, max_length=100, description="Required clinical specialty")
    required_capability: Optional[str] = Field(None, max_length=100, description="Specific service capability required")
    expected_arrival_time: Optional[datetime] = Field(None, description="Expected patient arrival timestamp")
    transport_mode: Optional[str] = Field(None, description="Transport mode (108_AMBULANCE, 102_AMBULANCE, PRIVATE_VEHICLE, etc.)")


class ReferralAcceptInput(BaseModel):
    """Schema for facility acceptance action."""
    notes: Optional[str] = Field(None, max_length=1000, description="Acceptance notes or admission instructions")
    expected_arrival_time: Optional[datetime] = Field(None, description="Updated expected arrival timestamp")


class ReferralRejectInput(BaseModel):
    """Schema for facility rejection action."""
    rejection_reason: str = Field(..., description="Controlled rejection reason (SERVICE_UNAVAILABLE, CAPACITY_UNAVAILABLE, etc.)")
    rejection_notes: Optional[str] = Field(None, max_length=1000, description="Detailed reason notes")


class ReferralNotifyInput(BaseModel):
    """Schema for patient notification action."""
    notes: Optional[str] = Field(None, max_length=1000, description="Notification method or counseling notes")


class ReferralDepartInput(BaseModel):
    """Schema for patient departure action."""
    transport_mode: Optional[str] = Field(None, max_length=100, description="Transport vehicle / ambulance ID or mode")
    estimated_transit_minutes: Optional[int] = Field(None, ge=1, le=1440, description="Estimated transit time in minutes")
    notes: Optional[str] = Field(None, max_length=1000, description="Departure remarks")


class ReferralArriveInput(BaseModel):
    """Schema for patient arrival action."""
    notes: Optional[str] = Field(None, max_length=1000, description="Triage or reception remarks upon arrival")


class ReferralStartServiceInput(BaseModel):
    """Schema for consultation or service initiation action."""
    notes: Optional[str] = Field(None, max_length=1000, description="Treating doctor or department notes")


class ReferralCompleteInput(BaseModel):
    """Schema for service completion action."""
    clinical_summary: Optional[str] = Field(None, max_length=4000, description="Treatment summary, discharge note, or outcome")
    notes: Optional[str] = Field(None, max_length=1000, description="General completion notes")


class ReferralBackReferInput(BaseModel):
    """Schema for issuing back-referral instructions to primary health center."""
    back_referral_notes: str = Field(..., min_length=5, max_length=4000, description="Clinical guidance and follow-up instructions for primary care worker")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional administrative remarks")


class ReferralRerouteInput(BaseModel):
    """Schema for rerouting a rejected referral to an alternative facility."""
    new_receiving_facility_id: UUID = Field(..., description="Alternative receiving facility UUID")
    reason: Optional[str] = Field(None, max_length=1000, description="Rerouting justification")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional clinical notes for new facility")


# -------------------------------------------------------------------------
# Response Schemas
# -------------------------------------------------------------------------

class ReferralEventResponse(BaseModel):
    """Immutable referral lifecycle event log entry."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    referral_id: UUID
    event_type: str
    previous_status: Optional[str] = None
    new_status: str
    performed_by: Optional[UUID] = None
    performer_name: Optional[str] = None
    performer_role: Optional[str] = None
    notes: Optional[str] = None
    event_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime


class ReferralResponse(BaseModel):
    """Detailed referral record response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    referral_code: str
    care_request_id: UUID
    care_request_number: Optional[str] = None
    care_category: Optional[str] = None
    required_service: Optional[str] = None

    patient_id: UUID
    patient_name: Optional[str] = None
    patient_code: Optional[str] = None
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None
    patient_phone: Optional[str] = None
    patient_village: Optional[str] = None

    source_facility_id: Optional[UUID] = None
    source_facility_name: Optional[str] = None
    receiving_facility_id: UUID
    receiving_facility_name: Optional[str] = None
    receiving_facility_type: Optional[str] = None

    created_by: Optional[UUID] = None
    creator_name: Optional[str] = None
    creator_role: Optional[str] = None
    parent_referral_id: Optional[UUID] = None

    status: str
    urgency: str
    referral_reason: Optional[str] = None
    clinical_summary: Optional[str] = None
    required_specialty: Optional[str] = None

    transport_mode: Optional[str] = None
    transport_status: Optional[str] = None
    estimated_transit_minutes: Optional[int] = None
    expected_arrival_time: Optional[datetime] = None

    rejection_reason: Optional[str] = None
    rejection_notes: Optional[str] = None
    back_referral_notes: Optional[str] = None

    initiated_at: datetime
    accepted_at: Optional[datetime] = None
    notified_at: Optional[datetime] = None
    departed_at: Optional[datetime] = None
    arrived_at: Optional[datetime] = None
    in_service_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    back_referred_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    events: Optional[List[ReferralEventResponse]] = None


class ReferralListResponse(BaseModel):
    """Paginated list of referrals."""
    items: List[ReferralResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
