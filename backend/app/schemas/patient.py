"""Pydantic schemas for Patient and Village entities."""
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class VillageSummary(BaseModel):
    """Clean summary of a Village habitational unit."""

    id: uuid.UUID
    name: str
    district: str
    state: str
    pincode: Optional[str] = None

    model_config = {"from_attributes": True}


class PatientBase(BaseModel):
    """Base patient data validation schema."""

    full_name: str = Field(..., min_length=2, max_length=150, description="Full name of the patient")
    age: Optional[int] = Field(None, ge=0, le=130, description="Patient age in years")
    gender: str = Field(..., description="Gender (MALE, FEMALE, OTHER)")
    phone: Optional[str] = Field(None, max_length=20, description="Contact phone number")
    village_id: Optional[uuid.UUID] = Field(None, description="Associated village UUID")
    address: Optional[str] = Field(None, max_length=255, description="Street / habitational address")
    emergency_contact_name: Optional[str] = Field(None, max_length=150, description="Emergency contact person name")
    emergency_contact_phone: Optional[str] = Field(None, max_length=20, description="Emergency contact phone number")
    abha_reference: Optional[str] = Field(None, max_length=50, description="Synthetic ABHA ID reference")
    blood_group: Optional[str] = Field(None, max_length=10, description="Blood group (e.g. A+, O+, B-)")
    chronic_conditions: Optional[List[str]] = Field(default_factory=list, description="List of pre-existing conditions")
    allergies: Optional[List[str]] = Field(default_factory=list, description="Known drug / food allergies")

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str) -> str:
        clean = v.strip().upper()
        if clean not in {"MALE", "FEMALE", "OTHER"}:
            raise ValueError("Gender must be one of: MALE, FEMALE, OTHER")
        return clean


class PatientCreate(PatientBase):
    """Schema for registering a new patient."""
    pass


class PatientUpdate(BaseModel):
    """Schema for updating permitted patient demographic and clinical index fields."""

    full_name: Optional[str] = Field(None, min_length=2, max_length=150)
    age: Optional[int] = Field(None, ge=0, le=130)
    gender: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    village_id: Optional[uuid.UUID] = None
    address: Optional[str] = Field(None, max_length=255)
    emergency_contact_name: Optional[str] = Field(None, max_length=150)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    abha_reference: Optional[str] = Field(None, max_length=50)
    blood_group: Optional[str] = Field(None, max_length=10)
    chronic_conditions: Optional[List[str]] = None
    allergies: Optional[List[str]] = None

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        clean = v.strip().upper()
        if clean not in {"MALE", "FEMALE", "OTHER"}:
            raise ValueError("Gender must be one of: MALE, FEMALE, OTHER")
        return clean


class PatientResponse(BaseModel):
    """Safe response schema for patient details."""

    id: uuid.UUID
    patient_code: str = Field(..., description="Unique system-generated patient code")
    full_name: str
    age: Optional[int] = None
    gender: str
    phone: Optional[str] = None
    village_id: Optional[uuid.UUID] = None
    village: Optional[VillageSummary] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact: Optional[str] = None
    abha_reference: Optional[str] = None
    blood_group: Optional[str] = None
    chronic_conditions: Optional[List[str]] = Field(default_factory=list)
    allergies: Optional[List[str]] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PatientListResponse(BaseModel):
    """Paginated patient listing response."""

    items: List[PatientResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
