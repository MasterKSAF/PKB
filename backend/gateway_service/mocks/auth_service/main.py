import copy
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(title="Auth Service", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_counter = 0
def new_id() -> str:
    global _counter
    _counter += 1
    return str(_counter)

def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

def error_response(code: str, message: str, details: dict = None) -> JSONResponse:
    status_map = {
        "VALIDATION_ERROR": 400, "UNAUTHORIZED": 401, "INVALID_TOKEN": 401,
        "FORBIDDEN": 403, "USER_NOT_FOUND": 404, "DUPLICATE_EMAIL": 409,
        "INTERNAL_ERROR": 500, "TOO_MANY_REQUESTS": 429,
    }
    return JSONResponse(
        status_code=status_map.get(code, 400),
        content={"error": {"code": code, "message": message, "details": details or {}}}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, JSONResponse):
        return exc.detail
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc.detail)})

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return error_response("VALIDATION_ERROR", "Некорректные входные данные", {"errors": exc.errors()})

def paginate(items: list, page: int, page_size: int) -> dict:
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return {"items": items[start:end], "meta": {"total": total, "page": page, "page_size": page_size}}

SEED_USERS = [
    {"user_id":"u-001","email":"ivanov@example.com","full_name":"Иванов Иван Иванович","password":"secret123","position":"Инженер-конструктор","roles":["engineer"],"is_active":True,"available_tabs":["chat","search","checks","history"],"permissions":{"can_upload_documents":False,"can_run_ocr":False,"can_manage_users":False,"can_manage_classifiers":False,"can_manage_terminology":False,"can_manage_registry":False},"last_login_at":"","created_at":"2025-12-01T08:00:00Z"},
    {"user_id":"u-002","email":"petrova@example.com","full_name":"Петрова Анна Викторовна","password":"secret456","position":"Администратор НСИ","roles":["knowledge_admin"],"is_active":True,"available_tabs":["chat","search","checks","history","registry","documents"],"permissions":{"can_upload_documents":True,"can_run_ocr":True,"can_manage_users":False,"can_manage_classifiers":True,"can_manage_terminology":True,"can_manage_registry":True},"last_login_at":"","created_at":"2025-11-15T10:00:00Z"},
    {"user_id":"u-003","email":"admin@example.com","full_name":"Сидоров Павел Алексеевич","password":"admin123","position":"Системный администратор","roles":["system_admin"],"is_active":True,"available_tabs":["chat","search","checks","history","registry","documents","admin","monitor"],"permissions":{"can_upload_documents":True,"can_run_ocr":True,"can_manage_users":True,"can_manage_classifiers":True,"can_manage_terminology":True,"can_manage_registry":True},"last_login_at":"","created_at":"2025-10-01T08:00:00Z"},
    {"user_id":"u-004","email":"kuznetsov@example.com","full_name":"Кузнецов Дмитрий Олегович","password":"secret789","position":"Инженер-технолог","roles":["engineer"],"is_active":True,"available_tabs":["chat","search","checks","history"],"permissions":{"can_upload_documents":False,"can_run_ocr":False,"can_manage_users":False,"can_manage_classifiers":False,"can_manage_terminology":False,"can_manage_registry":False},"last_login_at":"","created_at":"2026-01-10T09:00:00Z"},
    {"user_id":"u-005","email":"smirnova@example.com","full_name":"Смирнова Елена Игоревна","password":"secret000","position":"Ведущий инженер","roles":["engineer"],"is_active":False,"available_tabs":["chat","search","checks","history"],"permissions":{"can_upload_documents":True,"can_run_ocr":True,"can_manage_users":False,"can_manage_classifiers":False,"can_manage_terminology":False,"can_manage_registry":False},"last_login_at":"","created_at":"2025-12-20T08:00:00Z"},
]
SEED_ROLES = [
    {"role_id":"r-engineer","name":"Инженер","permissions":["documents:read","search"],"created_at":"2025-12-01T08:00:00Z"},
    {"role_id":"r-knowledge-admin","name":"Администратор НСИ","permissions":["documents:read","documents:write","search","classifiers:manage","terminology:manage","registry:manage"],"created_at":"2025-12-01T08:00:00Z"},
    {"role_id":"r-system-admin","name":"Системный администратор","permissions":["documents:read","documents:write","documents:delete","search","classifiers:manage","terminology:manage","registry:manage","users:manage","roles:manage","audit:read"],"created_at":"2025-12-01T08:00:00Z"},
]
SEED_AUDIT = [
    {"event_id":"evt-001","user_id":"u-001","action":"document.upload","resource_type":"document","resource_id":"doc-001","details":{"filename":"spec_ГОСТ_2.109.pdf"},"ip_address":"192.168.1.25","timestamp":"2026-04-27T09:30:00Z"},
]

_users: Dict[str, dict] = {}
_roles: Dict[str, dict] = {}
_audit: list = []
_tokens: Dict[str, str] = {}
_tokens_meta: Dict[str, dict] = {}
_access_token_map: Dict[str, str] = {}
_blacklist: Dict[str, str] = {}
_password_hashes: Dict[str, str] = {}
_rate_limits: Dict[str, dict] = {}

def init_data():
    global _users, _roles, _audit, _tokens, _tokens_meta, _password_hashes, _rate_limits, _access_token_map
    _users = {u["user_id"]: copy.deepcopy(u) for u in SEED_USERS}
    _roles = {r["role_id"]: copy.deepcopy(r) for r in SEED_ROLES}
    _audit = copy.deepcopy(SEED_AUDIT)
    _rate_limits = {}
    _access_token_map = {}
    for u in SEED_USERS:
        _password_hashes[u["user_id"]] = hashlib.sha256(u["password"].encode()).hexdigest()
    now = utcnow()
    expires_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    for uid in _users:
        rt = f"rt-mock-{uid}"
        _tokens[rt] = uid
        _tokens_meta[rt] = {"user_id": uid, "expires_at": expires_at, "created_at": now}

init_data()

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
    roles: List[str]

class UpdateUserRequest(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    position: Optional[str] = None
    roles: Optional[List[str]] = None
    is_active: Optional[bool] = None

class PatchUserRequest(BaseModel):
    role: Optional[str] = None
    roles: Optional[List[str]] = None

class CreateRoleRequest(BaseModel):
    name: str
    permissions: List[str]

class ValidateTokenRequest(BaseModel):
    access_token: str

def _hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def _add_audit(user_id: str, action: str, resource_type: str, resource_id: str = "",
               details: dict = None, ip: str = "127.0.0.1"):
    _audit.append({
        "event_id": f"evt-{new_id()}", "user_id": user_id, "action": action,
        "resource_type": resource_type, "resource_id": resource_id,
        "details": details or {}, "ip_address": ip, "timestamp": utcnow()
    })

def _make_token(user_id: str) -> dict:
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

@app.post("/api/v1/auth/token", status_code=200)
async def login(req: LoginRequest, request: Request):
    ip = request.client.host if request.client else "127.0.0.1"
    now = utcnow()
    if ip not in _rate_limits:
        _rate_limits[ip] = {"count": 0, "reset_at": now}
    reset_at = datetime.fromisoformat(_rate_limits[ip]["reset_at"])
    if datetime.now(timezone.utc) - reset_at > timedelta(minutes=1):
        _rate_limits[ip] = {"count": 0, "reset_at": now}
    if _rate_limits[ip]["count"] >= 5:
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
        raise HTTPException(status_code=401, detail=error_response("UNAUTHORIZED", "Неверные учётные данные"))
    if not user.get("is_active", True):
        raise HTTPException(status_code=401, detail=error_response("UNAUTHORIZED", "Пользователь деактивирован"))
    user["last_login_at"] = utcnow()
    _add_audit(user["user_id"], "login", "auth", ip=ip)
    return _make_token(user["user_id"])

@app.post("/api/v1/auth/refresh")
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

@app.post("/api/v1/auth/revoke")
async def revoke(req: RevokeRequest):
    _tokens.pop(req.refresh_token, None)
    _tokens_meta.pop(req.refresh_token, None)
    _blacklist[req.refresh_token] = utcnow()
    return {"message": "Токен отозван", "revoked_at": utcnow()}

@app.get("/api/v1/auth/me")
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

@app.get("/api/v1/admin/users")
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

@app.post("/api/v1/admin/users", status_code=201)
async def create_user(req: CreateUserRequest, current_user: dict = Depends(require_admin)):
    for u in _users.values():
        if u.get("email", "").lower() == req.email.lower():
            raise HTTPException(status_code=409, detail=error_response("DUPLICATE_EMAIL", "Email уже используется"))
    user_id = f"u-{new_id()}"
    now = utcnow()
    new_user = {
        "user_id": user_id, "email": req.email, "full_name": req.full_name, "position": "",
        "roles": req.roles, "role": req.roles[0] if req.roles else "engineer",
        "role_title": req.roles[0] if req.roles else "Инженер",
        "is_active": True, "available_tabs": ["chat","search","checks","history"],
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

@app.get("/api/v1/admin/users/{user_id}")
async def get_user(user_id: str, current_user: dict = Depends(require_admin)):
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

@app.put("/api/v1/admin/users/{user_id}")
async def update_user(user_id: str, req: UpdateUserRequest, current_user: dict = Depends(require_admin)):
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
        user["role"] = req.roles[0] if req.roles else user["role"]
    if req.is_active is not None:
        user["is_active"] = req.is_active
    user["updated_at"] = utcnow()
    _add_audit(current_user["user_id"], "user.update", "user", user_id)
    return user

@app.patch("/api/v1/admin/users/{user_id}")
async def patch_user(user_id: str, req: PatchUserRequest, current_user: dict = Depends(require_admin)):
    user = _users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=error_response("USER_NOT_FOUND", "Пользователь не найден"))
    audit_log_id = f"audit-{new_id()}"
    if req.role is not None:
        user["role"] = req.role
        user["roles"] = [req.role]
    if req.roles is not None:
        user["roles"] = req.roles
        user["role"] = req.roles[0] if req.roles else user["role"]
    user["updated_at"] = utcnow()
    _add_audit(current_user["user_id"], "user.patch", "user", user_id)
    return {
        "user_id": user["user_id"],
        "role": user.get("role", user["roles"][0] if user["roles"] else ""),
        "audit_log_id": audit_log_id,
        "updated_at": user["updated_at"],
    }

@app.delete("/api/v1/admin/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(require_admin)):
    user = _users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=error_response("USER_NOT_FOUND", "Пользователь не найден"))
    user["is_active"] = False
    now = utcnow()
    _add_audit(current_user["user_id"], "user.deactivate", "user", user_id)
    return {"user_id": user["user_id"], "is_active": False, "deactivated_at": now}

@app.get("/api/v1/admin/roles")
async def list_roles(current_user: dict = Depends(require_admin)):
    return {"roles": list(_roles.values())}

@app.post("/api/v1/admin/roles", status_code=201)
async def create_role(req: CreateRoleRequest, current_user: dict = Depends(require_admin)):
    role_id = f"r-{new_id()}"
    new_role = {"role_id": role_id, "name": req.name, "permissions": req.permissions, "created_at": utcnow()}
    _roles[role_id] = new_role
    _add_audit(current_user["user_id"], "role.create", "role", role_id)
    return new_role

@app.get("/api/v1/admin/audit")
async def list_audit(
    user_id: Optional[str] = Query(None),
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

@app.post("/api/v1/internal/auth/validate")
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

@app.get("/api/v1/system/health")
async def health():
    return {"status": "ok", "service": "auth-service", "timestamp": utcnow()}

if __name__ == "__main__":
    import os
    port = int(os.getenv("AUTH_SERVICE_PORT", "8082"))
    uvicorn.run(app, host="0.0.0.0", port=port)