from datetime import timedelta, timezone

from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import api_error
from app.core.logger import get_logger
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_token,
    utcnow,
    verify_password,
)
from app.models.models import RefreshToken
from app.services.user_service import get_permissions, get_user_by_email, get_user_by_id, role_names

logger = get_logger(__name__)


async def authenticate(db: AsyncSession, username: str, password: str):
    user = await get_user_by_email(db, username)

    if not user or not user.is_active:
        logger.warning("Failed login for unknown or inactive user: %s", username)
        api_error(status.HTTP_401_UNAUTHORIZED, "INVALID_CREDENTIALS", "Неверные учётные данные")

    # Check if account is locked
    now = utcnow()
    if user.locked_until is not None:
        locked_until = user.locked_until
        if locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=timezone.utc)
        if locked_until > now:
            retry_after = int((locked_until - now).total_seconds()) + 1
            logger.warning("Locked account login attempt: %s", username)
            api_error(
                status.HTTP_401_UNAUTHORIZED,
                "ACCOUNT_LOCKED",
                "Аккаунт заблокирован после нескольких неудачных попыток входа",
                {"retry_after_seconds": retry_after},
            )

    if not verify_password(password, user.password_hash):
        user.failed_attempts = (user.failed_attempts or 0) + 1
        if user.failed_attempts >= settings.max_failed_attempts:
            user.locked_until = now + timedelta(seconds=settings.lockout_duration_seconds)
            await db.commit()
            retry_after = settings.lockout_duration_seconds
            logger.warning(
                "Account locked after %d failed attempts: %s", user.failed_attempts, username
            )
            api_error(
                status.HTTP_401_UNAUTHORIZED,
                "ACCOUNT_LOCKED",
                "Аккаунт заблокирован после нескольких неудачных попыток входа",
                {"retry_after_seconds": retry_after},
            )
        await db.commit()
        logger.warning("Failed login attempt %d for user: %s", user.failed_attempts, username)
        api_error(status.HTTP_401_UNAUTHORIZED, "INVALID_CREDENTIALS", "Неверные учётные данные")

    # Successful login — reset brute-force counters
    user.failed_attempts = 0
    user.locked_until = None
    await db.commit()
    logger.info("User logged in: %s", username)
    return user


async def issue_tokens(db: AsyncSession, user):
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
    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_seconds,
    }


async def refresh_access_token(db: AsyncSession, refresh_token: str):
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(refresh_token))
    )
    db_token = result.scalar_one_or_none()

    if not db_token:
        logger.warning("Refresh token not found")
        api_error(status.HTTP_401_UNAUTHORIZED, "INVALID_TOKEN", "Токен истёк или отозван")

    expires_at = db_token.expires_at
    if expires_at is None:
        api_error(status.HTTP_401_UNAUTHORIZED, "INVALID_TOKEN", "Токен не содержит срока действия")
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if db_token.revoked_at is not None or expires_at < utcnow():
        logger.warning("Refresh token expired or revoked for user: %s", db_token.user_id)
        api_error(status.HTTP_401_UNAUTHORIZED, "INVALID_TOKEN", "Токен истёк или отозван")

    user = await get_user_by_id(db, db_token.user_id)
    if not user or not user.is_active:
        logger.warning("User unavailable during token refresh: %s", db_token.user_id)
        api_error(status.HTTP_401_UNAUTHORIZED, "INVALID_TOKEN", "Пользователь недоступен")

    return await issue_tokens(db, user)


async def revoke_refresh_token(db: AsyncSession, refresh_token: str):
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(refresh_token))
    )
    db_token = result.scalar_one_or_none()

    if not db_token or db_token.revoked_at is not None:
        logger.warning("Attempt to revoke invalid or already revoked token")
        api_error(status.HTTP_401_UNAUTHORIZED, "INVALID_TOKEN", "Токен недействителен")

    db_token.revoked_at = utcnow()
    await db.commit()
    await db.refresh(db_token)
    logger.info("Refresh token revoked for user: %s", db_token.user_id)
    return db_token
