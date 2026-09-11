"""User database model."""
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.models.base import Base, GUID, TimestampMixin


class User(Base, TimestampMixin):
    """User account entity for healthcare workers, administrators, and coordinators."""

    __tablename__ = "users"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    role_id = Column(GUID, ForeignKey("roles.id", ondelete="SET NULL"), nullable=True, index=True)
    facility_id = Column(GUID, ForeignKey("facilities.id", ondelete="SET NULL"), nullable=True, index=True)

    email = Column(String(255), unique=True, index=True, nullable=True)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    role = relationship("Role", back_populates="users")
    facility = relationship("Facility", back_populates="users")
    healthcare_profile = relationship(
        "HealthcareProfessional",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    care_requests_created = relationship(
        "CareRequest",
        back_populates="created_by_user",
        foreign_keys="CareRequest.created_by_user_id",
    )
    referrals_managed = relationship(
        "Referral",
        back_populates="referred_by_user",
        foreign_keys="Referral.referred_by_user_id",
    )
    audit_logs = relationship("AuditLog", back_populates="user")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_users_active_role", "is_active", "role_id"),
    )

    def __repr__(self) -> str:
        return f"<User phone={self.phone} name={self.full_name}>"
