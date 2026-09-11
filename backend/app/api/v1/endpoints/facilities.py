"""Facility & Facility Capabilities Management API endpoints."""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_roles
from app.models.user import User
from app.schemas.facility import (
    FacilityCreate,
    FacilityUpdate,
    FacilityResponse,
    FacilityListResponse,
    FacilityCapabilityCreate,
    FacilityCapabilityUpdate,
    FacilityCapabilityResponse,
    NearbyFacilitiesResponse,
)
from app.services.facility_service import FacilityService

router = APIRouter()

# Administrative roles authorized for facility & capability modifications
FACILITY_MANAGE_ROLES = [
    "ADMIN",
    "DISTRICT_ADMIN",
    "FACILITY_ADMIN",
]


@router.post(
    "",
    response_model=FacilityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new healthcare facility",
    description="Add a new healthcare facility (AAM, PHC, CHC, Hospital, etc.) to the health infrastructure registry.",
)
def create_facility(
    facility_in: FacilityCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = require_roles(*FACILITY_MANAGE_ROLES),
) -> FacilityResponse:
    """Create a new facility record."""
    client_ip = request.client.host if request.client else None
    return FacilityService.create_facility(
        db=db,
        facility_in=facility_in,
        current_user=current_user,
        client_ip=client_ip,
    )


@router.get(
    "",
    response_model=FacilityListResponse,
    summary="List healthcare facilities",
    description="Retrieve a paginated list of facilities with optional filters for facility type, district, status, and search term.",
)
def list_facilities(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    facility_type: Optional[str] = Query(None, description="Filter by facility type (e.g. PHC, CHC, DISTRICT_HOSPITAL)"),
    district: Optional[str] = Query(None, description="Filter by district name"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search term across name, code, address, and district"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FacilityListResponse:
    """List facilities matching the query criteria."""
    return FacilityService.list_facilities(
        db=db,
        page=page,
        page_size=page_size,
        facility_type=facility_type,
        district=district,
        is_active=is_active,
        search=search,
    )


@router.get(
    "/nearby",
    response_model=NearbyFacilitiesResponse,
    summary="Find nearby facilities",
    description="Geographic lookup of active healthcare facilities within a specified radius (km) from coordinates.",
)
def get_nearby_facilities(
    latitude: float = Query(..., ge=-90.0, le=90.0, description="Latitude of center point"),
    longitude: float = Query(..., ge=-180.0, le=180.0, description="Longitude of center point"),
    radius_km: float = Query(25.0, ge=0.1, le=200.0, description="Search radius in kilometers (default 25 km)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NearbyFacilitiesResponse:
    """Geospatial proximity search for facilities."""
    return FacilityService.find_nearby_facilities(
        db=db,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
    )


@router.get(
    "/{id}",
    response_model=FacilityResponse,
    summary="Get facility by ID",
    description="Retrieve detailed facility information including its capabilities, bed counts, and contact data.",
)
def get_facility(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FacilityResponse:
    """Fetch facility profile by UUID."""
    return FacilityService.get_facility_by_id(db=db, facility_id=id)


@router.patch(
    "/{id}",
    response_model=FacilityResponse,
    summary="Update facility",
    description="Update facility details, bed counts, status, or contact information.",
)
def update_facility(
    id: uuid.UUID,
    update_in: FacilityUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = require_roles(*FACILITY_MANAGE_ROLES),
) -> FacilityResponse:
    """Update facility attributes."""
    client_ip = request.client.host if request.client else None
    return FacilityService.update_facility(
        db=db,
        facility_id=id,
        update_in=update_in,
        current_user=current_user,
        client_ip=client_ip,
    )


# ---------------------------------------------------------------------------
# Facility Capabilities Sub-resource Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/{id}/capabilities",
    response_model=List[FacilityCapabilityResponse],
    summary="List facility capabilities",
    description="Retrieve all clinical and diagnostic capabilities defined for a specific facility.",
)
def list_facility_capabilities(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[FacilityCapabilityResponse]:
    """List capabilities for the facility."""
    return FacilityService.list_capabilities(db=db, facility_id=id)


@router.post(
    "/{id}/capabilities",
    response_model=FacilityCapabilityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add facility capability",
    description="Add a new service/diagnostic capability to a healthcare facility.",
)
def create_facility_capability(
    id: uuid.UUID,
    cap_in: FacilityCapabilityCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = require_roles(*FACILITY_MANAGE_ROLES),
) -> FacilityCapabilityResponse:
    """Add a capability to the facility."""
    client_ip = request.client.host if request.client else None
    return FacilityService.create_capability(
        db=db,
        facility_id=id,
        cap_in=cap_in,
        current_user=current_user,
        client_ip=client_ip,
    )


@router.patch(
    "/{id}/capabilities/{capability_id}",
    response_model=FacilityCapabilityResponse,
    summary="Update facility capability",
    description="Update availability, capacity, or current load of a facility capability.",
)
def update_facility_capability(
    id: uuid.UUID,
    capability_id: uuid.UUID,
    update_in: FacilityCapabilityUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = require_roles(*FACILITY_MANAGE_ROLES),
) -> FacilityCapabilityResponse:
    """Update a capability."""
    client_ip = request.client.host if request.client else None
    return FacilityService.update_capability(
        db=db,
        facility_id=id,
        capability_id=capability_id,
        update_in=update_in,
        current_user=current_user,
        client_ip=client_ip,
    )
