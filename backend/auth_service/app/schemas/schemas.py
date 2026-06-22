from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator


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

    @field_validator("password")
    @classmethod
    def password_policy(cls, v: str) -> str:
        import re
        if not re.search(r"[A-Z]", v):
            raise ValueError("Пароль должен содержать хотя бы одну заглавную букву")
        if not re.search(r"\d", v):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")
        if not re.search(r"[!@#$%^&*()\-_=+\[\]{};':\"\\|,.<>/?`~]", v):
            raise ValueError("Пароль должен содержать хотя бы один спецсимвол")
        return v


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


class MetaPagination(BaseModel):
    total: int
    page: int
    page_size: int


class UserListResponse(BaseModel):
    users: list[UserListItem]
    meta: MetaPagination


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
    meta: MetaPagination


class UserPermissions(BaseModel):
    can_upload_documents: bool
    can_run_ocr: bool
    can_manage_users: bool
    can_manage_classifiers: bool
    can_manage_terminology: bool
    can_manage_registry: bool


class UserMeResponse(BaseModel):
    user_id: str
    full_name: str
    role: str
    role_title: str
    available_tabs: list[str]
    permissions: UserPermissions
    last_login_at: datetime | None = None
    created_at: datetime


class InternalValidateRequest(BaseModel):
    access_token: str


class InternalValidateResponse(BaseModel):
    valid: bool
    user_id: str
    email: str
    roles: list[str]
    permissions: list[str]
    exp: int
