"""Admin: list users, create user, delete user."""
from fastapi import APIRouter, Depends, HTTPException

from backend.database import get_db
from backend import models_db
from backend.schemas import UserResponse, UserCreateRequest, UserCreateResponse
from backend.auth import get_current_user, require_admin, hash_password

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserResponse])
def list_users(
    current_user: models_db.User = Depends(require_admin),
    db=Depends(get_db),
):
    if current_user.organization_id is None:
        return []
    users = (
        db.query(models_db.User)
        .filter(models_db.User.organization_id == current_user.organization_id)
        .all()
    )
    org = (
        db.query(models_db.Organization)
        .filter(models_db.Organization.id == current_user.organization_id)
        .first()
    )
    org_name = org.name if org else ""
    return [
        UserResponse(
            id=u.id,
            email=u.email,
            role=u.role.value,
            organization_id=u.organization_id,
            organization_name=org_name,
            created_at=u.created_at,
        )
        for u in users
    ]


@router.post("", response_model=UserCreateResponse)
def create_user(
    data: UserCreateRequest,
    current_user: models_db.User = Depends(require_admin),
    db=Depends(get_db),
):
    org_id = current_user.organization_id
    org = db.query(models_db.Organization).filter(models_db.Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organisasjon ikke funnet")
    count = db.query(models_db.User).filter(models_db.User.organization_id == org_id).count()
    if count >= org.seat_count:
        raise HTTPException(
            status_code=400,
            detail=f"Maks antall brukere ({org.seat_count}) er nådd. Oppgrader for flere plasser.",
        )
    if db.query(models_db.User).filter(models_db.User.email == data.email).first():
        raise HTTPException(status_code=400, detail="E-post er allerede i bruk")
    role = models_db.UserRole.admin if data.role == "admin" else models_db.UserRole.user
    user = models_db.User(
        organization_id=org_id,
        email=data.email,
        password_hash=hash_password(data.password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserCreateResponse(
        id=user.id,
        email=user.email,
        role=user.role.value,
        organization_id=user.organization_id,
        created_at=user.created_at,
    )


@router.delete("/{user_id}")
def delete_user(
  user_id: int,
  current_user: models_db.User = Depends(require_admin),
  db=Depends(get_db),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Du kan ikke slette deg selv")
    user = db.query(models_db.User).filter(
        models_db.User.id == user_id,
        models_db.User.organization_id == current_user.organization_id,
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="Bruker ikke funnet")
    db.delete(user)
    db.commit()
    return {"ok": True}
