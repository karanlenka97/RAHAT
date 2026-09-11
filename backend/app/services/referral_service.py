"""Referral Management and State Machine Service Layer."""
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Set, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.models.referral import Referral, ReferralEvent
from app.models.care_request import CareRequest
from app.models.patient import Patient
from app.models.facility import Facility, FacilityCapability
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.referral import (
    ReferralCreate,
    ReferralAcceptInput,
    ReferralRejectInput,
    ReferralNotifyInput,
    ReferralDepartInput,
    ReferralArriveInput,
    ReferralStartServiceInput,
    ReferralCompleteInput,
    ReferralBackReferInput,
    ReferralRerouteInput,
    ReferralEventResponse,
    ReferralResponse,
    ReferralListResponse,
    RejectionReason,
)


VALID_TRANSITIONS: Dict[str, Set[str]] = {
    "CREATED": {"PENDING_ACCEPTANCE", "CANCELLED"},
    "PENDING_ACCEPTANCE": {"ACCEPTED", "REJECTED", "CANCELLED"},
    "ACCEPTED": {"PATIENT_NOTIFIED", "DEPARTED", "CANCELLED"},
    "PATIENT_NOTIFIED": {"DEPARTED", "CANCELLED"},
    "DEPARTED": {"ARRIVED", "CANCELLED"},
    "ARRIVED": {"IN_SERVICE", "CANCELLED"},
    "IN_SERVICE": {"COMPLETED"},
    "COMPLETED": {"BACK_REFERRED", "FOLLOW_UP", "CLOSED"},
    "BACK_REFERRED": {"FOLLOW_UP", "CLOSED"},
    "FOLLOW_UP": {"CLOSED"},
    "REJECTED": {"REROUTED"},
    "REROUTED": {"PENDING_ACCEPTANCE"},
    "CLOSED": set(),
    "CANCELLED": set(),
}


class ReferralService:
    """Handles business logic, validation, state transitions, and audit logs for Referrals."""

    @staticmethod
    def generate_referral_code(db: Session) -> str:
        """Generate a unique human-readable referral identifier (e.g. REF-RAHAT-000001)."""
        count = db.query(func.count(Referral.id)).scalar() or 0
        seq = count + 1
        while True:
            code = f"REF-RAHAT-{seq:06d}"
            exists = db.query(Referral.id).filter(Referral.referral_code == code).first()
            if not exists:
                return code
            seq += 1

    @classmethod
    def _validate_transition(cls, current_status: str, target_status: str) -> None:
        """Validate if transition between current_status and target_status is permitted."""
        allowed = VALID_TRANSITIONS.get(current_status, set())
        if target_status not in allowed:
            allowed_str = ", ".join(sorted(list(allowed))) if allowed else "None (Terminal State)"
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid referral state transition from '{current_status}' to '{target_status}'. "
                    f"Permitted next states from '{current_status}': [{allowed_str}]."
                ),
            )

    @classmethod
    def _format_event_response(cls, event: ReferralEvent) -> ReferralEventResponse:
        """Convert a ReferralEvent database model to a response schema."""
        performer_name = None
        performer_role = None
        if event.triggered_by_user:
            performer_name = event.triggered_by_user.full_name
            if event.triggered_by_user.role:
                performer_role = event.triggered_by_user.role.name

        return ReferralEventResponse(
            id=event.id,
            referral_id=event.referral_id,
            event_type=event.event_type,
            previous_status=event.from_status,
            new_status=event.to_status,
            performed_by=event.triggered_by_user_id,
            performer_name=performer_name,
            performer_role=performer_role,
            notes=event.comments,
            event_metadata=event.event_metadata,
            created_at=event.event_timestamp or event.created_at,
        )

    @classmethod
    def _format_referral_response(
        cls, referral: Referral, include_events: bool = True
    ) -> ReferralResponse:
        """Convert a Referral database model to a comprehensive response schema."""
        # Patient details
        patient_name = None
        patient_code = None
        patient_age = None
        patient_gender = None
        patient_phone = None
        patient_village = None
        if referral.patient:
            patient_name = referral.patient.full_name
            patient_code = referral.patient.anonymous_patient_code
            patient_age = referral.patient.age
            patient_gender = referral.patient.gender
            patient_phone = referral.patient.phone
            if referral.patient.village:
                patient_village = f"{referral.patient.village.name}, {referral.patient.village.district}"

        # Care Request details
        care_req_number = None
        care_category = None
        required_service = None
        if referral.care_request:
            care_req_number = referral.care_request.request_number
            care_category = referral.care_request.care_category
            required_service = referral.care_request.required_service

        # Facility details
        source_fac_name = referral.origin_facility.name if referral.origin_facility else None
        receiving_fac_name = referral.destination_facility.name if referral.destination_facility else None
        receiving_fac_type = referral.destination_facility.facility_type if referral.destination_facility else None

        # Creator details
        creator_name = None
        creator_role = None
        if referral.referred_by_user:
            creator_name = referral.referred_by_user.full_name
            if referral.referred_by_user.role:
                creator_role = referral.referred_by_user.role.name

        # Events
        events_resp = None
        if include_events and referral.events:
            events_resp = [cls._format_event_response(e) for e in referral.events]

        return ReferralResponse(
            id=referral.id,
            referral_code=referral.referral_code,
            care_request_id=referral.care_request_id,
            care_request_number=care_req_number,
            care_category=care_category,
            required_service=required_service,
            patient_id=referral.patient_id,
            patient_name=patient_name,
            patient_code=patient_code,
            patient_age=patient_age,
            patient_gender=patient_gender,
            patient_phone=patient_phone,
            patient_village=patient_village,
            source_facility_id=referral.origin_facility_id,
            source_facility_name=source_fac_name,
            receiving_facility_id=referral.destination_facility_id,
            receiving_facility_name=receiving_fac_name,
            receiving_facility_type=receiving_fac_type,
            created_by=referral.referred_by_user_id,
            creator_name=creator_name,
            creator_role=creator_role,
            parent_referral_id=referral.parent_referral_id,
            status=referral.status,
            urgency=referral.priority,
            referral_reason=referral.clinical_summary,
            clinical_summary=referral.clinical_summary,
            required_specialty=referral.required_specialty,
            transport_mode=referral.transport_mode,
            transport_status=referral.transport_status,
            estimated_transit_minutes=referral.estimated_transit_minutes,
            expected_arrival_time=referral.expected_arrival_time,
            rejection_reason=referral.rejection_reason,
            rejection_notes=referral.rejection_notes,
            back_referral_notes=referral.back_referral_notes,
            initiated_at=referral.initiated_at or referral.created_at,
            accepted_at=referral.accepted_at,
            notified_at=referral.notified_at,
            departed_at=referral.departed_at,
            arrived_at=referral.arrived_at,
            in_service_at=referral.in_service_at,
            completed_at=referral.completed_at,
            back_referred_at=referral.back_referred_at,
            closed_at=referral.closed_at,
            created_at=referral.created_at,
            updated_at=referral.updated_at,
            events=events_resp,
        )

    @classmethod
    def create_referral(
        cls,
        db: Session,
        ref_in: ReferralCreate,
        current_user: User,
        client_ip: Optional[str] = None,
    ) -> ReferralResponse:
        """Create a new referral connecting a Care Request with a validated receiving facility."""
        care_request = db.query(CareRequest).filter(CareRequest.id == ref_in.care_request_id).first()
        if not care_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Care Request with ID {ref_in.care_request_id} does not exist.",
            )

        patient = db.query(Patient).filter(Patient.id == care_request.patient_id).first()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient associated with Care Request does not exist.",
            )

        receiving_facility = db.query(Facility).filter(Facility.id == ref_in.receiving_facility_id).first()
        if not receiving_facility:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Receiving Facility with ID {ref_in.receiving_facility_id} does not exist.",
            )

        if not receiving_facility.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Receiving facility '{receiving_facility.name}' is currently marked inactive and cannot accept new referrals.",
            )

        # Validate receiving facility capability
        has_capability = db.query(FacilityCapability).filter(
            FacilityCapability.facility_id == receiving_facility.id,
            FacilityCapability.available == True,
            FacilityCapability.availability_status != "UNAVAILABLE",
        ).first()

        if not has_capability and receiving_facility.tier_level < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Facility '{receiving_facility.name}' does not have active operational capabilities for this referral.",
            )

        referral_code = cls.generate_referral_code(db)
        urgency_val = (ref_in.urgency or care_request.urgency_level or "MEDIUM").upper()
        clinical_notes = ref_in.clinical_summary or ref_in.referral_reason or care_request.chief_complaint or "Referral initiated."

        source_fac_id = ref_in.source_facility_id or care_request.origin_facility_id

        referral = Referral(
            id=uuid.uuid4(),
            referral_code=referral_code,
            care_request_id=care_request.id,
            patient_id=patient.id,
            origin_facility_id=source_fac_id,
            destination_facility_id=receiving_facility.id,
            referred_by_user_id=current_user.id,
            priority=urgency_val,
            required_specialty=ref_in.required_specialty or care_request.care_category,
            required_capability=ref_in.required_capability or care_request.required_service,
            clinical_summary=clinical_notes,
            transport_mode=ref_in.transport_mode,
            transport_status="PENDING",
            status="PENDING_ACCEPTANCE",
            expected_arrival_time=ref_in.expected_arrival_time,
        )

        db.add(referral)
        db.flush()

        # Create Initial Referral Event
        init_event = ReferralEvent(
            id=uuid.uuid4(),
            referral_id=referral.id,
            event_type="REFERRAL_CREATED",
            from_status="CREATED",
            to_status="PENDING_ACCEPTANCE",
            triggered_by_user_id=current_user.id,
            comments=f"Referral created and queued for facility acceptance at {receiving_facility.name}.",
            event_metadata={
                "care_request_number": care_request.request_number,
                "urgency": urgency_val,
                "receiving_facility": receiving_facility.name,
            },
        )
        db.add(init_event)

        # Update Care Request status to REFERRED
        care_request.status = "REFERRED"

        # Create AuditLog
        audit = AuditLog(
            user_id=current_user.id,
            action="REFERRAL_CREATED",
            entity_type="Referral",
            entity_id=str(referral.id),
            details={
                "referral_code": referral.referral_code,
                "care_request_id": str(care_request.id),
                "patient_id": str(patient.id),
                "destination_facility_id": str(receiving_facility.id),
                "urgency": urgency_val,
            },
            ip_address=client_ip,
        )
        db.add(audit)

        db.commit()
        db.refresh(referral)
        return cls._format_referral_response(referral)

    @classmethod
    def _verify_receiving_facility_auth(cls, referral: Referral, current_user: User) -> None:
        """Ensure user is authorized at receiving facility or is an administrator."""
        user_role = current_user.role.name if current_user.role else "USER"
        if user_role in ["ADMIN", "DISTRICT_ADMIN"]:
            return

        if current_user.facility_id and current_user.facility_id != referral.destination_facility_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Only authorized staff assigned to the receiving facility can perform this action.",
            )

    @classmethod
    def accept_referral(
        cls,
        db: Session,
        referral_id: uuid.UUID,
        accept_in: ReferralAcceptInput,
        current_user: User,
        client_ip: Optional[str] = None,
    ) -> ReferralResponse:
        """Receiving facility accepts the inbound referral."""
        referral = db.query(Referral).filter(Referral.id == referral_id).first()
        if not referral:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Referral with ID {referral_id} not found.",
            )

        cls._verify_receiving_facility_auth(referral, current_user)
        cls._validate_transition(referral.status, "ACCEPTED")

        now = datetime.now(timezone.utc)
        prev_status = referral.status
        referral.status = "ACCEPTED"
        referral.accepted_at = now
        if accept_in.expected_arrival_time:
            referral.expected_arrival_time = accept_in.expected_arrival_time

        event = ReferralEvent(
            id=uuid.uuid4(),
            referral_id=referral.id,
            event_type="FACILITY_ACCEPTED",
            from_status=prev_status,
            to_status="ACCEPTED",
            triggered_by_user_id=current_user.id,
            comments=accept_in.notes or "Referral accepted by receiving facility.",
        )
        db.add(event)

        audit = AuditLog(
            user_id=current_user.id,
            action="REFERRAL_ACCEPTED",
            entity_type="Referral",
            entity_id=str(referral.id),
            details={"referral_code": referral.referral_code, "notes": accept_in.notes},
            ip_address=client_ip,
        )
        db.add(audit)

        db.commit()
        db.refresh(referral)
        return cls._format_referral_response(referral)

    @classmethod
    def reject_referral(
        cls,
        db: Session,
        referral_id: uuid.UUID,
        reject_in: ReferralRejectInput,
        current_user: User,
        client_ip: Optional[str] = None,
    ) -> ReferralResponse:
        """Receiving facility rejects the inbound referral with a structured reason."""
        referral = db.query(Referral).filter(Referral.id == referral_id).first()
        if not referral:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Referral with ID {referral_id} not found.",
            )

        cls._verify_receiving_facility_auth(referral, current_user)
        cls._validate_transition(referral.status, "REJECTED")

        # Validate controlled reason
        valid_reasons = {r.value for r in RejectionReason}
        reason_str = reject_in.rejection_reason.strip().upper()
        if reason_str not in valid_reasons:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid rejection reason '{reject_in.rejection_reason}'. Permitted values: {sorted(list(valid_reasons))}",
            )

        prev_status = referral.status
        referral.status = "REJECTED"
        referral.rejection_reason = reason_str
        referral.rejection_notes = reject_in.rejection_notes

        event = ReferralEvent(
            id=uuid.uuid4(),
            referral_id=referral.id,
            event_type="FACILITY_REJECTED",
            from_status=prev_status,
            to_status="REJECTED",
            triggered_by_user_id=current_user.id,
            comments=f"Rejected: {reason_str}. Notes: {reject_in.rejection_notes or 'None'}",
            event_metadata={"reason": reason_str, "notes": reject_in.rejection_notes},
        )
        db.add(event)

        audit = AuditLog(
            user_id=current_user.id,
            action="REFERRAL_REJECTED",
            entity_type="Referral",
            entity_id=str(referral.id),
            details={"referral_code": referral.referral_code, "reason": reason_str, "notes": reject_in.rejection_notes},
            ip_address=client_ip,
        )
        db.add(audit)

        db.commit()
        db.refresh(referral)
        return cls._format_referral_response(referral)

    @classmethod
    def notify_patient(
        cls,
        db: Session,
        referral_id: uuid.UUID,
        notify_in: ReferralNotifyInput,
        current_user: User,
        client_ip: Optional[str] = None,
    ) -> ReferralResponse:
        """Mark patient as briefed and notified about the referral arrangement."""
        referral = db.query(Referral).filter(Referral.id == referral_id).first()
        if not referral:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Referral with ID {referral_id} not found.",
            )

        cls._validate_transition(referral.status, "PATIENT_NOTIFIED")

        now = datetime.now(timezone.utc)
        prev_status = referral.status
        referral.status = "PATIENT_NOTIFIED"
        referral.notified_at = now

        event = ReferralEvent(
            id=uuid.uuid4(),
            referral_id=referral.id,
            event_type="PATIENT_NOTIFIED",
            from_status=prev_status,
            to_status="PATIENT_NOTIFIED",
            triggered_by_user_id=current_user.id,
            comments=notify_in.notes or "Patient / family notified of referral destination.",
        )
        db.add(event)

        audit = AuditLog(
            user_id=current_user.id,
            action="PATIENT_NOTIFIED",
            entity_type="Referral",
            entity_id=str(referral.id),
            details={"referral_code": referral.referral_code, "notes": notify_in.notes},
            ip_address=client_ip,
        )
        db.add(audit)

        db.commit()
        db.refresh(referral)
        return cls._format_referral_response(referral)

    @classmethod
    def depart_patient(
        cls,
        db: Session,
        referral_id: uuid.UUID,
        depart_in: ReferralDepartInput,
        current_user: User,
        client_ip: Optional[str] = None,
    ) -> ReferralResponse:
        """Record patient departure in transit toward the receiving facility."""
        referral = db.query(Referral).filter(Referral.id == referral_id).first()
        if not referral:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Referral with ID {referral_id} not found.",
            )

        cls._validate_transition(referral.status, "DEPARTED")

        now = datetime.now(timezone.utc)
        prev_status = referral.status
        referral.status = "DEPARTED"
        referral.departed_at = now
        referral.transport_status = "IN_TRANSIT"
        if depart_in.transport_mode:
            referral.transport_mode = depart_in.transport_mode
        if depart_in.estimated_transit_minutes:
            referral.estimated_transit_minutes = depart_in.estimated_transit_minutes

        event = ReferralEvent(
            id=uuid.uuid4(),
            referral_id=referral.id,
            event_type="PATIENT_DEPARTED",
            from_status=prev_status,
            to_status="DEPARTED",
            triggered_by_user_id=current_user.id,
            comments=depart_in.notes or f"Patient departed via {referral.transport_mode or 'transport'}.",
            event_metadata={
                "transport_mode": referral.transport_mode,
                "estimated_transit_minutes": referral.estimated_transit_minutes,
            },
        )
        db.add(event)

        audit = AuditLog(
            user_id=current_user.id,
            action="PATIENT_DEPARTED",
            entity_type="Referral",
            entity_id=str(referral.id),
            details={"referral_code": referral.referral_code, "transport_mode": referral.transport_mode},
            ip_address=client_ip,
        )
        db.add(audit)

        db.commit()
        db.refresh(referral)
        return cls._format_referral_response(referral)

    @classmethod
    def arrive_patient(
        cls,
        db: Session,
        referral_id: uuid.UUID,
        arrive_in: ReferralArriveInput,
        current_user: User,
        client_ip: Optional[str] = None,
    ) -> ReferralResponse:
        """Receiving facility records patient arrival at the facility."""
        referral = db.query(Referral).filter(Referral.id == referral_id).first()
        if not referral:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Referral with ID {referral_id} not found.",
            )

        cls._verify_receiving_facility_auth(referral, current_user)
        cls._validate_transition(referral.status, "ARRIVED")

        now = datetime.now(timezone.utc)
        prev_status = referral.status
        referral.status = "ARRIVED"
        referral.arrived_at = now
        referral.transport_status = "ARRIVED"

        event = ReferralEvent(
            id=uuid.uuid4(),
            referral_id=referral.id,
            event_type="PATIENT_ARRIVED",
            from_status=prev_status,
            to_status="ARRIVED",
            triggered_by_user_id=current_user.id,
            comments=arrive_in.notes or "Patient arrived at receiving facility.",
        )
        db.add(event)

        audit = AuditLog(
            user_id=current_user.id,
            action="PATIENT_ARRIVED",
            entity_type="Referral",
            entity_id=str(referral.id),
            details={"referral_code": referral.referral_code, "notes": arrive_in.notes},
            ip_address=client_ip,
        )
        db.add(audit)

        db.commit()
        db.refresh(referral)
        return cls._format_referral_response(referral)

    @classmethod
    def start_service(
        cls,
        db: Session,
        referral_id: uuid.UUID,
        service_in: ReferralStartServiceInput,
        current_user: User,
        client_ip: Optional[str] = None,
    ) -> ReferralResponse:
        """Mark clinical service / consultation as in-progress at the facility."""
        referral = db.query(Referral).filter(Referral.id == referral_id).first()
        if not referral:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Referral with ID {referral_id} not found.",
            )

        cls._verify_receiving_facility_auth(referral, current_user)
        cls._validate_transition(referral.status, "IN_SERVICE")

        now = datetime.now(timezone.utc)
        prev_status = referral.status
        referral.status = "IN_SERVICE"
        referral.in_service_at = now

        event = ReferralEvent(
            id=uuid.uuid4(),
            referral_id=referral.id,
            event_type="SERVICE_STARTED",
            from_status=prev_status,
            to_status="IN_SERVICE",
            triggered_by_user_id=current_user.id,
            comments=service_in.notes or "Clinical service / evaluation initiated.",
        )
        db.add(event)

        audit = AuditLog(
            user_id=current_user.id,
            action="SERVICE_STARTED",
            entity_type="Referral",
            entity_id=str(referral.id),
            details={"referral_code": referral.referral_code, "notes": service_in.notes},
            ip_address=client_ip,
        )
        db.add(audit)

        db.commit()
        db.refresh(referral)
        return cls._format_referral_response(referral)

    @classmethod
    def complete_service(
        cls,
        db: Session,
        referral_id: uuid.UUID,
        complete_in: ReferralCompleteInput,
        current_user: User,
        client_ip: Optional[str] = None,
    ) -> ReferralResponse:
        """Complete clinical care and record discharge/treatment summary."""
        referral = db.query(Referral).filter(Referral.id == referral_id).first()
        if not referral:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Referral with ID {referral_id} not found.",
            )

        cls._verify_receiving_facility_auth(referral, current_user)
        cls._validate_transition(referral.status, "COMPLETED")

        now = datetime.now(timezone.utc)
        prev_status = referral.status
        referral.status = "COMPLETED"
        referral.completed_at = now
        if complete_in.clinical_summary:
            referral.clinical_summary = f"{referral.clinical_summary}\n\n[Completion Summary]: {complete_in.clinical_summary}"

        event = ReferralEvent(
            id=uuid.uuid4(),
            referral_id=referral.id,
            event_type="SERVICE_COMPLETED",
            from_status=prev_status,
            to_status="COMPLETED",
            triggered_by_user_id=current_user.id,
            comments=complete_in.notes or "Referral medical service completed.",
            event_metadata={"completion_summary": complete_in.clinical_summary},
        )
        db.add(event)

        audit = AuditLog(
            user_id=current_user.id,
            action="SERVICE_COMPLETED",
            entity_type="Referral",
            entity_id=str(referral.id),
            details={"referral_code": referral.referral_code, "notes": complete_in.notes},
            ip_address=client_ip,
        )
        db.add(audit)

        db.commit()
        db.refresh(referral)
        return cls._format_referral_response(referral)

    @classmethod
    def back_refer(
        cls,
        db: Session,
        referral_id: uuid.UUID,
        back_in: ReferralBackReferInput,
        current_user: User,
        client_ip: Optional[str] = None,
    ) -> ReferralResponse:
        """Issue back-referral instructions to primary health post for continuity of care."""
        referral = db.query(Referral).filter(Referral.id == referral_id).first()
        if not referral:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Referral with ID {referral_id} not found.",
            )

        cls._validate_transition(referral.status, "BACK_REFERRED")

        now = datetime.now(timezone.utc)
        prev_status = referral.status
        referral.status = "BACK_REFERRED"
        referral.back_referred_at = now
        referral.back_referral_notes = back_in.back_referral_notes

        event = ReferralEvent(
            id=uuid.uuid4(),
            referral_id=referral.id,
            event_type="BACK_REFERRED",
            from_status=prev_status,
            to_status="BACK_REFERRED",
            triggered_by_user_id=current_user.id,
            comments=back_in.notes or f"Back referral issued: {back_in.back_referral_notes[:100]}...",
            event_metadata={"back_referral_notes": back_in.back_referral_notes},
        )
        db.add(event)

        audit = AuditLog(
            user_id=current_user.id,
            action="BACK_REFERRED",
            entity_type="Referral",
            entity_id=str(referral.id),
            details={"referral_code": referral.referral_code, "notes": back_in.back_referral_notes},
            ip_address=client_ip,
        )
        db.add(audit)

        db.commit()
        db.refresh(referral)
        return cls._format_referral_response(referral)

    @classmethod
    def reroute_referral(
        cls,
        db: Session,
        referral_id: uuid.UUID,
        reroute_in: ReferralRerouteInput,
        current_user: User,
        client_ip: Optional[str] = None,
    ) -> ReferralResponse:
        """Reroute a rejected referral to a chosen new eligible facility."""
        original = db.query(Referral).filter(Referral.id == referral_id).first()
        if not original:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Referral with ID {referral_id} not found.",
            )

        cls._validate_transition(original.status, "REROUTED")

        if reroute_in.new_receiving_facility_id == original.destination_facility_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot reroute to the same facility that previously rejected this referral.",
            )

        new_facility = db.query(Facility).filter(Facility.id == reroute_in.new_receiving_facility_id).first()
        if not new_facility:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"New target facility with ID {reroute_in.new_receiving_facility_id} does not exist.",
            )

        if not new_facility.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Facility '{new_facility.name}' is inactive.",
            )

        # Transition original to REROUTED
        original_prev_status = original.status
        original.status = "REROUTED"

        orig_event = ReferralEvent(
            id=uuid.uuid4(),
            referral_id=original.id,
            event_type="REFERRAL_REROUTED",
            from_status=original_prev_status,
            to_status="REROUTED",
            triggered_by_user_id=current_user.id,
            comments=f"Rerouted to {new_facility.name}. Reason: {reroute_in.reason or 'Alternative facility chosen.'}",
            event_metadata={"new_facility_id": str(new_facility.id), "new_facility_name": new_facility.name},
        )
        db.add(orig_event)

        # Create new child referral
        new_code = cls.generate_referral_code(db)
        child_referral = Referral(
            id=uuid.uuid4(),
            referral_code=new_code,
            care_request_id=original.care_request_id,
            patient_id=original.patient_id,
            origin_facility_id=original.origin_facility_id,
            destination_facility_id=new_facility.id,
            referred_by_user_id=current_user.id,
            parent_referral_id=original.id,
            priority=original.priority,
            required_specialty=original.required_specialty,
            required_capability=original.required_capability,
            clinical_summary=f"{original.clinical_summary}\n\n[Reroute Note]: {reroute_in.notes or reroute_in.reason or 'Rerouted from ' + original.referral_code}",
            transport_mode=original.transport_mode,
            transport_status="PENDING",
            status="PENDING_ACCEPTANCE",
        )
        db.add(child_referral)
        db.flush()

        child_event = ReferralEvent(
            id=uuid.uuid4(),
            referral_id=child_referral.id,
            event_type="REFERRAL_CREATED",
            from_status="CREATED",
            to_status="PENDING_ACCEPTANCE",
            triggered_by_user_id=current_user.id,
            comments=f"Referral rerouted from {original.referral_code} to {new_facility.name}.",
            event_metadata={"parent_referral_code": original.referral_code},
        )
        db.add(child_event)

        audit = AuditLog(
            user_id=current_user.id,
            action="REFERRAL_REROUTED",
            entity_type="Referral",
            entity_id=str(original.id),
            details={
                "original_referral_code": original.referral_code,
                "new_referral_code": child_referral.referral_code,
                "new_facility_id": str(new_facility.id),
            },
            ip_address=client_ip,
        )
        db.add(audit)

        db.commit()
        db.refresh(child_referral)
        return cls._format_referral_response(child_referral)

    @classmethod
    def list_referrals(
        cls,
        db: Session,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None,
        receiving_facility_id: Optional[uuid.UUID] = None,
        origin_facility_id: Optional[uuid.UUID] = None,
        urgency: Optional[str] = None,
        search: Optional[str] = None,
    ) -> ReferralListResponse:
        """Query referrals with multi-criteria filtering and pagination."""
        query = db.query(Referral)

        if status_filter:
            query = query.filter(Referral.status == status_filter.upper())

        if receiving_facility_id:
            query = query.filter(Referral.destination_facility_id == receiving_facility_id)

        if origin_facility_id:
            query = query.filter(Referral.origin_facility_id == origin_facility_id)

        if urgency:
            query = query.filter(Referral.priority == urgency.upper())

        if search:
            s_term = f"%{search.strip()}%"
            query = query.join(Referral.patient).filter(
                or_(
                    Referral.referral_code.ilike(s_term),
                    Patient.full_name.ilike(s_term),
                    Patient.phone.ilike(s_term),
                    Patient.anonymous_patient_code.ilike(s_term),
                )
            )

        total = query.count()
        total_pages = max(1, (total + page_size - 1) // page_size)
        offset = (page - 1) * page_size

        referrals = query.order_by(Referral.created_at.desc()).offset(offset).limit(page_size).all()

        items = [cls._format_referral_response(r, include_events=False) for r in referrals]

        return ReferralListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @classmethod
    def get_referral_by_id(
        cls,
        db: Session,
        referral_id: uuid.UUID,
        current_user: User,
    ) -> ReferralResponse:
        """Get single referral details with all events."""
        referral = db.query(Referral).filter(Referral.id == referral_id).first()
        if not referral:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Referral with ID {referral_id} not found.",
            )
        return cls._format_referral_response(referral, include_events=True)

    @classmethod
    def get_referral_events(
        cls,
        db: Session,
        referral_id: uuid.UUID,
        current_user: User,
    ) -> List[ReferralEventResponse]:
        """Fetch immutable chronological timeline of referral events."""
        referral = db.query(Referral).filter(Referral.id == referral_id).first()
        if not referral:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Referral with ID {referral_id} not found.",
            )

        events = (
            db.query(ReferralEvent)
            .filter(ReferralEvent.referral_id == referral_id)
            .order_by(ReferralEvent.event_timestamp.asc())
            .all()
        )
        return [cls._format_event_response(e) for e in events]
