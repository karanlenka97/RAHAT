"""Facility and FacilityCapability models with PostGIS spatial geometry and Phase 6 capabilities."""
import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.models.base import Base, GUID, UniversalJSON, TimestampMixin


class Facility(Base, TimestampMixin):
    """Healthcare facility (AAM, SUB_CENTER, PHC, CHC, RURAL_HOSPITAL, DISTRICT_HOSPITAL, SPECIALTY_HOSPITAL, DIAGNOSTIC_CENTER)."""

    __tablename__ = "facilities"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, index=True)
    code = Column(String(50), unique=True, index=True, nullable=True)  # NIN / HFR / ABDM ID
    facility_type = Column(String(50), nullable=False, index=True)  # AAM, SUB_CENTER, PHC, CHC, etc.
    tier_level = Column(Integer, default=1, nullable=False, index=True)

    address_line = Column(String(255), nullable=True)
    district = Column(String(100), nullable=False, index=True)
    state = Column(String(100), default="Odisha", nullable=False, index=True)
    pincode = Column(String(10), nullable=True, index=True)
    contact_phone = Column(String(20), nullable=True)
    contact_email = Column(String(255), nullable=True)

    # PostGIS Spatial Point (SRID 4326) & Decimal Coordinates
    location = Column(Geometry(geometry_type="POINT", srid=4326, spatial_index=True), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    operating_hours = Column(String(100), default="24x7", nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    operational_status = Column(String(50), default="OPERATIONAL", nullable=False)

    # Capacity and Live Bed Tracking
    total_beds = Column(Integer, default=0, nullable=False)
    available_beds = Column(Integer, default=0, nullable=False)
    icu_beds = Column(Integer, default=0, nullable=False)
    available_icu_beds = Column(Integer, default=0, nullable=False)
    oxygen_supported_beds = Column(Integer, default=0, nullable=False)
    available_oxygen_beds = Column(Integer, default=0, nullable=False)
    ventilators_count = Column(Integer, default=0, nullable=False)
    available_ventilators = Column(Integer, default=0, nullable=False)

    # Relationships
    served_villages = relationship(
        "Village",
        foreign_keys="Village.assigned_phc_facility_id",
        back_populates="assigned_phc",
    )
    capabilities = relationship(
        "FacilityCapability",
        back_populates="facility",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    staff = relationship(
        "HealthcareProfessional",
        back_populates="facility",
    )
    users = relationship(
        "User",
        back_populates="facility",
    )
    referrals_origin = relationship(
        "Referral",
        foreign_keys="Referral.origin_facility_id",
        back_populates="origin_facility",
    )
    referrals_destination = relationship(
        "Referral",
        foreign_keys="Referral.destination_facility_id",
        back_populates="destination_facility",
    )

    # Property Aliases for Phase 6 Specification
    @property
    def address(self) -> str | None:
        """Alias for address_line."""
        return self.address_line

    @address.setter
    def address(self, value: str | None):
        self.address_line = value

    @property
    def phone(self) -> str | None:
        """Alias for contact_phone."""
        return self.contact_phone

    @phone.setter
    def phone(self, value: str | None):
        self.contact_phone = value

    __table_args__ = (
        Index("idx_facility_type_district", "facility_type", "district"),
        Index("idx_facility_beds", "available_beds", "available_icu_beds"),
        Index("idx_facility_location_active", "latitude", "longitude", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Facility name={self.name} type={self.facility_type} district={self.district}>"


class FacilityCapability(Base, TimestampMixin):
    """Specific medical, diagnostic, surgical, or specialty capability of a facility."""

    __tablename__ = "facility_capabilities"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    facility_id = Column(GUID, ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True)

    service_name = Column(String(150), nullable=False, index=True)
    service_category = Column(String(100), nullable=False, index=True)  # GENERAL_MEDICINE, CARDIOLOGY, etc.
    available = Column(Boolean, default=True, nullable=False)
    availability_status = Column(String(50), default="AVAILABLE", nullable=False, index=True)  # AVAILABLE, LIMITED, UNAVAILABLE
    capacity = Column(Integer, default=50, nullable=False)
    current_load = Column(Integer, default=0, nullable=False)
    specialist_required = Column(Boolean, default=False, nullable=False)
    diagnostic_required = Column(Boolean, default=False, nullable=False)
    operating_hours = Column(String(100), default="24x7", nullable=True)

    metadata_json = Column(UniversalJSON, nullable=True)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    facility = relationship("Facility", back_populates="capabilities")

    # Property Aliases for Phase 2 / Phase 6 compatibility
    @property
    def name(self) -> str:
        """Alias for service_name."""
        return self.service_name

    @name.setter
    def name(self, value: str):
        self.service_name = value

    @property
    def capability_type(self) -> str:
        """Alias for service_category."""
        return self.service_category

    @capability_type.setter
    def capability_type(self, value: str):
        self.service_category = value

    @property
    def current_status(self) -> str:
        """Alias for availability_status."""
        return self.availability_status

    @current_status.setter
    def current_status(self, value: str):
        self.availability_status = value

    @property
    def is_available_24x7(self) -> bool:
        """Helper property for 24x7 check."""
        return self.operating_hours == "24x7"

    @is_available_24x7.setter
    def is_available_24x7(self, value: bool):
        if value:
            self.operating_hours = "24x7"

    __table_args__ = (
        Index("idx_capability_lookup", "service_category", "service_name", "availability_status"),
        Index("idx_facility_service", "facility_id", "service_category"),
    )

    def __repr__(self) -> str:
        return f"<FacilityCapability name={self.service_name} category={self.service_category} status={self.availability_status}>"
