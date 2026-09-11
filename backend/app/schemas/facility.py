"""Pydantic schemas for Facility and FacilityCapability Management."""
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator


class FacilityType(str, Enum):
    """Controlled set of healthcare facility classifications."""
    AAM = "AAM"  # Ayushman Arogya Mandir
    SUB_CENTER = "SUB_CENTER"  # Sub-Health Center
    PHC = "PHC"  # Primary Health Center
    CHC = "CHC"  # Community Health Center
    RURAL_HOSPITAL = "RURAL_HOSPITAL"  # Sub-Divisional / Rural Hospital
    DISTRICT_HOSPITAL = "DISTRICT_HOSPITAL"  # District Headquarters Hospital
    SPECIALTY_HOSPITAL = "SPECIALTY_HOSPITAL"  # Tertiary / Specialty Teaching Hospital
    DIAGNOSTIC_CENTER = "DIAGNOSTIC_CENTER"  # Dedicated Diagnostic & Imaging Center


class ServiceCategory(str, Enum):
    """Controlled structure of clinical, diagnostic, and specialty services."""
    GENERAL_MEDICINE = "GENERAL_MEDICINE"
    CARDIOLOGY = "CARDIOLOGY"
    OBSTETRICS = "OBSTETRICS"
    PEDIATRICS = "PEDIATRICS"
    ORTHOPEDICS = "ORTHOPEDICS"
    LABORATORY = "LABORATORY"
    X_RAY = "X_RAY"
    ULTRASOUND = "ULTRASOUND"
    CT = "CT"
    DIALYSIS = "DIALYSIS"
    MENTAL_HEALTH = "MENTAL_HEALTH"
    EYE_CARE = "EYE_CARE"
    ENT = "ENT"
    DENTAL = "DENTAL"
    EMERGENCY = "EMERGENCY"
    OTHER = "OTHER"


class AvailabilityStatus(str, Enum):
    """Live capability availability level."""
    AVAILABLE = "AVAILABLE"
    LIMITED = "LIMITED"
    HIGH_LOAD = "HIGH_LOAD"
    UNAVAILABLE = "UNAVAILABLE"


# ---------------------------------------------------------------------------
# Facility Capability Schemas
# ---------------------------------------------------------------------------

class FacilityCapabilityCreate(BaseModel):
    """Schema for adding a new service capability to a facility."""
    service_name: str = Field(..., min_length=1, max_length=150, description="Specific name of service/procedure")
    service_category: ServiceCategory = Field(..., description="Standardized clinical service category")
    available: bool = Field(default=True, description="Whether capability is currently operational")
    availability_status: AvailabilityStatus = Field(default=AvailabilityStatus.AVAILABLE, description="Availability status level")
    capacity: int = Field(default=50, ge=0, description="Daily patient/test capacity (non-negative)")
    current_load: int = Field(default=0, ge=0, description="Current daily utilization/load (non-negative)")
    specialist_required: bool = Field(default=False, description="Whether specialist doctor is needed to render this service")
    diagnostic_required: bool = Field(default=False, description="Whether specialized diagnostic equipment is involved")
    operating_hours: Optional[str] = Field(default="24x7", max_length=100, description="Operating schedule (e.g. 24x7, 9am-5pm)")

    @model_validator(mode="after")
    def validate_capacity_and_load(self) -> "FacilityCapabilityCreate":
        if not self.service_name or not self.service_name.strip():
            raise ValueError("Service name cannot be empty.")
        if self.capacity < 0:
            raise ValueError("Capacity cannot be negative.")
        if self.current_load < 0:
            raise ValueError("Current load cannot be negative.")
        if self.capacity > 0 and self.current_load > self.capacity:
            raise ValueError("Current load cannot exceed capacity.")
        return self


class FacilityCapabilityUpdate(BaseModel):
    """Schema for updating an existing service capability."""
    service_name: Optional[str] = Field(None, min_length=1, max_length=150)
    service_category: Optional[ServiceCategory] = None
    available: Optional[bool] = None
    availability_status: Optional[AvailabilityStatus] = None
    capacity: Optional[int] = Field(None, ge=0)
    current_load: Optional[int] = Field(None, ge=0)
    specialist_required: Optional[bool] = None
    diagnostic_required: Optional[bool] = None
    operating_hours: Optional[str] = Field(None, max_length=100)

    @model_validator(mode="after")
    def validate_capacity_and_load(self) -> "FacilityCapabilityUpdate":
        if self.service_name is not None and not self.service_name.strip():
            raise ValueError("Service name cannot be empty.")
        if self.capacity is not None and self.capacity < 0:
            raise ValueError("Capacity cannot be negative.")
        if self.current_load is not None and self.current_load < 0:
            raise ValueError("Current load cannot be negative.")
        if (
            self.capacity is not None
            and self.current_load is not None
            and self.capacity > 0
            and self.current_load > self.capacity
        ):
            raise ValueError("Current load cannot exceed capacity.")
        return self


class FacilityCapabilityResponse(BaseModel):
    """Representation of a facility capability."""
    id: uuid.UUID
    facility_id: uuid.UUID
    service_name: str
    service_category: str
    available: bool
    availability_status: str
    capacity: int
    current_load: int
    specialist_required: bool
    diagnostic_required: bool
    operating_hours: Optional[str] = "24x7"
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Facility Schemas
# ---------------------------------------------------------------------------

class FacilityCreate(BaseModel):
    """Schema for creating a new healthcare facility."""
    name: str = Field(..., min_length=1, max_length=200, description="Official facility name")
    code: Optional[str] = Field(None, max_length=50, description="NIN / HFR / ABDM National Registry Code")
    facility_type: FacilityType = Field(..., description="Standard facility type classification")
    district: str = Field(..., min_length=1, max_length=100, description="District name")
    state: str = Field(default="Odisha", max_length=100, description="State name")
    address: Optional[str] = Field(None, max_length=255, description="Street address and landmark")
    pincode: Optional[str] = Field(None, max_length=10, description="Postal code")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="WGS84 GPS Latitude")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="WGS84 GPS Longitude")
    phone: Optional[str] = Field(None, max_length=20, description="Contact helpline phone number")
    operating_hours: Optional[str] = Field(default="24x7", max_length=100, description="Operating schedule")
    is_active: bool = Field(default=True, description="Whether facility is active in network")
    total_beds: int = Field(default=0, ge=0, description="Total sanctioned inpatient beds")
    available_beds: int = Field(default=0, ge=0, description="Currently vacant general beds")
    icu_beds: int = Field(default=0, ge=0, description="Total ICU beds")
    available_icu_beds: int = Field(default=0, ge=0, description="Currently vacant ICU beds")


class FacilityUpdate(BaseModel):
    """Schema for updating facility details."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    facility_type: Optional[FacilityType] = None
    district: Optional[str] = Field(None, min_length=1, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=255)
    pincode: Optional[str] = Field(None, max_length=10)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    phone: Optional[str] = Field(None, max_length=20)
    operating_hours: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    total_beds: Optional[int] = Field(None, ge=0)
    available_beds: Optional[int] = Field(None, ge=0)
    icu_beds: Optional[int] = Field(None, ge=0)
    available_icu_beds: Optional[int] = Field(None, ge=0)


class FacilityResponse(BaseModel):
    """Full representation of a facility."""
    id: uuid.UUID
    name: str
    code: Optional[str] = None
    facility_type: str
    tier_level: int
    district: str
    state: str
    address: Optional[str] = None
    pincode: Optional[str] = None
    latitude: float
    longitude: float
    phone: Optional[str] = None
    operating_hours: Optional[str] = "24x7"
    is_active: bool
    total_beds: int
    available_beds: int
    icu_beds: int
    available_icu_beds: int
    capabilities: List[FacilityCapabilityResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FacilityListResponse(BaseModel):
    """Paginated list of facilities."""
    items: List[FacilityResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class NearbyFacilityItem(BaseModel):
    """Facility item with calculated distance in kilometers."""
    facility: FacilityResponse
    distance_km: float


class NearbyFacilitiesResponse(BaseModel):
    """Geospatial radius lookup result."""
    center_latitude: float
    center_longitude: float
    radius_km: float
    count: int
    items: List[NearbyFacilityItem]
