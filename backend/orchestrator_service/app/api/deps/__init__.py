"""
Auth dependencies — Bearer token validation.

Uses the Auth Service client to validate tokens.
In mock mode, returns a mock user without real validation.
"""

from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.services.auth_client import AuthServiceClient

security = HTTPBearer(auto_error=False)

# Paths that never require authentication
PUBLIC_PATH_PREFIXES = (
    "/auth/",
    "/system/health",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
)


class CurrentUser:
    """Represents an authenticated user."""

    def __init__(
        self,
        user_id: str,
        email: str,
        full_name: str,
        roles: list[str],
        permissions: list[str],
    ):
        self.user_id = user_id
        self.email = email
        self.full_name = full_name
        self.roles = roles
        self.permissions = permissions


MOCK_USER = CurrentUser(
    user_id="u-mock-001",
    email="user@example.com",
    full_name="Иванов И.И.",
    roles=["engineer"],
    permissions=[
        "documents:read",
        "documents:write",
        "documents:delete",
        "search",
        "validate",
    ],
)


def _skip_auth_paths(path: str) -> bool:
    """Return True if the path does NOT require authentication."""
    return any(path.startswith(p) for p in PUBLIC_PATH_PREFIXES)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[CurrentUser]:
    """
    Dependency that extracts and validates the current user.

    - Public paths (``/auth/*``, ``/system/health``, swagger docs) skip
      authentication entirely.
    - In mock mode (``AUTH_SERVICE_MOCK=true``), returns the mock user
      without checking the token.
    - In real mode, validates the Bearer token with the Auth Service.
    """
    # Public paths → no auth needed
    if _skip_auth_paths(request.url.path):
        return None

    # Mock mode → return mock user without real validation
    if settings.services.AUTH_SERVICE_MOCK:
        return MOCK_USER

    # Require credentials for non-public endpoints
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Требуется авторизация — предоставьте Bearer токен",
                    "details": {},
                }
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Validate token with Auth Service
    client = AuthServiceClient()
    try:
        result = await client.validate_token(token)
        if not result.get("valid"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "INVALID_TOKEN",
                        "message": "Токен недействителен или истёк",
                        "details": {},
                    }
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        return CurrentUser(
            user_id=result.get("user_id", "unknown"),
            email=result.get("email", ""),
            full_name=result.get("full_name", ""),
            roles=result.get("roles", []),
            permissions=result.get("permissions", []),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": {
                    "code": "AUTH_SERVICE_UNAVAILABLE",
                    "message": "Сервис аутентификации временно недоступен",
                    "details": {"original_error": str(exc)},
                }
            },
        )
    finally:
        await client.close()
