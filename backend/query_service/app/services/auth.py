from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..config import get_settings

bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> str:
    settings = get_settings()
    if settings.DEV_AUTH_MODE:
        return settings.DEV_USER_ID
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization required")
    # TODO: JWT-валидация через auth-сервис
    return settings.DEV_USER_ID
