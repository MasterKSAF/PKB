from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.schemas.schemas import InternalValidateRequest, InternalValidateResponse
from app.services.user_service import get_permissions, get_user_by_id, role_names

router = APIRouter(prefix="/internal/auth", tags=["internal"])


@router.post("/validate", response_model=InternalValidateResponse)
def validate(payload: InternalValidateRequest, db: Session = Depends(get_db)):
    try:
        decoded = decode_token(payload.access_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен недействителен")

    if decoded.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный тип токена")

    user = get_user_by_id(db, decoded.get("sub"))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь недоступен")

    return {
        "valid": True,
        "user_id": user.user_id,
        "email": user.email,
        "roles": role_names(user),
        "permissions": get_permissions(user),
        "exp": decoded["exp"],
    }
