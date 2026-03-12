"""Auth routes: register, login, refresh – OWASP A07 brute-force protection."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
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

# OWASP A07 – account lockout thresholds
_MAX_ATTEMPTS = 5
_LOCKOUT_MINUTES = 15
# Generic message – never leak whether email exists
_AUTH_FAIL = "Ugyldig e-post eller passord"


def _check_lockout(user: models_db.User) -> None:
    if user.locked_until and datetime.utcnow() < user.locked_until:
        remaining = int((user.locked_until - datetime.utcnow()).total_seconds() / 60) + 1
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"For mange mislykkede forsøk – prøv igjen om {remaining} min",
        )


def _record_failed(db: Session, user: models_db.User) -> None:
    try:
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        if user.failed_login_attempts >= _MAX_ATTEMPTS:
            user.locked_until = datetime.utcnow() + timedelta(minutes=_LOCKOUT_MINUTES)
        db.commit()
    except Exception:
        db.rollback()


def _record_success(db: Session, user: models_db.User) -> None:
    try:
        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()
    except Exception:
        db.rollback()


def _issue_tokens(db: Session, user: models_db.User) -> TokenResponse:
    access = create_access_token({"sub": str(user.id)})
    refresh_token, _ = create_refresh_token(user.id)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


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
    return _issue_tokens(db, user)


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    # Look up user without leaking existence (constant-time path)
    user = db.query(models_db.User).filter(models_db.User.email == data.email).first()

    if not user:
        # Run a dummy verify so timing is consistent (OWASP A07)
        verify_password("dummy", hash_password("dummy"))
        raise HTTPException(status_code=401, detail=_AUTH_FAIL)

    _check_lockout(user)

    if not verify_password(data.password, user.password_hash):
        _record_failed(db, user)
        raise HTTPException(status_code=401, detail=_AUTH_FAIL)

    # Optional: verify API key header if present (org-level validation)
    api_key_header = request.headers.get("X-API-Key")
    if api_key_header:
        from backend.routes.apikeys import verify_api_key
        key_record = verify_api_key(api_key_header, db)
        if not key_record:
            raise HTTPException(status_code=401, detail="Ugyldig API-nøkkel")
        if key_record.organization_id != user.organization_id:
            raise HTTPException(status_code=403, detail="API-nøkkel tilhører en annen organisasjon")

    _record_success(db, user)
    return _issue_tokens(db, user)


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
        raise HTTPException(status_code=401, detail=_AUTH_FAIL)
    return _issue_tokens(db, user)
