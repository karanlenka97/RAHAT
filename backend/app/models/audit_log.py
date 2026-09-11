"""AuditLog database model."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import relationship
from app.models.base import Base, GUID, UniversalJSON


class AuditLog(Base):
    """Immutable audit trail for compliance, patient safety, and operational traceability."""

    __tablename__ = "audit_logs"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(
        GUID,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    action = Column(String(100), nullable=False, index=True)  # LOGIN, CARE_REQUEST_CREATED, REFERRAL_ACCEPTED, etc.
    entity_type = Column(String(100), nullable=False, index=True)  # User, Patient, Referral, Facility
    entity_id = Column(String(100), nullable=True, index=True)
    details = Column(UniversalJSON, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)

    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("idx_audit_entity_action", "entity_type", "action", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog action={self.action} entity={self.entity_type} user_id={self.user_id}>"
