"""Patient Management API endpoints."""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Header, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_roles
from app.core.idempotency import idempotency_cache
from app.models.user import User
from app.schemas.patient import (
    PatientCreate,
    PatientUpdate,
    PatientResponse,
    PatientListResponse,
)
from app.services.patient_service import (
    create_patient,
    get_patients,
    get_patient_by_id,
    update_patient,
    format_patient_response,
)

router = APIRouter()

# Frontline, Clinical, and Administrative roles permitted to register/update patients
PATIENT_MANAGEMENT_ROLES = [
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
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new patient",
    description="Register a patient demographic and clinical record with a system-generated unique patient code.",
)
def register_patient(
    patient_in: PatientCreate,
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
    db: Session = Depends(get_db),
    current_user: User = require_roles(*PATIENT_MANAGEMENT_ROLES),
) -> PatientResponse:
    """Create a new patient record with idempotency replay protection."""
    # Check if request with identical idempotency key was already completed
    if x_idempotency_key:
        cached_res = idempotency_cache.get(x_idempotency_key)
        if cached_res:
            return cached_res

    try:
        new_patient = create_patient(db, patient_in, current_user)
        response_data = format_patient_response(new_patient)
        if x_idempotency_key:
            idempotency_cache.set(x_idempotency_key, response_data)
        return response_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )



@router.get(
    "",
    response_model=PatientListResponse,
    summary="List and search patients",
    description="Retrieve a paginated list of patients with optional query search by name, code, phone, or ABHA.",
)
def list_patients(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term for name, patient code, phone, or ABHA reference"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PatientListResponse:
    """List and search registered patients with pagination."""
    items, total, total_pages = get_patients(db, page=page, page_size=page_size, search=search)
    return PatientListResponse(
        items=[format_patient_response(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
    summary="Get patient profile by ID",
    description="Retrieve complete patient demographic, contact, village, and clinical profile.",
)
def get_patient(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PatientResponse:
    """Fetch patient by UUID."""
    patient = get_patient_by_id(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID '{patient_id}' not found.",
        )
    return format_patient_response(patient)


@router.patch(
    "/{patient_id}",
    response_model=PatientResponse,
    summary="Update permitted patient information",
    description="Update patient demographic, phone, address, village, or emergency contact.",
)
def patch_patient(
    patient_id: uuid.UUID,
    patient_update: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = require_roles(*PATIENT_MANAGEMENT_ROLES),
) -> PatientResponse:
    """Update existing patient record."""
    patient = get_patient_by_id(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID '{patient_id}' not found.",
        )

    try:
        updated = update_patient(db, patient, patient_update, current_user)
        return format_patient_response(updated)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
