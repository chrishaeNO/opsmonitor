"""Pydantic schemas for API request/response."""
from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, EmailStr, constr


# Bcrypt støtter maks 72 byte passord. Vi validerer på schema-nivå
# slik at APIet gir en ryddig 422-feil i stedet for 500.
PasswordStr = constr(min_length=8, max_length=72)


class RegisterRequest(BaseModel):
    org_name: str
    email: EmailStr
    password: PasswordStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: PasswordStr


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    organization_id: int
    organization_name: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserCreateRequest(BaseModel):
    email: EmailStr
    password: PasswordStr
    role: str = "user"


class UserCreateResponse(BaseModel):
    id: int
    email: str
    role: str
    organization_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class LayoutConfig(BaseModel):
    """Struktur for enkelt dashboard-layout slik desktop-klienten kjenner det."""

    id: Optional[str] = None
    title: str
    template: str
    rows: int
    cols: int
    slot_assignments: Dict[str, str] = {}


class LayoutOut(BaseModel):
    id: int
    name: str
    config: LayoutConfig
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LayoutCreate(BaseModel):
    name: str
    config: LayoutConfig


class LayoutUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[LayoutConfig] = None
