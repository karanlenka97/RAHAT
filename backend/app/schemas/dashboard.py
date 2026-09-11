"""Dashboard Pydantic Schemas for Frontline, Facility, and District Operations."""
from datetime import datetime, timezone
from typing import List, Optional, Dict
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Common / Filter Schemas
# ---------------------------------------------------------------------------

class TimeRangeFilter(BaseModel):
    """Time range query parameter representation."""
    time_range: str = Field(
        default="all",
        description="Time filter: 'today', '7d', '30d', or 'all'",
    )


# ---------------------------------------------------------------------------
# Frontline Dashboard Schemas
# ---------------------------------------------------------------------------

class FrontlineActionItem(BaseModel):
    """Operational action/attention queue item for frontline healthcare workers."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    item_type: str = Field(description="'CARE_REQUEST' or 'REFERRAL'")
    patient_id: str
    patient_name: str
    patient_code: str
    urgency: str = Field(description="'EMERGENCY', 'HIGH', 'MEDIUM', 'LOW'")
    status: str
    action_required: str = Field(
        description="Human-readable pending action description, e.g. 'Needs Referral Creation', 'Awaiting Facility Acceptance'"
    )
    facility_name: Optional[str] = None
    village_name: Optional[str] = None
    elapsed_hours: float = Field(
        description="Hours elapsed since item creation or last status change"
    )
    created_at: datetime
    updated_at: Optional[datetime] = None
    deep_link: str = Field(description="Frontend route link to view or act upon")


class FrontlineRecentActivity(BaseModel):
    """Timestamped recent clinical or milestone activity item."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    item_type: str
    patient_name: str
    patient_code: str
    action_description: str
    timestamp: datetime
    deep_link: str


class FrontlineDashboardResponse(BaseModel):
    """Complete Frontline Dashboard payload for ASHA, ANM, CHO, and Medical Officers."""
    model_config = ConfigDict(from_attributes=True)

    role: str
    user_name: str
    total_patients: int
    active_care_requests: int
    urgent_care_requests: int
    pending_referrals: int
    action_required_count: int
    in_transit_referrals: int
    completed_referrals: int

    action_queue: List[FrontlineActionItem]
    recent_activity: List[FrontlineRecentActivity]
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Facility Dashboard Schemas
# ---------------------------------------------------------------------------

class FacilityCapabilityMetric(BaseModel):
    """Capability and workload operational status."""
    model_config = ConfigDict(from_attributes=True)

    capability_id: str
    service_name: str
    service_category: str
    availability_status: str  # AVAILABLE, LIMITED, UNAVAILABLE
    capacity: int
    current_load: int
    utilization_percent: float
    specialist_required: bool
    diagnostic_required: bool
    operating_hours: str


class FacilityReferralQueueItem(BaseModel):
    """Inbound/active referral in facility operational queue."""
    model_config = ConfigDict(from_attributes=True)

    referral_id: str
    referral_code: str
    care_request_id: str
    patient_id: str
    patient_name: str
    patient_code: str
    origin_facility_name: Optional[str] = None
    priority: str
    status: str
    transport_mode: Optional[str] = None
    expected_arrival_time: Optional[datetime] = None
    initiated_at: datetime
    elapsed_hours: float
    deep_link: str


class FacilityStatusBreakdown(BaseModel):
    """Breakdown of referrals by operational status."""
    pending_acceptance: int = 0
    accepted: int = 0
    patient_notified: int = 0
    in_transit: int = 0  # DEPARTED
    arrived: int = 0
    in_service: int = 0
    completed: int = 0
    back_referred: int = 0
    rejected: int = 0
    rerouted: int = 0


class FacilityDashboardResponse(BaseModel):
    """Complete Facility Dashboard payload for Facility Admins, Doctors, and Medical Officers."""
    model_config = ConfigDict(from_attributes=True)

    facility_id: str
    facility_name: str
    facility_type: str
    tier_level: int
    district: str
    state: str
    operational_status: str

    # Bed Tracking & Utilization
    total_beds: int
    available_beds: int
    occupied_beds: int
    bed_utilization_percent: float
    icu_beds_total: int
    icu_beds_available: int
    icu_beds_occupied: int
    icu_utilization_percent: float
    oxygen_supported_beds: int
    available_oxygen_beds: int
    ventilators_count: int
    available_ventilators: int

    # Referrals Overview
    active_referrals_count: int
    status_breakdown: FacilityStatusBreakdown
    operational_queue: List[FacilityReferralQueueItem]

    # Capabilities Summary
    total_capabilities_count: int
    available_capabilities_count: int
    limited_capabilities_count: int
    unavailable_capabilities_count: int
    capabilities: List[FacilityCapabilityMetric]

    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# District Dashboard Schemas
# ---------------------------------------------------------------------------

class FacilityPerformanceSummary(BaseModel):
    """District-level operational performance summary for a specific health facility."""
    model_config = ConfigDict(from_attributes=True)

    facility_id: str
    facility_name: str
    facility_type: str
    tier_level: int
    referrals_received: int
    referrals_accepted: int
    referrals_rejected: int
    referrals_completed: int
    active_referrals: int
    acceptance_rate: float
    avg_completion_hours: Optional[float] = None
    available_services_count: int
    total_beds: int
    available_beds: int
    bed_utilization_percent: float


class DistrictDashboardResponse(BaseModel):
    """Aggregate District Dashboard payload for District Admins and System Admins."""
    model_config = ConfigDict(from_attributes=True)

    district_name: str
    time_range: str
    total_care_requests: int
    total_referrals: int
    accepted_referrals: int
    rejected_referrals: int
    completed_referrals: int
    active_referrals: int
    urgent_emergency_count: int

    # Core RAHAT KPIs
    care_completion_rate: float = Field(
        description="Percentage of eligible referred care requests that reached completed/resolved status"
    )
    avg_referral_completion_hours: Optional[float] = Field(
        default=None,
        description="Average hours from referral initiation to completion"
    )

    # Distributions
    care_requests_by_category: Dict[str, int]
    care_requests_by_urgency: Dict[str, int]
    referrals_by_status: Dict[str, int]

    # Facility Performance Table
    facility_performance: List[FacilityPerformanceSummary]

    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Referral Funnel Schemas
# ---------------------------------------------------------------------------

class FunnelStageItem(BaseModel):
    """Individual stage item in referral funnel."""
    stage_key: str
    stage_name: str
    count: int
    percentage_of_total: float
    drop_off_count: int = 0
    drop_off_rate: float = 0.0


class ReferralFunnelResponse(BaseModel):
    """Referral funnel analytics response."""
    district: Optional[str] = None
    facility_id: Optional[str] = None
    time_range: str
    total_initiated: int
    stages: List[FunnelStageItem]
    side_branches: Dict[str, int] = Field(
        description="Counts for side branches such as REJECTED, REROUTED, CANCELLED"
    )
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Care Completion Schemas
# ---------------------------------------------------------------------------

class CareCompletionByGroup(BaseModel):
    """Grouped care completion metrics."""
    group_name: str
    total_care_requests: int
    referred_care_requests: int
    completed_care_requests: int
    completion_rate: float


class CareCompletionResponse(BaseModel):
    """Dedicated Care Completion KPI response with multi-dimensional breakdowns."""
    district: Optional[str] = None
    time_range: str
    total_care_requests: int
    referred_care_requests: int
    completed_care_requests: int
    overall_completion_rate: float
    formula_definition: str
    by_urgency: List[CareCompletionByGroup]
    by_category: List[CareCompletionByGroup]
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

