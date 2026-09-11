"""Healthcare professional profile database model."""
import uuid
from sqlalchemy import Column, String, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.models.base import Base, GUID, TimestampMixin


class HealthcareProfessional(Base, TimestampMixin):
    """Clinical staff profile (Specialists, General Doctors, Nurses, ANMs, ASHA workers)."""

    __tablename__ = "healthcare_professionals"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(
        GUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    facility_id = Column(
        GUID,
        ForeignKey("facilities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    professional_type = Column(String(50), nullable=False, index=True)  # SPECIALIST, DOCTOR, NURSE, ASHA, ANM
    registration_number = Column(String(100), unique=True, index=True, nullable=True)
    specialization = Column(String(150), nullable=True, index=True)
    department = Column(String(100), nullable=True)
    qualification = Column(String(150), nullable=True)
    duty_status = Column(String(50), default="ON_DUTY", nullable=False, index=True)
    contact_number = Column(String(20), nullable=True)

    # Relationships
    user = relationship("User", back_populates="healthcare_profile")
    facility = relationship("Facility", back_populates="staff")
    assigned_care_requests = relationship(
        "CareRequest",
        back_populates="assigned_professional",
    )

    __table_args__ = (
        Index("idx_prof_spec_facility", "specialization", "facility_id"),
    )

    def __repr__(self) -> str:
        return f"<HealthcareProfessional type={self.professional_type} spec={self.specialization}>"
