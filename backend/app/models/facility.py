"""Facility and FacilityCapability models with PostGIS spatial geometry."""
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
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.models.base import Base, GUID, UniversalJSON, TimestampMixin


class Facility(Base, TimestampMixin):
    """Healthcare facility (SC, PHC, CHC, SDH, DH, Tertiary Hospital)."""

    __tablename__ = "facilities"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, index=True)
    code = Column(String(50), unique=True, index=True, nullable=True)  # NIN / HFR / ABDM ID
    facility_type = Column(String(50), nullable=False, index=True)  # SC, PHC, CHC, SDH, DH, TERTIARY
    tier_level = Column(Integer, default=1, nullable=False, index=True)

    address_line = Column(String(255), nullable=True)
    district = Column(String(100), nullable=False, index=True)
    state = Column(String(100), nullable=False, index=True)
    pincode = Column(String(10), nullable=True, index=True)
    contact_phone = Column(String(20), nullable=True)
    contact_email = Column(String(255), nullable=True)

    # PostGIS Spatial Point (SRID 4326)
    location = Column(Geometry(geometry_type="POINT", srid=4326, spatial_index=True), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

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

    __table_args__ = (
        Index("idx_facility_type_district", "facility_type", "district"),
        Index("idx_facility_beds", "available_beds", "available_icu_beds"),
    )

    def __repr__(self) -> str:
        return f"<Facility name={self.name} type={self.facility_type} district={self.district}>"


class FacilityCapability(Base, TimestampMixin):
    """Specific medical, diagnostic, surgical, or specialty capability of a facility."""

    __tablename__ = "facility_capabilities"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    facility_id = Column(GUID, ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    capability_type = Column(String(100), nullable=False, index=True)  # SPECIALTY, DIAGNOSTIC, NICU, BLOOD_BANK, etc.
    name = Column(String(150), nullable=False, index=True)
    is_available_24x7 = Column(Boolean, default=True, nullable=False)
    current_status = Column(String(50), default="AVAILABLE", nullable=False)  # AVAILABLE, LIMITED, UNAVAILABLE
    metadata_json = Column(UniversalJSON, nullable=True)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    facility = relationship("Facility", back_populates="capabilities")

    __table_args__ = (
        UniqueConstraint("facility_id", "capability_type", "name", name="uq_facility_capability"),
        Index("idx_capability_lookup", "capability_type", "name", "current_status"),
    )

    def __repr__(self) -> str:
        return f"<FacilityCapability name={self.name} type={self.capability_type}>"
