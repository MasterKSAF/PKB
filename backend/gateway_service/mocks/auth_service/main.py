"""
Auth Service Mock
Сервис аутентификации и управления пользователями (in-memory).
Порт: 8082
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import copy
import hashlib
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from ..common import (
    SEED_AUDIT,
    SEED_ROLES,
    SEED_USERS,
    error_response,
    new_id,
    paginate,
    utcnow,
)

router = APIRouter(prefix="/api/v1")

# ---------------------------------------------------------------------------
# In-memory хранилища
# ---------------------------------------------------------------------------

_users: dict[str, dict] = {}
_roles: dict[str, dict] = {}
_audit: list[dict] = []
_tokens: dict[str, str] = {}  # refresh_token -> user_id
_tokens_meta: dict[str, dict] = {}  # refresh_token -> {user_id, expires_at, created_at}
_blacklist: dict[str, str] = {}  # refresh_token -> revoked_at
_password_hashes: dict[str, str] = {}  # user_id -> hashed password
_rate_limits: dict[str, dict] = {}  # ip -> {"count": int, "reset_at": str}


def _init_data():
    global _users, _roles, _audit, _tokens, _tokens_meta, _password_hashes, _rate_limits
    if _users and _roles:
        return  # already initialized — preserve existing state
    _users = {u["user_id"]: copy.deepcopy(u) for u in SEED_USERS}
    _roles = {r["role_id"]: copy.deepcopy(r) for r in SEED_ROLES}
    _audit = copy.deepcopy(SEED_AUDIT)
    _rate_limits = {}

    # Хеши паролей (простой SHA256 для мока)
    for u in SEED_USERS:
        _password_hashes[u["user_id"]] = hashlib.sha256(
            u["password"].encode()
        ).hexdigest()

    # Начальные refresh-токены (для u-001, u-002, u-003)
    now = utcnow()
    expires_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    _tokens["rt-mock-001"] = "u-001"
    _tokens_meta["rt-mock-001"] = {
        "user_id": "u-001",
        "expires_at": expires_at,
        "created_at": now,
    }
    _tokens["rt-mock-002"] = "u-002"
    _tokens_meta["rt-mock-002"] = {
        "user_id": "u-002",
        "expires_at": expires_at,
        "created_at": now,
    }
    _tokens["rt-mock-003"] = "u-003"
    _tokens_meta["rt-mock-003"] = {
        "user_id": "u-003",
        "expires_at": expires_at,
        "created_at": now,
    }


def _make_token(user_id: str) -> dict:
    """Генерирует пару токенов."""
    rt = f"rt-mock-{new_id()}"
    now = utcnow()
    expires_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    _tokens[rt] = user_id
    _tokens_meta[rt] = {"user_id": user_id, "expires_at": expires_at, "created_at": now}
    return {
        "access_token": f"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.mock.{new_id()}",
        "refresh_token": rt,
        "token_type": "bearer",
        "expires_in": 3600,
        "expires_at": expires_at,
    }


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _add_audit(
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: str = "",
    details: dict | None = None,
    ip: str = "127.0.0.1",
):
    _audit.append(
        {
            "event_id": f"evt-{new_id()}",
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
            "ip_address": ip,
            "timestamp": utcnow(),
        }
    )


# ---------------------------------------------------------------------------
# Модели данных
# ---------------------------------------------------------------------------


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class RevokeRequest(BaseModel):
    refresh_token: str


class CreateUserRequest(BaseModel):
    email: str
    full_name: str
    password: str
    roles: list[str]


class UpdateUserRequest(BaseModel):
    email: str | None = None
    full_name: str | None = None
    position: str | None = None
    roles: list[str] | None = None
    is_active: bool | None = None
    password: str | None = None


class PatchUserRequest(BaseModel):
    role: str | None = None
    roles: list[str] | None = None
    email: str | None = None
    full_name: str | None = None
    position: str | None = None
    is_active: bool | None = None
    password: str | None = None


class CreateRoleRequest(BaseModel):
    name: str
    permissions: list[str]


class ValidateTokenRequest(BaseModel):
    access_token: str


# ---------------------------------------------------------------------------
# Response-модели для OpenAPI
# ---------------------------------------------------------------------------


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    expires_at: str


class UserProfileResponse(BaseModel):
    user_id: str
    full_name: str
    position: str
    role: str
    role_title: str
    available_tabs: list[str]
    permissions: dict[str, Any]
    last_login_at: str
    created_at: str


class UserListItem(BaseModel):
    user_id: str
    email: str
    full_name: str
    position: str
    roles: list[str]
    is_active: bool
    last_login_at: str
    created_at: str


class UserListResponse(BaseModel):
    users: list[UserListItem]
    meta: dict[str, Any]


class UserDetailResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    position: str
    roles: list[str]
    permissions: dict[str, bool]
    is_active: bool
    last_login_at: str
    created_at: str
    updated_at: str


class UserCreateResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    position: str
    roles: list[str]
    role: str
    role_title: str
    is_active: bool
    available_tabs: list[str]
    permissions: dict[str, Any]
    last_login_at: str
    created_at: str
    updated_at: str


class RoleResponse(BaseModel):
    role_id: str
    name: str
    permissions: list[str]
    created_at: str


class RolesListResponse(BaseModel):
    roles: list[RoleResponse]


class AuditEvent(BaseModel):
    event_id: str
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    details: dict[str, Any]
    ip_address: str
    timestamp: str


class AuditListResponse(BaseModel):
    events: list[AuditEvent]
    meta: dict[str, Any]


class MessageResponse(BaseModel):
    message: str
    revoked_at: str


class DeactivateResponse(BaseModel):
    user_id: str
    is_active: bool
    deactivated_at: str


class PatchUserResponse(BaseModel):
    user_id: str
    role: str
    audit_log_id: str
    updated_at: str


# ---------------------------------------------------------------------------
# Инициализация
# ---------------------------------------------------------------------------

_init_data()


# ===========================================================================
# Группа auth
# ===========================================================================


@router.post("/auth/token", response_model=TokenResponse)
async def login(req: LoginRequest, request: Request):
    """Получение JWT-токенов."""
    # Rate limiting: не более 5 запросов в минуту с одного IP
    ip = request.client.host if request.client else "127.0.0.1"
    now = utcnow()

    if ip not in _rate_limits:
        _rate_limits[ip] = {"count": 0, "reset_at": now}

    # Сброс счётчика, если прошла минута
    reset_at = datetime.fromisoformat(_rate_limits[ip]["reset_at"])
    if datetime.now(timezone.utc) - reset_at > timedelta(minutes=1):
        _rate_limits[ip] = {"count": 0, "reset_at": now}

    if _rate_limits[ip]["count"] >= 5:
        raise HTTPException(
            status_code=429,
            detail=error_response(
                "TOO_MANY_REQUESTS", "Слишком много запросов. Попробуйте позже"
            ),
        )
    _rate_limits[ip]["count"] += 1

    # Поиск пользователя
    user = None
    login_value = req.username.strip().lower()
    for u in _users.values():
        user_email = u.get("email", "").lower()
        user_login = user_email.split("@")[0]
        if user_email == login_value or user_login == login_value:
            stored_hash = _password_hashes.get(u["user_id"], "")
            if _hash_password(req.password) == stored_hash:
                user = u
                break

    if not user:
        raise HTTPException(
            status_code=401,
            detail=error_response("UNAUTHORIZED", "Неверные учётные данные"),
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=401,
            detail=error_response("UNAUTHORIZED", "Пользователь деактивирован"),
        )

    # Обновляем last_login_at
    user["last_login_at"] = utcnow()
    _add_audit(
        user["user_id"],
        "login",
        "auth",
        ip=request.client.host if request.client else "127.0.0.1",
    )

    return _make_token(user["user_id"])


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh(req: RefreshRequest):
    """Обновление access-токена."""
    if req.refresh_token in _blacklist:
        raise HTTPException(
            status_code=401,
            detail=error_response("INVALID_TOKEN", "Токен отозван"),
        )

    # Проверка срока действия refresh-токена
    rt_meta = _tokens_meta.get(req.refresh_token)
    if rt_meta:
        expires_at = datetime.fromisoformat(rt_meta["expires_at"])
        if datetime.now(timezone.utc) > expires_at:
            # Очищаем истёкший токен
            _tokens.pop(req.refresh_token, None)
            _tokens_meta.pop(req.refresh_token, None)
            raise HTTPException(
                status_code=401,
                detail=error_response("INVALID_TOKEN", "Refresh-токен истёк"),
            )

    user_id = _tokens.get(req.refresh_token)
    if not user_id or user_id not in _users:
        raise HTTPException(
            status_code=401,
            detail=error_response("INVALID_TOKEN", "Токен недействителен или истёк"),
        )

    return _make_token(user_id)


@router.post("/auth/revoke", response_model=MessageResponse)
async def revoke(req: RevokeRequest):
    """Отзыв refresh-токена."""
    if req.refresh_token in _tokens:
        del _tokens[req.refresh_token]
    _tokens_meta.pop(req.refresh_token, None)

    _blacklist[req.refresh_token] = utcnow()

    return {
        "message": "Токен отозван",
        "revoked_at": utcnow(),
    }


@router.get("/auth/me", response_model=UserProfileResponse)
async def get_me(request: Request):
    """Профиль текущего пользователя из JWT-токена."""
    user_state = request.state.user

    if not user_state["is_authenticated"]:
        raise HTTPException(
            status_code=401,
            detail=error_response("UNAUTHORIZED", "Не авторизован"),
        )

    user_id = user_state["user_id"]
    user = _users.get(user_id)
    if not user:
        raise HTTPException(
            status_code=401,
            detail=error_response("UNAUTHORIZED", "Пользователь не найден"),
        )

    return {
        "user_id": user["user_id"],
        "full_name": user["full_name"],
        "position": user.get("position", ""),
        "role": user.get("role", user["roles"][0] if user["roles"] else "engineer"),
        "role_title": user.get(
            "role_title", user["roles"][0] if user["roles"] else "Инженер"
        ),
        "available_tabs": user.get("available_tabs", []),
        "permissions": user.get("permissions", {}),
        "last_login_at": user.get("last_login_at", utcnow()),
        "created_at": user.get("created_at", utcnow()),
    }


# ===========================================================================
# Группа admin
# ===========================================================================


@router.get("/admin/users", response_model=UserListResponse)
async def list_users(
    role: str | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
):
    """Список пользователей."""
    items = list(_users.values())

    if role:
        items = [u for u in items if role in u.get("roles", [])]

    if search:
        search_lower = search.lower()
        items = [
            u
            for u in items
            if search_lower in u.get("full_name", "").lower()
            or search_lower in u.get("email", "").lower()
        ]

    # Форматируем для ответа
    result = []
    for u in items:
        result.append(
            {
                "user_id": u["user_id"],
                "email": u.get("email", ""),
                "full_name": u.get("full_name", ""),
                "position": u.get("position", ""),
                "roles": u.get("roles", []),
                "is_active": u.get("is_active", True),
                "last_login_at": u.get("last_login_at", ""),
                "created_at": u.get("created_at", ""),
            }
        )

    return {
        "users": paginate(result, page, page_size)["items"],
        "meta": paginate(result, page, page_size)["meta"],
    }


@router.post("/admin/users", status_code=201, response_model=UserCreateResponse)
async def create_user(req: CreateUserRequest, request: Request):
    """Создание пользователя."""
    # Проверка дубликата email
    for u in _users.values():
        if u.get("email", "").lower() == req.email.lower():
            raise HTTPException(
                status_code=409,
                detail=error_response("DUPLICATE_EMAIL", "Email уже используется"),
            )

    user_id = f"u-{new_id()}"
    now = utcnow()
    new_user = {
        "user_id": user_id,
        "email": req.email,
        "full_name": req.full_name,
        "position": "",
        "roles": req.roles,
        "role": req.roles[0] if req.roles else "engineer",
        "role_title": req.roles[0] if req.roles else "Инженер",
        "is_active": True,
        "available_tabs": ["chat", "search", "checks", "history"],
        "permissions": {
            "can_upload_documents": False,
            "can_run_ocr": False,
            "can_manage_users": False,
            "can_manage_classifiers": False,
            "can_manage_terminology": False,
            "can_manage_registry": False,
        },
        "last_login_at": "",
        "created_at": now,
        "updated_at": now,
    }
    _users[user_id] = new_user
    _password_hashes[user_id] = _hash_password(req.password)

    _add_audit(
        request.state.user.get("user_id") or "system",
        "user.create",
        "user",
        user_id,
        {"email": req.email},
    )

    return new_user


@router.get("/admin/users/{user_id}", response_model=UserDetailResponse)
async def get_user(user_id: str):
    """Детали пользователя."""
    user = _users.get(user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail=error_response("USER_NOT_FOUND", "Пользователь не найден"),
        )

    return {
        "user_id": user["user_id"],
        "email": user.get("email", ""),
        "full_name": user.get("full_name", ""),
        "position": user.get("position", ""),
        "roles": user.get("roles", []),
        "permissions": user.get("permissions", {})
        if isinstance(user.get("permissions"), dict)
        else {},
        "is_active": user.get("is_active", True),
        "last_login_at": user.get("last_login_at", ""),
        "created_at": user.get("created_at", ""),
        "updated_at": user.get("updated_at", ""),
    }


@router.put("/admin/users/{user_id}", response_model=UserCreateResponse)
async def update_user(user_id: str, req: UpdateUserRequest, request: Request):
    """Обновление пользователя."""
    user = _users.get(user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail=error_response("USER_NOT_FOUND", "Пользователь не найден"),
        )

    if req.email is not None:
        user["email"] = req.email
    if req.full_name is not None:
        user["full_name"] = req.full_name
    if req.position is not None:
        user["position"] = req.position
    if req.roles is not None:
        user["roles"] = req.roles
        user["role"] = req.roles[0] if req.roles else user["role"]
    if req.is_active is not None:
        user["is_active"] = req.is_active
    if req.password is not None:
        _password_hashes[user_id] = _hash_password(req.password)
        # Отозвать все refresh-токены этого пользователя
        tokens_to_remove = [rt for rt, uid in _tokens.items() if uid == user_id]
        for rt in tokens_to_remove:
            del _tokens[rt]
            _tokens_meta.pop(rt, None)

    user["updated_at"] = utcnow()
    _add_audit(
        request.state.user.get("user_id") or "system", "user.update", "user", user_id
    )

    return user


@router.patch("/admin/users/{user_id}", response_model=PatchUserResponse)
async def patch_user(user_id: str, req: PatchUserRequest, request: Request):
    """Частичное обновление пользователя."""
    user = _users.get(user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail=error_response("USER_NOT_FOUND", "Пользователь не найден"),
        )

    audit_log_id = f"audit-{new_id()}"

    if req.role is not None:
        user["role"] = req.role
        user["roles"] = [req.role]
    if req.roles is not None:
        user["roles"] = req.roles
        user["role"] = req.roles[0] if req.roles else user["role"]
    if req.email is not None:
        user["email"] = req.email
    if req.full_name is not None:
        user["full_name"] = req.full_name
    if req.position is not None:
        user["position"] = req.position
    if req.is_active is not None:
        user["is_active"] = req.is_active
    if req.password is not None:
        _password_hashes[user_id] = _hash_password(req.password)
        # Отозвать все refresh-токены этого пользователя
        tokens_to_remove = [rt for rt, uid in _tokens.items() if uid == user_id]
        for rt in tokens_to_remove:
            del _tokens[rt]
            _tokens_meta.pop(rt, None)

    user["updated_at"] = utcnow()
    _add_audit(
        request.state.user.get("user_id") or "system", "user.patch", "user", user_id
    )

    return {
        "user_id": user["user_id"],
        "role": user.get("role", user["roles"][0] if user["roles"] else ""),
        "audit_log_id": audit_log_id,
        "updated_at": user["updated_at"],
    }


@router.delete("/admin/users/{user_id}", response_model=DeactivateResponse)
async def deactivate_user(user_id: str, request: Request):
    """Деактивация пользователя."""
    user = _users.get(user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail=error_response("USER_NOT_FOUND", "Пользователь не найден"),
        )

    user["is_active"] = False
    now = utcnow()
    _add_audit(
        request.state.user.get("user_id") or "system",
        "user.deactivate",
        "user",
        user_id,
    )

    return {
        "user_id": user["user_id"],
        "is_active": False,
        "deactivated_at": now,
    }


@router.get("/admin/roles", response_model=RolesListResponse)
async def list_roles():
    """Список ролей."""
    return {"roles": list(_roles.values())}


@router.post("/admin/roles", status_code=201)
async def create_role(req: CreateRoleRequest, request: Request):
    """Создание роли."""
    role_id = f"r-{new_id()}"
    new_role = {
        "role_id": role_id,
        "name": req.name,
        "permissions": req.permissions,
        "created_at": utcnow(),
    }
    _roles[role_id] = new_role
    _add_audit(
        request.state.user.get("user_id") or "system", "role.create", "role", role_id
    )

    return new_role


@router.get("/admin/audit")
async def list_audit(
    user_id: str | None = Query(None),
    action: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """Журнал аудита."""
    items = list(_audit)

    if user_id:
        items = [e for e in items if e["user_id"] == user_id]
    if action:
        items = [e for e in items if action in e["action"]]
    if date_from:
        items = [e for e in items if e["timestamp"] >= date_from]
    if date_to:
        items = [e for e in items if e["timestamp"] <= date_to]

    paged = paginate(items, page, page_size)
    return {
        "events": paged["items"],
        "meta": paged["meta"],
    }


# ===========================================================================
# Internal endpoints
# ===========================================================================


@router.post("/internal/auth/validate")
async def validate_token(req: ValidateTokenRequest):
    """Внутренняя проверка токена."""
    # Для мока любой непустой токен считается валидным
    if not req.access_token or len(req.access_token) < 10:
        raise HTTPException(
            status_code=401,
            detail=error_response("INVALID_TOKEN", "Токен недействителен или истёк"),
        )

    user = next(
        (u for u in _users.values() if u.get("is_active", True)),
        None,
    )
    if not user:
        raise HTTPException(
            status_code=401,
            detail=error_response("INVALID_TOKEN", "Токен недействителен или истёк"),
        )

    return {
        "valid": True,
        "user_id": user["user_id"],
        "email": user.get("email", ""),
        "roles": user.get("roles", []),
        "permissions": user.get("permissions", {})
        if isinstance(user.get("permissions"), dict)
        else {},
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    }


# ===========================================================================
# Health check
# ===========================================================================


@router.get("/system/health")
async def health():
    return {
        "status": "ok",
        "service": "auth-service",
        "timestamp": utcnow(),
    }
