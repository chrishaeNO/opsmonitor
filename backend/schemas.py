"""Pydantic schemas for API request/response."""
from datetime import datetime
from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    org_name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


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
    password: str
    role: str = "user"


class UserCreateResponse(BaseModel):
    id: int
    email: str
    role: str
    organization_id: int
    created_at: datetime

    class Config:
        from_attributes = True
