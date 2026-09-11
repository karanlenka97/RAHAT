"""Referral Lifecycle and Tracking API Endpoints."""
import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.user import User
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
)
from app.services.referral_service import ReferralService


router = APIRouter()

# Healthcare roles permitted for referral management
ALL_HEALTHCARE_ROLES = [
    "ADMIN",
    "DISTRICT_ADMIN",
    "FACILITY_ADMIN",
    "DOCTOR",
    "MEDICAL_OFFICER",
    "CHO",
    "ANM",
    "ASHA",
]


@router.post(
    "",
    response_model=ReferralResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Referral from a Care Request and Facility",
)
def create_referral(
    ref_in: ReferralCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = require_roles(*ALL_HEALTHCARE_ROLES),
) -> ReferralResponse:
    """Create a new referral from an existing Care Request and target Receiving Facility."""
    client_ip = request.client.host if request.client else None
    return ReferralService.create_referral(
        db=db,
        ref_in=ref_in,
        current_user=current_user,
        client_ip=client_ip,
    )


@router.get(
    "",
    response_model=ReferralListResponse,
    summary="List Referrals with filtering and pagination",
)
def list_referrals(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by referral status"),
    receiving_facility_id: Optional[uuid.UUID] = Query(None, description="Filter by receiving facility UUID"),
    origin_facility_id: Optional[uuid.UUID] = Query(None, description="Filter by origin facility UUID"),
    urgency: Optional[str] = Query(None, description="Filter by urgency level (EMERGENCY, HIGH, MEDIUM, LOW)"),
    search: Optional[str] = Query(None, description="Search referral code or patient name/phone"),
    db: Session = Depends(get_db),
    current_user: User = require_roles(*ALL_HEALTHCARE_ROLES),
) -> ReferralListResponse:
    """List referrals with multi-criteria filtering and pagination."""
    return ReferralService.list_referrals(
        db=db,
        current_user=current_user,
        page=page,
        page_size=page_size,
        status_filter=status,
        receiving_facility_id=receiving_facility_id,
        origin_facility_id=origin_facility_id,
        urgency=urgency,
        search=search,
    )


@router.get(
    "/{id}",
    response_model=ReferralResponse,
    summary="Get single referral detail by ID",
)
def get_referral(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = require_roles(*ALL_HEALTHCARE_ROLES),
) -> ReferralResponse:
    """Retrieve complete referral details including patient, care request, and timeline events."""
    return ReferralService.get_referral_by_id(
        db=db,
        referral_id=id,
        current_user=current_user,
    )


@router.get(
    "/{id}/events",
    response_model=List[ReferralEventResponse],
    summary="Get chronological timeline of referral lifecycle events",
)
def get_referral_events(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = require_roles(*ALL_HEALTHCARE_ROLES),
) -> List[ReferralEventResponse]:
    """Retrieve chronological immutable timeline events for the referral."""
    return ReferralService.get_referral_events(
        db=db,
        referral_id=id,
        current_user=current_user,
    )


@router.post(
    "/{id}/accept",
    response_model=ReferralResponse,
    summary="Receiving facility accepts referral",
)
def accept_referral(
    id: uuid.UUID,
    accept_in: ReferralAcceptInput,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = require_roles(*ALL_HEALTHCARE_ROLES),
) -> ReferralResponse:
    """Accept incoming referral. Restricted to receiving facility staff or admins."""
    client_ip = request.client.host if request.client else None
    return ReferralService.accept_referral(
        db=db,
        referral_id=id,
        accept_in=accept_in,
        current_user=current_user,
        client_ip=client_ip,
    )


@router.post(
    "/{id}/reject",
    response_model=ReferralResponse,
    summary="Receiving facility rejects referral with structured reason",
)
def reject_referral(
    id: uuid.UUID,
    reject_in: ReferralRejectInput,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = require_roles(*ALL_HEALTHCARE_ROLES),
) -> ReferralResponse:
    """Reject incoming referral with structured reason. Restricted to receiving facility staff or admins."""
    client_ip = request.client.host if request.client else None
    return ReferralService.reject_referral(
        db=db,
        referral_id=id,
        reject_in=reject_in,
        current_user=current_user,
        client_ip=client_ip,
    )


@router.post(
    "/{id}/notify-patient",
    response_model=ReferralResponse,
    summary="Mark patient as notified of accepted referral",
)
def notify_patient(
    id: uuid.UUID,
    notify_in: ReferralNotifyInput,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = require_roles(*ALL_HEALTHCARE_ROLES),
) -> ReferralResponse:
    """Record patient notification and briefing regarding accepted destination facility."""
    client_ip = request.client.host if request.client else None
    return ReferralService.notify_patient(
        db=db,
        referral_id=id,
        notify_in=notify_in,
        current_user=current_user,
        client_ip=client_ip,
    )


@router.post(
    "/{id}/depart",
    response_model=ReferralResponse,
    summary="Record patient departure toward receiving facility",
)
def depart_patient(
    id: uuid.UUID,
    depart_in: ReferralDepartInput,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = require_roles(*ALL_HEALTHCARE_ROLES),
) -> ReferralResponse:
    """Mark patient as departed and in-transit."""
    client_ip = request.client.host if request.client else None
    return ReferralService.depart_patient(
        db=db,
        referral_id=id,
        depart_in=depart_in,
        current_user=current_user,
        client_ip=client_ip,
    )


@router.post(
    "/{id}/arrive",
    response_model=ReferralResponse,
    summary="Record patient arrival at receiving facility",
)
def arrive_patient(
    id: uuid.UUID,
    arrive_in: ReferralArriveInput,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = require_roles(*ALL_HEALTHCARE_ROLES),
) -> ReferralResponse:
    """Mark patient arrival at receiving facility. Restricted to receiving facility staff or admins."""
    client_ip = request.client.host if request.client else None
    return ReferralService.arrive_patient(
        db=db,
        referral_id=id,
        arrive_in=arrive_in,
        current_user=current_user,
        client_ip=client_ip,
    )


@router.post(
    "/{id}/start-service",
    response_model=ReferralResponse,
    summary="Mark clinical service as started",
)
def start_service(
    id: uuid.UUID,
    service_in: ReferralStartServiceInput,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = require_roles(*ALL_HEALTHCARE_ROLES),
) -> ReferralResponse:
    """Mark clinical consultation/evaluation as started at receiving facility."""
    client_ip = request.client.host if request.client else None
    return ReferralService.start_service(
        db=db,
        referral_id=id,
        service_in=service_in,
        current_user=current_user,
        client_ip=client_ip,
    )


@router.post(
    "/{id}/complete",
    response_model=ReferralResponse,
    summary="Complete clinical service and record summary",
)
def complete_service(
    id: uuid.UUID,
    complete_in: ReferralCompleteInput,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = require_roles(*ALL_HEALTHCARE_ROLES),
) -> ReferralResponse:
    """Record completion of care and discharge/treatment notes."""
    client_ip = request.client.host if request.client else None
    return ReferralService.complete_service(
        db=db,
        referral_id=id,
        complete_in=complete_in,
        current_user=current_user,
        client_ip=client_ip,
    )


@router.post(
    "/{id}/back-refer",
    response_model=ReferralResponse,
    summary="Issue back-referral instructions to primary health center",
)
def back_refer(
    id: uuid.UUID,
    back_in: ReferralBackReferInput,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = require_roles(*ALL_HEALTHCARE_ROLES),
) -> ReferralResponse:
    """Issue formal back-referral and continuity-of-care instructions to primary health post."""
    client_ip = request.client.host if request.client else None
    return ReferralService.back_refer(
        db=db,
        referral_id=id,
        back_in=back_in,
        current_user=current_user,
        client_ip=client_ip,
    )


@router.post(
    "/{id}/reroute",
    response_model=ReferralResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Reroute rejected referral to new facility",
)
def reroute_referral(
    id: uuid.UUID,
    reroute_in: ReferralRerouteInput,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = require_roles(*ALL_HEALTHCARE_ROLES),
) -> ReferralResponse:
    """Reroute rejected referral to alternative facility, creating linked child referral."""
    client_ip = request.client.host if request.client else None
    return ReferralService.reroute_referral(
        db=db,
        referral_id=id,
        reroute_in=reroute_in,
        current_user=current_user,
        client_ip=client_ip,
    )
