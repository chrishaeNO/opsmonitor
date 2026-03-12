"""API key management – create, list, revoke organisation keys (admin only)."""
import hashlib
import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend import models_db
from backend.schemas import APIKeyCreate, APIKeyOut, APIKeyCreated
from backend.auth import require_admin

router = APIRouter(prefix="/apikeys", tags=["api-keys"])

_PREFIX = "opsm"


def _generate_key() -> tuple[str, str, str]:
    """Return (full_key, key_hash, key_prefix).

    Full key format: ``opsm_<64 hex chars>``
    The key itself is 32 random bytes (256-bit entropy).
    We store SHA-256(full_key) – sufficient for high-entropy random tokens.
    """
    raw = secrets.token_hex(32)          # 64 hex chars, 256-bit entropy
    full_key = f"{_PREFIX}_{raw}"        # e.g. opsm_1a2b...
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    key_prefix = full_key[:16]           # first 16 chars shown in list
    return full_key, key_hash, key_prefix


def verify_api_key(raw_key: str, db: Session) -> models_db.APIKey | None:
    """Look up and return an active API key record, or None."""
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key = (
        db.query(models_db.APIKey)
        .filter(
            models_db.APIKey.key_hash == key_hash,
            models_db.APIKey.revoked.is_(False),
        )
        .first()
    )
    if key:
        key.last_used_at = datetime.utcnow()
        db.commit()
    return key


@router.get("", response_model=list[APIKeyOut])
def list_keys(
    db: Session = Depends(get_db),
    admin: models_db.User = Depends(require_admin),
):
    return (
        db.query(models_db.APIKey)
        .filter(models_db.APIKey.organization_id == admin.organization_id)
        .order_by(models_db.APIKey.created_at.desc())
        .all()
    )


@router.post("", response_model=APIKeyCreated, status_code=status.HTTP_201_CREATED)
def create_key(
    payload: APIKeyCreate,
    db: Session = Depends(get_db),
    admin: models_db.User = Depends(require_admin),
):
    name = payload.name.strip()
    if not name:
        raise HTTPException(400, "Nøkkelnavn er påkrevd")

    full_key, key_hash, key_prefix = _generate_key()
    key = models_db.APIKey(
        organization_id=admin.organization_id,
        name=name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        revoked=False,
    )
    db.add(key)
    db.commit()
    db.refresh(key)

    return APIKeyCreated(
        id=key.id,
        name=key.name,
        key_prefix=key.key_prefix,
        revoked=key.revoked,
        created_at=key.created_at,
        last_used_at=key.last_used_at,
        key=full_key,  # shown ONCE – not stored in plaintext
    )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_key(
    key_id: int,
    db: Session = Depends(get_db),
    admin: models_db.User = Depends(require_admin),
):
    key = (
        db.query(models_db.APIKey)
        .filter(
            models_db.APIKey.id == key_id,
            models_db.APIKey.organization_id == admin.organization_id,
        )
        .first()
    )
    if not key:
        return
    key.revoked = True
    db.commit()
