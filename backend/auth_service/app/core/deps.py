from fastapi import Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import api_error
from app.core.security import decode_token
from app.db.session import get_db
from app.services.user_service import get_permissions, get_user_by_id, role_names


async def get_current_user(authorization: str | None = Header(default=None), db: AsyncSession = Depends(get_db)):
    if not authorization or not authorization.lower().startswith("bearer "):
        api_error(status.HTTP_401_UNAUTHORIZED, "INVALID_TOKEN", "Отсутствует access token")

    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_token(token)
    except Exception:
        api_error(status.HTTP_401_UNAUTHORIZED, "INVALID_TOKEN", "Токен недействителен или истёк")

    if payload.get("type") != "access":
        api_error(status.HTTP_401_UNAUTHORIZED, "INVALID_TOKEN", "Неверный тип токена")

    user = await get_user_by_id(db, payload.get("sub"))
    if not user or not user.is_active:
        api_error(status.HTTP_401_UNAUTHORIZED, "INVALID_TOKEN", "Пользователь недоступен")
    return user


def require_permission(permission: str):
    async def checker(user=Depends(get_current_user)):
        if permission not in get_permissions(user):
            api_error(status.HTTP_403_FORBIDDEN, "FORBIDDEN", "Недостаточно прав")
        return user
    return checker


def require_any_permission(permissions: list[str]):
    async def checker(user=Depends(get_current_user)):
        user_permissions = set(get_permissions(user))
        if not any(p in user_permissions for p in permissions):
            api_error(status.HTTP_403_FORBIDDEN, "FORBIDDEN", "Недостаточно прав")
        return user
    return checker


def user_to_context(user):
    return {
        "user_id": user.user_id,
        "email": user.email,
        "roles": role_names(user),
        "permissions": get_permissions(user),
    }
