"""API v1 router registry."""
from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, patients, villages

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(patients.router, prefix="/patients", tags=["Patients"])
api_router.include_router(villages.router, prefix="/villages", tags=["Villages"])
