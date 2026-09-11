"""API v1 router registry."""
from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    auth,
    patients,
    villages,
    care_requests,
    facilities,
    recommendations,
    referrals,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(patients.router, prefix="/patients", tags=["Patients"])
api_router.include_router(villages.router, prefix="/villages", tags=["Villages"])
api_router.include_router(care_requests.router, prefix="/care-requests", tags=["Care Requests"])
api_router.include_router(facilities.router, prefix="/facilities", tags=["Facilities"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["Smart Recommendations"])
api_router.include_router(referrals.router, prefix="/referrals", tags=["Referrals"])
