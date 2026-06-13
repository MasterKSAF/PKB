from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.schemas.schemas import RefreshRequest, RevokeRequest, RevokeResponse, TokenRequest, TokenResponse, UserPublic
from app.services.audit_service import create_audit_event
from app.services.auth_service import authenticate, issue_tokens, refresh_access_token, revoke_refresh_token
from app.services.user_service import get_permissions, role_names

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserPublic)
async def me(current_user=Depends(get_current_user)):
    return UserPublic(
        user_id=current_user.user_id,
        email=current_user.email,
        full_name=current_user.full_name,
        roles=role_names(current_user),
        permissions=get_permissions(current_user),
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )


@router.post("/token", response_model=TokenResponse)
async def token(payload: TokenRequest, request: Request, db: AsyncSession = Depends(get_db)):
    user = await authenticate(db, payload.username, payload.password)
    tokens = await issue_tokens(db, user)
    await create_audit_event(db, "auth.login", user.user_id, "auth", user.user_id, ip_address=request.client.host if request.client else None)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await refresh_access_token(db, payload.refresh_token)


@router.post("/revoke", response_model=RevokeResponse)
async def revoke(payload: RevokeRequest, request: Request, db: AsyncSession = Depends(get_db)):
    db_token = await revoke_refresh_token(db, payload.refresh_token)
    await create_audit_event(db, "auth.revoke", db_token.user_id, "auth", db_token.token_id, ip_address=request.client.host if request.client else None)
    return {"message": "Токен отозван", "revoked_at": db_token.revoked_at}
