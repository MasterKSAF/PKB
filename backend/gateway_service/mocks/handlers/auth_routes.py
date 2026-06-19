"""
Auth handlers — extracted from auth_service/main.py.
All data stores imported from mocks.common.
"""

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from mocks.common import (
    _users, _roles, _audit, _tokens, _tokens_meta,
    _access_token_map, _blacklist, _password_hashes, _rate_limits,
    new_id, utcnow, error_response, paginate,
)

logger = logging.getLogger("auth_service")

router = APIRouter()


# ── Depends / helpers ────────────────────────────────────────────────────────

async def get_current_user(request: Request) -> dict:
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail=error_response("UNAUTHORIZED", "Отсутствует токен"))
    token = auth.split(" ")[1]
    user_id = _access_token_map.get(token)
    if not user_id or user_id not in _users:
        raise HTTPException(status_code=401, detail=error_response("INVALID_TOKEN", "Токен недействителен или истёк"))
    return _users[user_id]


def require_admin(current_user: dict = Depends(get_current_user)):
    if "system_admin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail=error_response("FORBIDDEN", "Нет прав администратора"))
    return current_user


# ── Pydantic модели ──────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class RevokeRequest(BaseModel):
    refresh_token: str = ""
    token: str = ""


class CreateUserRequest(BaseModel):
    email: str
    full_name: str
    password: str
    roles: List[str]


class UpdateUserRequest(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    position: Optional[str] = None
    roles: Optional[List[str]] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class PatchUserRequest(BaseModel):
    roles: Optional[List[str]] = None  # AU-5: role заменён на roles[]
    role: Optional[str] = None  # обратная совместимость


class CreateRoleRequest(BaseModel):
    name: str
    permissions: List[str]


class ValidateTokenRequest(BaseModel):
    access_token: str


# ── Внутренние утилиты ──────────────────────────────────────────────────────

def _hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def _mask_ip(ip: str) -> str:
    """AU-6: Маскировка PII — IP → 123.xxx.xxx.xxx"""
    parts = ip.split(".")
    if len(parts) == 4:
        return f"{parts[0]}.xxx.xxx.xxx"
    return ip


def _validate_password(pw: str) -> None:
    """AU-4: Минимальная проверка пароля — только длина."""
    if len(pw) < 8:
        raise HTTPException(
            status_code=422,
            detail=error_response("WEAK_PASSWORD", "Пароль должен содержать минимум 8 символов"),
        )


def _add_audit(user_id: int, action: str, resource_type: str, resource_id: int = None,
               details: dict = None, ip: str = "127.0.0.1"):
    _audit.append({
        "event_id": new_id(), "user_id": user_id, "action": action,
        "resource_type": resource_type, "resource_id": resource_id,
        "details": details or {}, "ip_address": _mask_ip(ip), "timestamp": utcnow()
    })


def _make_token(user_id: int) -> dict:
    access_token = f"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.mock.{new_id()}"
    refresh_token = f"rt-mock-{new_id()}"
    now = utcnow()
    expires_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    _tokens[refresh_token] = user_id
    _tokens_meta[refresh_token] = {"user_id": user_id, "expires_at": expires_at, "created_at": now}
    _access_token_map[access_token] = user_id
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 3600
    }


# ── Маршруты ─────────────────────────────────────────────────────────────────

@router.post("/api/v1/auth/token", status_code=200)
async def login(req: LoginRequest, request: Request):
    ip = request.client.host if request.client else "127.0.0.1"
    now = utcnow()
    if ip not in _rate_limits:
        _rate_limits[ip] = {"count": 0, "reset_at": now}
    reset_at = datetime.fromisoformat(_rate_limits[ip]["reset_at"])
    if datetime.now(timezone.utc) - reset_at > timedelta(minutes=1):
        _rate_limits[ip] = {"count": 0, "reset_at": now}
    if _rate_limits[ip]["count"] >= 9999:
        raise HTTPException(status_code=429, detail=error_response("TOO_MANY_REQUESTS", "Слишком много запросов"))
    _rate_limits[ip]["count"] += 1

    user = None
    login_value = req.username.strip().lower()
    for u in _users.values():
        user_email = u.get("email", "").lower()
        if user_email == login_value or user_email.split("@")[0] == login_value:
            if _password_hashes.get(u["user_id"]) == _hash_password(req.password):
                user = u
                break
    if not user:
        # AU-3: инкремент failed_attempts по email
        for u in _users.values():
            user_email = u.get("email", "").lower()
            if user_email == login_value or user_email.split("@")[0] == login_value:
                u["failed_attempts"] = u.get("failed_attempts", 0) + 1
                if u["failed_attempts"] >= 5:
                    u["locked_until"] = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
                break
        raise HTTPException(status_code=401, detail=error_response("UNAUTHORIZED", "Неверные учётные данные"))

    # AU-3: проверка блокировки
    locked_until = user.get("locked_until")
    if locked_until:
        try:
            if datetime.fromisoformat(locked_until) > datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=423,
                    detail=error_response("ACCOUNT_LOCKED", "Учётная запись заблокирована на 30 минут из-за множества неудачных попыток входа"),
                )
        except (ValueError, TypeError):
            pass

    if not user.get("is_active", True):
        raise HTTPException(status_code=401, detail=error_response("UNAUTHORIZED", "Пользователь деактивирован"))

    # AU-3: успешный вход — сброс failed_attempts
    user["failed_attempts"] = 0
    user["locked_until"] = None
    user["last_login_at"] = utcnow()
    _add_audit(user["user_id"], "login", "auth", ip=ip)
    return _make_token(user["user_id"])


@router.post("/api/v1/auth/refresh")
async def refresh(req: RefreshRequest):
    if req.refresh_token in _blacklist:
        raise HTTPException(status_code=401, detail=error_response("INVALID_TOKEN", "Токен отозван"))
    rt_meta = _tokens_meta.get(req.refresh_token)
    if rt_meta:
        expires_at = datetime.fromisoformat(rt_meta["expires_at"])
        if datetime.now(timezone.utc) > expires_at:
            _tokens.pop(req.refresh_token, None)
            _tokens_meta.pop(req.refresh_token, None)
            raise HTTPException(status_code=401, detail=error_response("INVALID_TOKEN", "Refresh-токен истёк"))
    user_id = _tokens.get(req.refresh_token)
    if not user_id or user_id not in _users:
        raise HTTPException(status_code=401, detail=error_response("INVALID_TOKEN", "Токен недействителен или истёк"))
    return _make_token(user_id)


@router.post("/api/v1/auth/revoke")
async def revoke(req: RevokeRequest):
    token = req.refresh_token or req.token
    _tokens.pop(token, None)
    _tokens_meta.pop(token, None)
    _blacklist[token] = utcnow()
    return {"message": "Токен отозван", "revoked_at": utcnow()}


@router.get("/api/v1/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    user = current_user
    return {
        "user_id": user["user_id"],
        "full_name": user["full_name"],
        "position": user.get("position", ""),
        "role": user.get("role", user["roles"][0] if user["roles"] else "engineer"),
        "role_title": user.get("role_title", user["roles"][0] if user["roles"] else "Инженер"),
        "available_tabs": user.get("available_tabs", []),
        "permissions": user.get("permissions", {}),
        "last_login_at": user.get("last_login_at", ""),
        "created_at": user.get("created_at", ""),
    }


@router.get("/api/v1/admin/users")
async def list_users(
    role: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    current_user: dict = Depends(require_admin),
):
    items = list(_users.values())
    if role:
        items = [u for u in items if role in u.get("roles", [])]
    if search:
        s = search.lower()
        items = [u for u in items if s in u.get("full_name", "").lower() or s in u.get("email", "").lower()]
    paged = paginate(items, page, page_size)
    return {
        "users": [{
            "user_id": u["user_id"], "email": u.get("email", ""), "full_name": u.get("full_name", ""),
            "position": u.get("position", ""), "roles": u.get("roles", []), "is_active": u.get("is_active", True),
            "last_login_at": u.get("last_login_at", ""), "created_at": u.get("created_at", ""),
        } for u in paged["items"]],
        "meta": paged["meta"],
    }


@router.post("/api/v1/admin/users", status_code=201)
async def create_user(req: CreateUserRequest, current_user: dict = Depends(require_admin)):
    for u in _users.values():
        if u.get("email", "").lower() == req.email.lower():
            raise HTTPException(status_code=409, detail=error_response("DUPLICATE_EMAIL", "Email уже используется"))
    # AU-4: валидация пароля
    _validate_password(req.password)
    user_id = new_id()
    now = utcnow()
    new_user = {
        "user_id": user_id, "id": user_id, "email": req.email, "full_name": req.full_name, "position": "",
        "roles": req.roles, "role": req.roles[0] if req.roles else "engineer",
        "role_title": req.roles[0] if req.roles else "Инженер",
        "is_active": True, "available_tabs": ["chat", "search", "registry", "history"],
        "failed_attempts": 0, "locked_until": None,  # AU-3
        "permissions": {
            "can_upload_documents": False, "can_run_ocr": False, "can_manage_users": False,
            "can_manage_classifiers": False, "can_manage_terminology": False, "can_manage_registry": False,
        },
        "last_login_at": "", "created_at": now, "updated_at": now,
    }
    _users[user_id] = new_user
    _password_hashes[user_id] = _hash_password(req.password)
    _add_audit(current_user["user_id"], "user.create", "user", user_id, {"email": req.email})
    return new_user


@router.get("/api/v1/admin/users/{user_id}")
async def get_user(user_id: int, current_user: dict = Depends(require_admin)):
    user = _users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=error_response("USER_NOT_FOUND", "Пользователь не найден"))
    return {
        "user_id": user["user_id"], "email": user.get("email", ""), "full_name": user.get("full_name", ""),
        "position": user.get("position", ""), "roles": user.get("roles", []),
        "permissions": user.get("permissions", {}) if isinstance(user.get("permissions"), dict) else {},
        "is_active": user.get("is_active", True), "last_login_at": user.get("last_login_at", ""),
        "created_at": user.get("created_at", ""), "updated_at": user.get("updated_at", ""),
    }


@router.put("/api/v1/admin/users/{user_id}")
async def update_user(user_id: int, req: UpdateUserRequest, current_user: dict = Depends(require_admin)):
    user = _users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=error_response("USER_NOT_FOUND", "Пользователь не найден"))
    if req.email is not None:
        user["email"] = req.email
    if req.full_name is not None:
        user["full_name"] = req.full_name
    if req.position is not None:
        user["position"] = req.position
    if req.roles is not None:
        user["roles"] = req.roles
        user["role"] = req.roles[0] if req.roles else "engineer"
    if req.is_active is not None:
        user["is_active"] = req.is_active
    if req.password is not None:
        # AU-4: валидация пароля
        _validate_password(req.password)
        _password_hashes[user_id] = _hash_password(req.password)
        # Revoke all refresh tokens for this user
        revoked_rts = [rt for rt, uid in list(_tokens.items()) if uid == user_id]
        for rt in revoked_rts:
            _tokens.pop(rt, None)
            _tokens_meta.pop(rt, None)
            _blacklist[rt] = utcnow()
        revoked_ats = [at for at, uid in list(_access_token_map.items()) if uid == user_id]
        for at in revoked_ats:
            _access_token_map.pop(at, None)
    if req.is_active is False:
        # Deactivation also revokes tokens
        revoked_rts = [rt for rt, uid in list(_tokens.items()) if uid == user_id]
        for rt in revoked_rts:
            _tokens.pop(rt, None)
            _tokens_meta.pop(rt, None)
            _blacklist[rt] = utcnow()
        revoked_ats = [at for at, uid in list(_access_token_map.items()) if uid == user_id]
        for at in revoked_ats:
            _access_token_map.pop(at, None)
    user["updated_at"] = utcnow()
    _add_audit(current_user["user_id"], "user.update", "user", user_id)
    user["id"] = user["user_id"]
    return user


@router.patch("/api/v1/admin/users/{user_id}")
async def patch_user(user_id: int, req: PatchUserRequest, current_user: dict = Depends(require_admin)):
    user = _users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=error_response("USER_NOT_FOUND", "Пользователь не найден"))
    # AU-5: приоритет roles[] над role
    if req.roles is not None:
        user["roles"] = req.roles
        user["role"] = req.roles[0] if req.roles else "engineer"
    elif req.role is not None:
        user["role"] = req.role
        user["roles"] = [req.role]
    user["updated_at"] = utcnow()
    _add_audit(current_user["user_id"], "user.patch", "user", user_id)
    return {
        "user_id": user["user_id"],
        "role": user.get("role", user["roles"][0] if user["roles"] else ""),
        "roles": user.get("roles", []),
        "updated_at": user["updated_at"],
    }


@router.delete("/api/v1/admin/users/{user_id}")
async def delete_user(user_id: int, current_user: dict = Depends(require_admin)):
    user = _users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=error_response("USER_NOT_FOUND", "Пользователь не найден"))
    user["is_active"] = False
    now = utcnow()
    _add_audit(current_user["user_id"], "user.deactivate", "user", user_id)
    return {"user_id": user["user_id"], "is_active": False, "deactivated_at": now}


@router.get("/api/v1/admin/roles")
async def list_roles(current_user: dict = Depends(require_admin)):
    return {"roles": list(_roles.values())}


@router.post("/api/v1/admin/roles", status_code=201)
async def create_role(req: CreateRoleRequest, current_user: dict = Depends(require_admin)):
    role_id = new_id()
    logger.info("create_role: user=%s body=%s", current_user.get("user_id"), req.model_dump_json())
    new_role = {"role_id": role_id, "name": req.name, "permissions": req.permissions, "created_at": utcnow()}
    _roles[role_id] = new_role
    _add_audit(current_user["user_id"], "role.create", "role", role_id)
    return new_role


@router.get("/api/v1/admin/audit")
async def list_audit(
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(require_admin),
):
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
    return {"events": paged["items"], "meta": paged["meta"]}


@router.post("/api/v1/internal/auth/validate")
async def validate_token(req: ValidateTokenRequest):
    if not req.access_token or len(req.access_token) < 10:
        raise HTTPException(status_code=401, detail=error_response("INVALID_TOKEN", "Токен недействителен или истёк"))
    user_id = _access_token_map.get(req.access_token)
    if not user_id or user_id not in _users:
        raise HTTPException(status_code=401, detail=error_response("INVALID_TOKEN", "Токен недействителен или истёк"))
    user = _users[user_id]
    return {
        "valid": True,
        "user_id": user["user_id"],
        "email": user["email"],
        "roles": user["roles"],
        "permissions": user.get("permissions", {}),
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    }


@router.get("/api/v1/health")
async def health():
    return {"status": "ok", "service": "auth-service", "version": "1.0.0", "uptime_seconds": 86400}
