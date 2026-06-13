"""
Auth dependencies — always returns mock user.
No external auth service is used.
"""

from typing import Optional

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

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
    Dependency that returns the current user.

    - Public paths (``/system/health``, swagger docs) skip authentication.
    - Always returns the mock user (no external auth service).
    """
    # Public paths → no auth needed
    if _skip_auth_paths(request.url.path):
        return None

    return MOCK_USER
