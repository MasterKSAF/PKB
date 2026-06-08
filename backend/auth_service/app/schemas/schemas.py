from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class TokenRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class RevokeRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RevokeResponse(BaseModel):
    message: str
    revoked_at: datetime


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(min_length=8)
    roles: list[str]


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None
    roles: list[str] | None = None
    is_active: bool | None = None


class UserPublic(BaseModel):
    user_id: str
    email: str
    full_name: str
    roles: list[str]
    permissions: list[str]
    is_active: bool = True
    created_at: datetime
    updated_at: datetime | None = None


class UserListItem(BaseModel):
    user_id: str
    email: str
    full_name: str
    roles: list[str]
    is_active: bool
    created_at: datetime


class UserListResponse(BaseModel):
    users: list[UserListItem]
    total: int
    limit: int
    offset: int


class RoleCreate(BaseModel):
    name: str
    permissions: list[str]


class RolePublic(BaseModel):
    role_id: str
    name: str
    permissions: list[str]
    created_at: datetime


class RoleListResponse(BaseModel):
    roles: list[RolePublic]


class AuditEventPublic(BaseModel):
    event_id: str
    user_id: str | None
    action: str
    resource_type: str | None
    resource_id: str | None
    details: dict[str, Any] | None
    ip_address: str | None
    timestamp: datetime


class AuditListResponse(BaseModel):
    events: list[AuditEventPublic]
    total: int


class InternalValidateRequest(BaseModel):
    access_token: str


class InternalValidateResponse(BaseModel):
    valid: bool
    user_id: str
    email: str
    roles: list[str]
    permissions: list[str]
    exp: int
