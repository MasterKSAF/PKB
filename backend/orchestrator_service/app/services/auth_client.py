"""
Auth Service Client with mock mode support.
"""
from typing import Any, Dict, List, Optional
from app.services.base_client import ServiceClient
from app.core.config import settings


class AuthServiceClient(ServiceClient):
    """Client for Auth Service."""
    
    def __init__(self):
        super().__init__(
            service_name="auth",
            service_url=settings.services.AUTH_SERVICE_URL,
            mock_mode=settings.services.AUTH_SERVICE_MOCK
        )
    
    async def _generate_mock(
        self,
        method: str,
        endpoint: str,
        default_mock: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Generate mock auth responses."""
        if endpoint == "/auth/token" and method == "POST":
            return {
                "access_token": "mock_access_token_12345",
                "refresh_token": "mock_refresh_token_67890",
                "token_type": "bearer",
                "expires_in": 3600
            }
        
        if endpoint == "/auth/refresh" and method == "POST":
            return {
                "access_token": "mock_refreshed_token_54321",
                "refresh_token": "mock_new_refresh_09876",
                "token_type": "bearer",
                "expires_in": 3600
            }
        
        if endpoint == "/auth/revoke" and method == "POST":
            return {
                "message": "Токен отозван",
                "revoked_at": "2026-05-05T10:00:00Z"
            }
        
        if endpoint == "/users/me" and method == "GET":
            return {
                "user_id": "u-mock-001",
                "email": "user@example.com",
                "full_name": "Иванов И.И.",
                "roles": ["engineer"],
                "permissions": ["documents:read", "search"],
                "created_at": "2025-12-01T08:00:00Z"
            }
        
        if endpoint.startswith("/users/") and method == "GET":
            user_id = endpoint.split("/")[-1]
            return {
                "user_id": user_id,
                "email": f"user_{user_id}@example.com",
                "full_name": "Пользователь",
                "roles": ["engineer"],
                "permissions": ["documents:read", "search"],
                "is_active": True,
                "created_at": "2025-12-01T08:00:00Z",
                "updated_at": "2026-05-05T10:00:00Z"
            }
        
        if endpoint == "/users" and method == "GET":
            return {
                "users": [
                    {
                        "user_id": "u-mock-001",
                        "email": "user1@example.com",
                        "full_name": "Иванов И.И.",
                        "roles": ["engineer"],
                        "is_active": True,
                        "created_at": "2025-12-01T08:00:00Z"
                    }
                ],
                "total": 1,
                "limit": 20,
                "offset": 0
            }
        
        if endpoint == "/users" and method == "POST":
            return {
                "user_id": "u-mock-new",
                "email": kwargs.get("json", {}).get("email", "new@example.com"),
                "full_name": kwargs.get("json", {}).get("full_name", "Новый Пользователь"),
                "roles": kwargs.get("json", {}).get("roles", ["engineer"]),
                "permissions": ["documents:read", "search"],
                "is_active": True,
                "created_at": "2026-05-05T10:00:00Z",
                "updated_at": "2026-05-05T10:00:00Z"
            }
        
        if endpoint == "/roles" and method == "GET":
            return {
                "roles": [
                    {
                        "role_id": "r-engineer",
                        "name": "Инженер",
                        "permissions": ["documents:read", "search"],
                        "created_at": "2025-12-01T08:00:00Z"
                    },
                    {
                        "role_id": "r-admin",
                        "name": "Администратор",
                        "permissions": ["users:manage", "audit:read"],
                        "created_at": "2025-12-01T08:00:00Z"
                    }
                ]
            }
        
        if endpoint == "/audit" and method == "GET":
            return {
                "events": [
                    {
                        "event_id": "evt-mock-001",
                        "user_id": "u-mock-001",
                        "action": "document.upload",
                        "resource_type": "document",
                        "resource_id": "doc-mock-001",
                        "details": {"filename": "spec.pdf"},
                        "ip_address": "192.168.1.1",
                        "timestamp": "2026-05-05T09:30:00Z"
                    }
                ],
                "total": 1
            }
        
        if endpoint == "/internal/auth/validate" and method == "POST":
            return {
                "valid": True,
                "user_id": "u-mock-001",
                "email": "user@example.com",
                "roles": ["engineer"],
                "permissions": ["documents:read", "search"],
                "exp": 1714900000
            }
        
        return default_mock
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate access token."""
        return await self.call(
            "POST",
            "/internal/auth/validate",
            mock_response={"valid": True, "user_id": "mock", "roles": []},
            json={"access_token": token}
        )
