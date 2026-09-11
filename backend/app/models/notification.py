"""Notification database model."""
import uuid
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.models.base import Base, GUID, TimestampMixin


class Notification(Base, TimestampMixin):
    """User targeted alerts and critical care workflow notifications."""

    __tablename__ = "notifications"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(
        GUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False, index=True)  # REFERRAL_INCOMING, BED_SHORTAGE, CRITICAL_ALERT
    priority = Column(String(30), default="NORMAL", nullable=False, index=True)  # EMERGENCY, HIGH, NORMAL, LOW

    reference_entity_type = Column(String(50), nullable=True)  # Referral, CareRequest, Facility
    reference_entity_id = Column(GUID, nullable=True, index=True)

    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="notifications")

    __table_args__ = (
        Index("idx_user_unread_notifications", "user_id", "is_read", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Notification title={self.title} user_id={self.user_id} read={self.is_read}>"
