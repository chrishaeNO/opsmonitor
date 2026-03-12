"""Current user: GET /me."""
from fastapi import APIRouter, Depends

from backend.database import get_db
from backend import models_db
from backend.schemas import UserResponse
from backend.auth import get_current_user

router = APIRouter(tags=["me"])


@router.get("/me", response_model=UserResponse)
def get_me(current_user: models_db.User = Depends(get_current_user), db=Depends(get_db)):
    org = db.query(models_db.Organization).filter(
        models_db.Organization.id == current_user.organization_id
    ).first()
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role.value,
        organization_id=current_user.organization_id,
        organization_name=org.name if org else "",
        created_at=current_user.created_at,
    )
