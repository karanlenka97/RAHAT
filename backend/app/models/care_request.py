"""CareRequest database model."""
import uuid
from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Index
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

    # Core Phase 5 Care Categorization & Service Requirements
    care_category = Column(String(50), nullable=True, index=True)
    required_service = Column(String(100), nullable=True, index=True)
    urgency_level = Column(String(30), default="LOW", nullable=False, index=True)  # LOW, MEDIUM, HIGH, EMERGENCY
    diagnostic_requirements = Column(UniversalJSON, nullable=True, default=list)
    specialist_required = Column(Boolean, default=False, nullable=False)

    chief_complaint = Column(Text, nullable=False)
    symptoms = Column(UniversalJSON, nullable=True, default=list)
    vitals = Column(UniversalJSON, nullable=True, default=dict)
    provisional_diagnosis = Column(Text, nullable=True)
    status = Column(String(50), default="SUBMITTED", nullable=False, index=True)  # SUBMITTED, TRIAGED, REFERRED, RESOLVED
    notes = Column(Text, nullable=True)

    # Relationships
    patient = relationship("Patient", back_populates="care_requests", lazy="joined")
    village = relationship("Village", back_populates="care_requests", lazy="joined")
    origin_facility = relationship("Facility", foreign_keys=[origin_facility_id])
    created_by_user = relationship(
        "User",
        foreign_keys=[created_by_user_id],
        back_populates="care_requests_created",
        lazy="joined",
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

    # Property Aliases for Phase 5 Specification
    @property
    def created_by(self) -> uuid.UUID | None:
        """Alias for created_by_user_id."""
        return self.created_by_user_id

    @created_by.setter
    def created_by(self, value: uuid.UUID | None):
        self.created_by_user_id = value

    @property
    def symptoms_summary(self) -> str:
        """Alias for chief_complaint."""
        return self.chief_complaint

    @symptoms_summary.setter
    def symptoms_summary(self, value: str):
        self.chief_complaint = value

    @property
    def urgency(self) -> str:
        """Alias for urgency_level."""
        return self.urgency_level

    @urgency.setter
    def urgency(self, value: str):
        self.urgency_level = value

    __table_args__ = (
        Index("idx_care_requests_urgency_status", "urgency_level", "status"),
        Index("idx_care_requests_patient_urgency", "patient_id", "urgency_level"),
    )

    def __repr__(self) -> str:
        return f"<CareRequest number={self.request_number} category={self.care_category} urgency={self.urgency_level}>"
