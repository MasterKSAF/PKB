from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.schemas import RefreshRequest, RevokeRequest, RevokeResponse, TokenRequest, TokenResponse
from app.services.audit_service import create_audit_event
from app.services.auth_service import authenticate, issue_tokens, refresh_access_token, revoke_refresh_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=TokenResponse)
def token(payload: TokenRequest, request: Request, db: Session = Depends(get_db)):
    user = authenticate(db, payload.username, payload.password)
    tokens = issue_tokens(db, user)
    create_audit_event(db, "auth.login", user.user_id, "auth", user.user_id, ip_address=request.client.host if request.client else None)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    return refresh_access_token(db, payload.refresh_token)


@router.post("/revoke", response_model=RevokeResponse)
def revoke(payload: RevokeRequest, request: Request, db: Session = Depends(get_db)):
    db_token = revoke_refresh_token(db, payload.refresh_token)
    create_audit_event(db, "auth.revoke", db_token.user_id, "auth", db_token.token_id, ip_address=request.client.host if request.client else None)
    return {"message": "Токен отозван", "revoked_at": db_token.revoked_at}
