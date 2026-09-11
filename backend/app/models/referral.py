"""Referral, ReferralEvent, and FollowUp database models."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    Index,
    func,
)
from sqlalchemy.orm import relationship
from app.models.base import Base, GUID, UniversalJSON, TimestampMixin


class Referral(Base, TimestampMixin):
    """Inter-facility emergency and elective patient referral workflow entity."""

    __tablename__ = "referrals"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    referral_code = Column(String(50), unique=True, index=True, nullable=False)

    care_request_id = Column(
        GUID,
        ForeignKey("care_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    patient_id = Column(
        GUID,
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    origin_facility_id = Column(
        GUID,
        ForeignKey("facilities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    destination_facility_id = Column(
        GUID,
        ForeignKey("facilities.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    referred_by_user_id = Column(
        GUID,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    parent_referral_id = Column(
        GUID,
        ForeignKey("referrals.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    priority = Column(String(30), default="MEDIUM", nullable=False, index=True)  # EMERGENCY, HIGH, MEDIUM, LOW
    required_specialty = Column(String(100), nullable=True, index=True)
    required_capability = Column(String(100), nullable=True)
    clinical_summary = Column(Text, nullable=False)

    transport_mode = Column(String(50), nullable=True)  # 108_AMBULANCE, 102_AMBULANCE, PRIVATE_VEHICLE, PUBLIC_TRANSPORT, OTHER
    transport_status = Column(String(50), default="PENDING", nullable=False)
    status = Column(String(50), default="PENDING_ACCEPTANCE", nullable=False, index=True)
    # Lifecycle: CREATED, PENDING_ACCEPTANCE, ACCEPTED, REJECTED, PATIENT_NOTIFIED, DEPARTED, ARRIVED, IN_SERVICE, COMPLETED, BACK_REFERRED, FOLLOW_UP, CLOSED, REROUTED, CANCELLED

    estimated_transit_minutes = Column(Integer, nullable=True)
    expected_arrival_time = Column(DateTime(timezone=True), nullable=True)

    rejection_reason = Column(String(100), nullable=True)  # SERVICE_UNAVAILABLE, CAPACITY_UNAVAILABLE, SPECIALIST_UNAVAILABLE, FACILITY_CLOSED, OTHER
    rejection_notes = Column(Text, nullable=True)
    back_referral_notes = Column(Text, nullable=True)

    initiated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    notified_at = Column(DateTime(timezone=True), nullable=True)
    departed_at = Column(DateTime(timezone=True), nullable=True)
    arrived_at = Column(DateTime(timezone=True), nullable=True)
    in_service_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    back_referred_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    care_request = relationship("CareRequest", back_populates="referral")
    patient = relationship("Patient", back_populates="referrals")
    origin_facility = relationship(
        "Facility",
        foreign_keys=[origin_facility_id],
        back_populates="referrals_origin",
    )
    destination_facility = relationship(
        "Facility",
        foreign_keys=[destination_facility_id],
        back_populates="referrals_destination",
    )
    referred_by_user = relationship(
        "User",
        foreign_keys=[referred_by_user_id],
        back_populates="referrals_managed",
    )
    parent_referral = relationship(
        "Referral",
        remote_side=[id],
        backref="child_referrals",
        foreign_keys=[parent_referral_id],
    )
    events = relationship(
        "ReferralEvent",
        back_populates="referral",
        cascade="all, delete-orphan",
        order_by="ReferralEvent.event_timestamp.asc()",
    )
    follow_ups = relationship(
        "FollowUp",
        back_populates="referral",
        cascade="all, delete-orphan",
    )

    # Property Aliases for Specification Conformity
    @property
    def source_facility_id(self):
        return self.origin_facility_id

    @source_facility_id.setter
    def source_facility_id(self, value):
        self.origin_facility_id = value

    @property
    def receiving_facility_id(self):
        return self.destination_facility_id

    @receiving_facility_id.setter
    def receiving_facility_id(self, value):
        self.destination_facility_id = value

    @property
    def source_facility(self):
        return self.origin_facility

    @property
    def receiving_facility(self):
        return self.destination_facility

    @property
    def created_by(self):
        return self.referred_by_user_id

    @created_by.setter
    def created_by(self, value):
        self.referred_by_user_id = value

    @property
    def urgency(self):
        return self.priority

    @urgency.setter
    def urgency(self, value):
        self.priority = value

    @property
    def referral_reason(self):
        return self.clinical_summary

    @referral_reason.setter
    def referral_reason(self, value):
        self.clinical_summary = value

    __table_args__ = (
        Index("idx_referral_status_priority", "status", "priority"),
        Index("idx_referral_facilities", "origin_facility_id", "destination_facility_id"),
        Index("idx_referral_care_request", "care_request_id"),
        Index("idx_referral_parent", "parent_referral_id"),
    )

    def __repr__(self) -> str:
        return f"<Referral code={self.referral_code} status={self.status} priority={self.priority}>"


class ReferralEvent(Base):
    """Immutable timestamped event tracking log for referral state transitions."""

    __tablename__ = "referral_events"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    referral_id = Column(
        GUID,
        ForeignKey("referrals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type = Column(String(100), nullable=False, index=True)
    from_status = Column(String(50), nullable=True)
    to_status = Column(String(50), nullable=False)
    triggered_by_user_id = Column(
        GUID,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    comments = Column(Text, nullable=True)
    event_metadata = Column(UniversalJSON, nullable=True)
    event_timestamp = Column(
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
    referral = relationship("Referral", back_populates="events")
    triggered_by_user = relationship("User")

    # Property Aliases
    @property
    def previous_status(self):
        return self.from_status

    @previous_status.setter
    def previous_status(self, value):
        self.from_status = value

    @property
    def new_status(self):
        return self.to_status

    @new_status.setter
    def new_status(self, value):
        self.to_status = value

    @property
    def performed_by(self):
        return self.triggered_by_user_id

    @performed_by.setter
    def performed_by(self, value):
        self.triggered_by_user_id = value

    @property
    def notes(self):
        return self.comments

    @notes.setter
    def notes(self, value):
        self.comments = value

    def __repr__(self) -> str:
        return f"<ReferralEvent type={self.event_type} to_status={self.to_status}>"


class FollowUp(Base, TimestampMixin):
    """Post-discharge / post-treatment follow-up and monitoring for patients."""

    __tablename__ = "follow_ups"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    referral_id = Column(
        GUID,
        ForeignKey("referrals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    patient_id = Column(
        GUID,
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assigned_worker_id = Column(
        GUID,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    followup_number = Column(Integer, default=1, nullable=False)
    scheduled_date = Column(DateTime(timezone=True), nullable=False, index=True)
    completed_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="SCHEDULED", nullable=False, index=True)  # SCHEDULED, COMPLETED, MISSED, CANCELLED
    clinical_notes = Column(Text, nullable=True)
    recovery_status = Column(String(50), nullable=True)  # RECOVERED, IMPROVING, STABLE, DETERIORATING
    patient_vitals = Column(UniversalJSON, nullable=True)

    # Relationships
    referral = relationship("Referral", back_populates="follow_ups")
    patient = relationship("Patient")
    assigned_worker = relationship("User")

    __table_args__ = (
        Index("idx_followup_status_date", "status", "scheduled_date"),
    )

    def __repr__(self) -> str:
        return f"<FollowUp referral={self.referral_id} status={self.status}>"
