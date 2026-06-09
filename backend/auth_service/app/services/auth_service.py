from datetime import timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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


async def authenticate(db: AsyncSession, username: str, password: str):
    user = await get_user_by_email(db, username)
    if not user or not user.is_active or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="РќРµРІРµСЂРЅС‹Рµ СѓС‡РµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ")
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

    expires_at = db_token.expires_at.replace(tzinfo=timezone.utc) if db_token and db_token.expires_at.tzinfo is None else db_token.expires_at
    if not db_token or db_token.revoked_at is not None or expires_at < utcnow():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="РўРѕРєРµРЅ РёСЃС‚РµРє РёР»Рё РѕС‚РѕР·РІР°РЅ")

    user = await get_user_by_id(db, db_token.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ РЅРµРґРѕСЃС‚СѓРїРµРЅ")

    return await issue_tokens(db, user)


async def revoke_refresh_token(db: AsyncSession, refresh_token: str):
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(refresh_token))
    )
    db_token = result.scalar_one_or_none()

    if not db_token or db_token.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="РўРѕРєРµРЅ РЅРµРґРµР№СЃС‚РІРёС‚РµР»РµРЅ")

    db_token.revoked_at = utcnow()
    await db.commit()
    await db.refresh(db_token)
    return db_token

