"""Village database model with PostGIS spatial point."""
import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey, Index
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.models.base import Base, GUID, TimestampMixin


class Village(Base, TimestampMixin):
    """Village or habitational community unit for rural outreach."""

    __tablename__ = "villages"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(150), nullable=False, index=True)
    code = Column(String(50), unique=True, index=True, nullable=True)  # Census / LGD code
    sub_district_tehsil = Column(String(100), nullable=True, index=True)
    district = Column(String(100), nullable=False, index=True)
    state = Column(String(100), nullable=False, index=True)
    pincode = Column(String(10), nullable=True, index=True)
    population = Column(Integer, nullable=True)

    # PostGIS Spatial Point (SRID 4326 - WGS 84 GPS coordinates)
    location = Column(Geometry(geometry_type="POINT", srid=4326, spatial_index=True), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    assigned_phc_facility_id = Column(
        GUID,
        ForeignKey("facilities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    assigned_phc = relationship(
        "Facility",
        foreign_keys=[assigned_phc_facility_id],
        back_populates="served_villages",
    )
    patients = relationship("Patient", back_populates="village")
    care_requests = relationship("CareRequest", back_populates="village")

    __table_args__ = (
        Index("idx_villages_state_district", "state", "district"),
    )

    def __repr__(self) -> str:
        return f"<Village name={self.name} district={self.district}>"
