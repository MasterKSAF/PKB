from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_token,
    utcnow,
    verify_password,
)
from app.models.models import RefreshToken
from app.services.user_service import get_permissions, get_user_by_email, get_user_by_id, role_names


def authenticate(db: Session, username: str, password: str):
    user = get_user_by_email(db, username)
    if not user or not user.is_active or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверные учетные данные")
    return user


def issue_tokens(db: Session, user):
    roles = role_names(user)
    permissions = get_permissions(user)
    access_token = create_access_token(user.user_id, roles, permissions)

    refresh_token = generate_refresh_token()
    db_token = RefreshToken(
        user_id=user.user_id,
        token_hash=hash_token(refresh_token),
        expires_at=utcnow() + timedelta(seconds=settings.refresh_token_expire_seconds),
    )
    db.add(db_token)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_seconds,
    }


def refresh_access_token(db: Session, refresh_token: str):
    db_token = db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(refresh_token))
    ).scalar_one_or_none()

    if not db_token or db_token.revoked_at is not None or db_token.expires_at < utcnow():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен истек или отозван")

    user = get_user_by_id(db, db_token.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь недоступен")

    return issue_tokens(db, user)


def revoke_refresh_token(db: Session, refresh_token: str):
    db_token = db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(refresh_token))
    ).scalar_one_or_none()

    if not db_token or db_token.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен недействителен")

    db_token.revoked_at = utcnow()
    db.commit()
    db.refresh(db_token)
    return db_token
