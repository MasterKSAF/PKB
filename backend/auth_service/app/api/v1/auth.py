import time
from collections import defaultdict

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user
from app.core.errors import api_error
from app.db.session import get_db
from app.schemas.schemas import RefreshRequest, RevokeRequest, RevokeResponse, TokenRequest, TokenResponse, UserMeResponse, UserPermissions
from app.services.audit_service import create_audit_event
from app.services.auth_service import authenticate, issue_tokens, refresh_access_token, revoke_refresh_token
from app.services.user_service import get_permissions, role_names

router = APIRouter(prefix="/auth", tags=["auth"])

_rate_buckets: dict[str, list[float]] = defaultdict(list)

_ROLE_TITLES = {
    "engineer": "Инженер-конструктор",
    "knowledge_admin": "Администратор НСИ",
    "system_admin": "Системный администратор",
}

_ROLE_TABS = {
    "engineer": ["chat", "search", "history"],
    "knowledge_admin": ["chat", "search", "history"],
    "system_admin": ["chat", "search", "history"],
}


def _check_rate_limit(client_ip: str) -> tuple[bool, int]:
    now = time.time()
    cutoff = now - settings.rate_limit_window_seconds
    bucket = _rate_buckets[client_ip]
    while bucket and bucket[0] < cutoff:
        bucket.pop(0)
    if len(bucket) >= settings.rate_limit_requests:
        retry_after = int(bucket[0] + settings.rate_limit_window_seconds - now) + 1
        return False, retry_after
    bucket.append(now)
    return True, 0


def _to_bool_permissions(string_permissions: list[str]) -> UserPermissions:
    perms = set(string_permissions)
    return UserPermissions(
        can_upload_documents="documents:write" in perms,
        can_run_ocr=False,
        can_manage_users="users:manage" in perms,
        can_manage_classifiers=False,
        can_manage_terminology=False,
        can_manage_registry=False,
    )


@router.get("/me", response_model=UserMeResponse)
async def me(current_user=Depends(get_current_user)):
    role = role_names(current_user)[0] if current_user.roles else ""
    string_permissions = get_permissions(current_user)
    return UserMeResponse(
        user_id=current_user.user_id,
        full_name=current_user.full_name,
        role=role,
        role_title=_ROLE_TITLES.get(role, role),
        available_tabs=_ROLE_TABS.get(role, []),
        permissions=_to_bool_permissions(string_permissions),
        last_login_at=None,
        created_at=current_user.created_at,
    )


@router.post("/token", response_model=TokenResponse)
async def token(payload: TokenRequest, request: Request, db: AsyncSession = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    allowed, retry_after = _check_rate_limit(client_ip)
    if not allowed:
        api_error(
            429,
            "RATE_LIMIT_EXCEEDED",
            "Слишком много запросов. Повторите позже.",
            {"retry_after_seconds": retry_after},
        )

    user = await authenticate(db, payload.username, payload.password)
    tokens = await issue_tokens(db, user)
    await create_audit_event(
        db, "auth.login", user.user_id, "auth", user.user_id,
        ip_address=client_ip,
    )
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await refresh_access_token(db, payload.refresh_token)


@router.post("/revoke", response_model=RevokeResponse)
async def revoke(payload: RevokeRequest, request: Request, db: AsyncSession = Depends(get_db)):
    db_token = await revoke_refresh_token(db, payload.refresh_token)
    await create_audit_event(
        db, "auth.revoke", db_token.user_id, "auth", db_token.token_id,
        ip_address=request.client.host if request.client else None,
    )
    return {"message": "Токен отозван", "revoked_at": db_token.revoked_at}
