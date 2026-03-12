"""Auth routes: register, login, refresh."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend import models_db
from backend.schemas import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest
from backend.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(models_db.User).filter(models_db.User.email == data.email).first():
        raise HTTPException(status_code=400, detail="E-post er allerede registrert")
    org = models_db.Organization(name=data.org_name, seat_count=5)
    db.add(org)
    db.flush()
    user = models_db.User(
        organization_id=org.id,
        email=data.email,
        password_hash=hash_password(data.password),
        role=models_db.UserRole.admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    access = create_access_token({"sub": str(user.id)})
    refresh_token, _ = create_refresh_token(user.id)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models_db.User).filter(models_db.User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Ugyldig e-post eller passord")
    access = create_access_token({"sub": str(user.id)})
    refresh_token, _ = create_refresh_token(user.id)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Ugyldig refresh token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Ugyldig refresh token")
    user = db.query(models_db.User).filter(models_db.User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="Bruker ikke funnet")
    access = create_access_token({"sub": str(user.id)})
    new_refresh, _ = create_refresh_token(user.id)
    return TokenResponse(
        access_token=access,
        refresh_token=new_refresh,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
