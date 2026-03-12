"""API key management – create, list, revoke organisation keys (admin only)."""
import base64
import hashlib
import os
import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend import models_db
from backend.schemas import APIKeyCreate, APIKeyOut, APIKeyCreated
from backend.auth import require_admin

router = APIRouter(prefix="/apikeys", tags=["api-keys"])


# ── Key format ────────────────────────────────────────────────────────────────
# opsm_{base64url(server_url)}_{hex_64}
#
# The URL segment lets the desktop app derive the server URL from the key alone –
# no manual URL configuration required. The hex segment is the secret (256-bit).
# SHA-256(full_key) is stored in the DB; plaintext key is shown once on creation.


def _server_url(request: Request) -> str:
    """Resolve the public base URL of this server for embedding in keys."""
    # Prefer an explicit env var (set this in Vercel: PUBLIC_URL=https://...)
    public_url = os.getenv("PUBLIC_URL", "").rstrip("/")
    if public_url:
        return public_url
    # Fall back to request headers (Vercel sets x-forwarded-proto / host)
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.headers.get("host", ""))
    return f"{scheme}://{host}".rstrip("/")


def _generate_key(server_url: str) -> tuple[str, str, str]:
    """Return (full_key, key_hash, key_prefix).

    Key format: ``opsm_{base64url(server_url)}_{64 hex chars}``
    - base64url segment → desktop app decodes the server URL automatically
    - 64 hex chars      → 256-bit secret (high entropy, SHA-256 hash stored)
    - key_prefix        → first 20 chars stored for display only
    """
    url_b64 = base64.urlsafe_b64encode(server_url.encode()).rstrip(b"=").decode()
    raw = secrets.token_hex(32)                          # 64 hex chars, 256-bit
    full_key = f"opsm_{url_b64}_{raw}"
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    key_prefix = f"opsm_{url_b64[:8]}…"                 # readable but non-secret
    return full_key, key_hash, key_prefix


def parse_api_key(key: str) -> tuple[str, str] | None:
    """Parse key → (server_url, raw_token) or None if invalid format."""
    parts = key.split("_", 2)
    if len(parts) != 3 or parts[0] != "opsm":
        return None
    try:
        # Restore stripped padding
        padded = parts[1] + "=" * (-len(parts[1]) % 4)
        server_url = base64.urlsafe_b64decode(padded).decode()
        return server_url, parts[2]
    except Exception:
        return None


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
    request: Request,
    db: Session = Depends(get_db),
    admin: models_db.User = Depends(require_admin),
):
    name = payload.name.strip()
    if not name:
        raise HTTPException(400, "Nøkkelnavn er påkrevd")

    url = _server_url(request)
    full_key, key_hash, key_prefix = _generate_key(url)

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
        key=full_key,  # shown ONCE – never stored in plaintext
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
