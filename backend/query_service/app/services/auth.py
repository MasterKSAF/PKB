from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..config import get_settings

bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> str:
    settings = get_settings()
    user_id = request.headers.get("X-User-ID")
    if user_id:
        return user_id
    if settings.DEV_AUTH_MODE:
        return settings.DEV_USER_ID
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization required")
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="X-User-ID header required")
