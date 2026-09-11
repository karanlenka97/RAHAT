"""Patient database model."""
import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.models.base import Base, GUID, UniversalJSON, TimestampMixin


class Patient(Base, TimestampMixin):
    """Patient demographic and basic clinical index."""

    __tablename__ = "patients"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    abha_id = Column(String(50), unique=True, index=True, nullable=True)  # Synthetic ABHA reference
    anonymous_patient_code = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(150), nullable=False, index=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=False)  # MALE, FEMALE, OTHER
    blood_group = Column(String(10), nullable=True)
    phone = Column(String(20), index=True, nullable=True)
    emergency_contact_name = Column(String(150), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)

    village_id = Column(
        GUID,
        ForeignKey("villages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    address_line = Column(String(255), nullable=True)
    chronic_conditions = Column(UniversalJSON, nullable=True, default=list)
    allergies = Column(UniversalJSON, nullable=True, default=list)
    abha_address = Column(String(100), nullable=True)

    # Relationships
    village = relationship("Village", back_populates="patients", lazy="joined")
    care_requests = relationship(
        "CareRequest",
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    referrals = relationship(
        "Referral",
        back_populates="patient",
        cascade="all, delete-orphan",
    )

    @property
    def patient_code(self) -> str:
        """Alias for system-generated patient code."""
        return self.anonymous_patient_code

    @patient_code.setter
    def patient_code(self, value: str):
        self.anonymous_patient_code = value

    @property
    def abha_reference(self) -> str | None:
        """Alias for abha_id."""
        return self.abha_id

    @abha_reference.setter
    def abha_reference(self, value: str | None):
        self.abha_id = value

    @property
    def address(self) -> str | None:
        """Alias for address_line."""
        return self.address_line

    @address.setter
    def address(self, value: str | None):
        self.address_line = value

    @property
    def emergency_contact(self) -> str | None:
        """Combined emergency contact summary."""
        parts = [p for p in [self.emergency_contact_name, self.emergency_contact_phone] if p]
        return " - ".join(parts) if parts else None

    __table_args__ = (
        Index("idx_patients_village_gender", "village_id", "gender"),
        Index("idx_patients_name_phone", "full_name", "phone"),
    )

    def __repr__(self) -> str:
        return f"<Patient code={self.anonymous_patient_code} name={self.full_name}>"
