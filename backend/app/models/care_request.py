"""CareRequest database model."""
import uuid
from sqlalchemy import Column, String, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.models.base import Base, GUID, UniversalJSON, TimestampMixin


class CareRequest(Base, TimestampMixin):
    """Initial triage, consultation, or care access request initiated by field workers or clinics."""

    __tablename__ = "care_requests"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    request_number = Column(String(50), unique=True, index=True, nullable=False)

    patient_id = Column(
        GUID,
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    village_id = Column(
        GUID,
        ForeignKey("villages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    origin_facility_id = Column(
        GUID,
        ForeignKey("facilities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_by_user_id = Column(
        GUID,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    assigned_professional_id = Column(
        GUID,
        ForeignKey("healthcare_professionals.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    urgency_level = Column(String(30), default="NORMAL", nullable=False, index=True)  # CRITICAL, URGENT, NORMAL, ROUTINE
    chief_complaint = Column(Text, nullable=False)
    symptoms = Column(UniversalJSON, nullable=True, default=list)
    vitals = Column(UniversalJSON, nullable=True, default=dict)  # bp, heart_rate, spo2, temp, etc.
    provisional_diagnosis = Column(Text, nullable=True)
    status = Column(String(50), default="SUBMITTED", nullable=False, index=True)  # SUBMITTED, TRIAGED, REFERRED, RESOLVED
    notes = Column(Text, nullable=True)

    # Relationships
    patient = relationship("Patient", back_populates="care_requests")
    village = relationship("Village", back_populates="care_requests")
    origin_facility = relationship("Facility", foreign_keys=[origin_facility_id])
    created_by_user = relationship(
        "User",
        foreign_keys=[created_by_user_id],
        back_populates="care_requests_created",
    )
    assigned_professional = relationship(
        "HealthcareProfessional",
        back_populates="assigned_care_requests",
    )
    referral = relationship(
        "Referral",
        back_populates="care_request",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_care_requests_urgency_status", "urgency_level", "status"),
    )

    def __repr__(self) -> str:
        return f"<CareRequest number={self.request_number} urgency={self.urgency_level} status={self.status}>"
