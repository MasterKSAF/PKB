from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.services.user_service import get_user_by_id, get_permissions, role_names


def get_current_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Нет access token")

    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недействительный токен")

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный тип токена")

    user = get_user_by_id(db, payload.get("sub"))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь недоступен")
    return user


def require_permission(permission: str):
    def checker(user = Depends(get_current_user)):
        if permission not in get_permissions(user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
        return user
    return checker


def require_any_permission(permissions: list[str]):
    def checker(user = Depends(get_current_user)):
        user_permissions = set(get_permissions(user))
        if not any(p in user_permissions for p in permissions):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
        return user
    return checker


def user_to_context(user):
    return {
        "user_id": user.user_id,
        "email": user.email,
        "roles": role_names(user),
        "permissions": get_permissions(user),
    }
