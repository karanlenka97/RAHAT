"""Villages API endpoint for habitational registry."""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.village import Village
from app.models.user import User
from app.schemas.patient import VillageSummary

router = APIRouter()


@router.get(
    "",
    response_model=List[VillageSummary],
    summary="List available villages",
    description="Retrieve all registered habitational villages for patient onboarding and facility routing.",
)
def list_villages(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[VillageSummary]:
    """Return all villages."""
    villages = db.query(Village).order_by(Village.name.asc()).all()
    return [
        VillageSummary(
            id=v.id,
            name=v.name,
            district=v.district,
            state=v.state,
            pincode=v.pincode,
        )
        for v in villages
    ]
