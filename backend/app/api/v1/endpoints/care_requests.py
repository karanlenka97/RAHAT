"""Care Request Management API endpoints."""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_roles
from app.models.user import User
from app.schemas.care_request import (
    CareRequestCreate,
    CareRequestUpdate,
    CareRequestResponse,
    CareRequestListResponse,
)
from app.services.care_request_service import CareRequestService

router = APIRouter()

# Frontline, Clinical, and Administrative roles permitted to create and triage care requests
CARE_REQUEST_ROLES = [
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
    response_model=CareRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new care request",
    description="Initiate a healthcare requirement/triage request for an existing patient.",
)
def create_care_request(
    request_in: CareRequestCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = require_roles(*CARE_REQUEST_ROLES),
) -> CareRequestResponse:
    """Create a care request bound to the authenticated user and specified patient."""
    client_ip = request.client.host if request.client else None
    return CareRequestService.create_care_request(
        db=db,
        request_in=request_in,
        current_user=current_user,
        client_ip=client_ip,
    )


@router.get(
    "",
    response_model=CareRequestListResponse,
    summary="List care requests",
    description="Retrieve a paginated list of care requests with filters for patient, urgency, category, and service.",
)
def list_care_requests(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    patient_id: Optional[uuid.UUID] = Query(None, description="Filter by Patient UUID"),
    urgency: Optional[str] = Query(None, description="Filter by urgency level (LOW, MEDIUM, HIGH, EMERGENCY)"),
    care_category: Optional[str] = Query(None, description="Filter by care category"),
    required_service: Optional[str] = Query(None, description="Filter by required service name"),
    search: Optional[str] = Query(None, description="Search term for complaint, patient name, or code"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CareRequestListResponse:
    """List care requests accessible to the authenticated user."""
    return CareRequestService.list_care_requests(
        db=db,
        page=page,
        page_size=page_size,
        patient_id=patient_id,
        urgency=urgency,
        care_category=care_category,
        required_service=required_service,
        search=search,
    )


@router.get(
    "/{id}",
    response_model=CareRequestResponse,
    summary="Get care request by ID",
    description="Retrieve full details of a specific care request including patient and creator summaries.",
)
def get_care_request(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CareRequestResponse:
    """Fetch care request details by UUID."""
    return CareRequestService.get_care_request_by_id(db=db, care_request_id=id)


@router.patch(
    "/{id}",
    response_model=CareRequestResponse,
    summary="Update care request",
    description="Update permitted clinical requirements, urgency, symptoms, or notes for a care request.",
)
def update_care_request(
    id: uuid.UUID,
    update_in: CareRequestUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = require_roles(*CARE_REQUEST_ROLES),
) -> CareRequestResponse:
    """Update care request details."""
    client_ip = request.client.host if request.client else None
    return CareRequestService.update_care_request(
        db=db,
        care_request_id=id,
        update_in=update_in,
        current_user=current_user,
        client_ip=client_ip,
    )
