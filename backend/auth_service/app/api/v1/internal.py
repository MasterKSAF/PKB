from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import api_error
from app.core.logger import get_logger
from app.core.security import decode_token
from app.db.session import get_db
from app.schemas.schemas import InternalValidateRequest, InternalValidateResponse
from app.services.user_service import get_permissions, get_user_by_id, role_names

router = APIRouter(prefix="/internal/auth", tags=["internal"])
logger = get_logger(__name__)


@router.post("/validate", response_model=InternalValidateResponse)
async def validate(payload: InternalValidateRequest, db: AsyncSession = Depends(get_db)):
    try:
        decoded = decode_token(payload.access_token)
    except Exception:
        logger.warning("Invalid access token presented to /internal/auth/validate")
        api_error(status.HTTP_401_UNAUTHORIZED, "INVALID_TOKEN", "Токен недействителен или истёк")

    if decoded.get("type") != "access":
        logger.warning("Wrong token type at /internal/auth/validate: %s", decoded.get("type"))
        api_error(status.HTTP_401_UNAUTHORIZED, "INVALID_TOKEN", "Неверный тип токена")

    user = await get_user_by_id(db, decoded.get("sub"))
    if not user or not user.is_active:
        logger.warning("User unavailable during token validation: %s", decoded.get("sub"))
        api_error(status.HTTP_401_UNAUTHORIZED, "INVALID_TOKEN", "Пользователь недоступен")

    return {
        "valid": True,
        "user_id": user.user_id,
        "email": user.email,
        "roles": role_names(user),
        "permissions": get_permissions(user),
        "exp": decoded["exp"],
    }
