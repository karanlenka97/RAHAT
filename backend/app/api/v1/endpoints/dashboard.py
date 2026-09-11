"""Dashboard API Router for Frontline, Facility, and District Operations."""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_roles
from app.models.user import User
from app.schemas.dashboard import (
    FrontlineDashboardResponse,
    FacilityDashboardResponse,
    DistrictDashboardResponse,
    ReferralFunnelResponse,
    CareCompletionResponse,
)
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get(
    "/frontline",
    response_model=FrontlineDashboardResponse,
    summary="Get Frontline Worker Operational Dashboard",
    description="Returns patient counts, active care requests, pending referrals, and prioritized action queue for frontline health workers (ASHA, ANM, CHO, MO).",
)
def get_frontline_dashboard(
    db: Session = Depends(get_db),
    current_user: User = require_roles("ASHA", "ANM", "CHO", "MEDICAL_OFFICER", "ADMIN"),
):
    """Frontline community operational dashboard endpoint."""
    try:
        return DashboardService.get_frontline_dashboard(db=db, current_user=current_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate frontline dashboard: {str(e)}",
        )


@router.get(
    "/facility",
    response_model=FacilityDashboardResponse,
    summary="Get Facility Operational Dashboard",
    description="Returns inbound referral queues, live bed occupancy, and capability workloads for health facilities (FACILITY_ADMIN, DOCTOR, MO).",
)
def get_facility_dashboard(
    facility_id: Optional[uuid.UUID] = Query(None, description="Optional facility UUID (ADMIN only)"),
    db: Session = Depends(get_db),
    current_user: User = require_roles("FACILITY_ADMIN", "DOCTOR", "MEDICAL_OFFICER", "ADMIN"),
):
    """Facility operations and capacity monitoring dashboard endpoint."""
    try:
        return DashboardService.get_facility_dashboard(
            db=db,
            current_user=current_user,
            facility_id=facility_id,
        )
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate facility dashboard: {str(e)}",
        )


@router.get(
    "/district",
    response_model=DistrictDashboardResponse,
    summary="Get District Performance Dashboard",
    description="Returns aggregate health access metrics, care completion rate, and facility performance table for district administrators.",
)
def get_district_dashboard(
    district: Optional[str] = Query(None, description="Optional district name filter"),
    time_range: str = Query("all", description="Time range: 'today', '7d', '30d', or 'all'"),
    db: Session = Depends(get_db),
    current_user: User = require_roles("DISTRICT_ADMIN", "ADMIN"),
):
    """District-wide aggregated operational performance dashboard endpoint."""
    if time_range not in ("today", "7d", "30d", "all"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid time_range parameter. Allowed values: 'today', '7d', '30d', 'all'.",
        )

    # District isolation: DISTRICT_ADMIN can only query their own district
    user_role = current_user.role.name if current_user.role else ""
    if user_role == "DISTRICT_ADMIN" and district and current_user.facility and current_user.facility.district:
        if district.lower() != current_user.facility.district.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to other district performance data.",
            )

    try:
        return DashboardService.get_district_dashboard(
            db=db,
            current_user=current_user,
            district=district,
            time_range=time_range,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate district dashboard: {str(e)}",
        )


@router.get(
    "/referral-funnel",
    response_model=ReferralFunnelResponse,
    summary="Get Referral Lifecycle Funnel Analytics",
    description="Returns sequential lifecycle milestone progression and drop-off counts.",
)
def get_referral_funnel(
    district: Optional[str] = Query(None, description="Optional district filter"),
    facility_id: Optional[uuid.UUID] = Query(None, description="Optional facility filter"),
    time_range: str = Query("all", description="Time range filter: 'today', '7d', '30d', 'all'"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Referral funnel analytics endpoint."""
    if time_range not in ("today", "7d", "30d", "all"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid time_range parameter.",
        )

    try:
        return DashboardService.get_referral_funnel(
            db=db,
            current_user=current_user,
            district=district,
            facility_id=facility_id,
            time_range=time_range,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate referral funnel: {str(e)}",
        )


@router.get(
    "/care-completion",
    response_model=CareCompletionResponse,
    summary="Get Care Completion KPI Analytics",
    description="Returns detailed care completion metrics broken down by clinical category and urgency level.",
)
def get_care_completion(
    district: Optional[str] = Query(None, description="Optional district filter"),
    time_range: str = Query("all", description="Time range filter: 'today', '7d', '30d', 'all'"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dedicated Care Completion KPI breakdown endpoint."""
    if time_range not in ("today", "7d", "30d", "all"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid time_range parameter.",
        )

    try:
        return DashboardService.get_care_completion(
            db=db,
            current_user=current_user,
            district=district,
            time_range=time_range,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate care completion metrics: {str(e)}",
        )
