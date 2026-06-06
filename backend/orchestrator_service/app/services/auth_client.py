"""
Auth Service Client with mock mode support.
"""

from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.services.base_client import ServiceClient


class AuthServiceClient(ServiceClient):
    """Client for Auth Service."""

    def __init__(self):
        super().__init__(
            service_name="auth",
            service_url=settings.services.AUTH_SERVICE_URL,
            mock_mode=settings.services.AUTH_SERVICE_MOCK,
        )

    async def _generate_mock(
        self,
        method: str,
        endpoint: str,
        default_mock: Dict[str, Any],
        **kwargs,
    ) -> Dict[str, Any]:
        """Generate mock auth responses."""
        if endpoint == "/auth/token" and method == "POST":
            return {
                "access_token": "mock_access_token_12345",
                "refresh_token": "mock_refresh_token_67890",
                "token_type": "bearer",
                "expires_in": 3600,
            }

        if endpoint == "/auth/refresh" and method == "POST":
            return {
                "access_token": "mock_refreshed_token_54321",
                "refresh_token": "mock_new_refresh_09876",
                "token_type": "bearer",
                "expires_in": 3600,
            }

        if endpoint == "/auth/revoke" and method == "POST":
            return {
                "message": "Токен отозван",
                "revoked_at": "2026-05-05T10:00:00Z",
            }

        if endpoint == "/auth/me" and method == "GET":
            return {
                "user_id": "u-001",
                "full_name": "Иванов Сергей Петрович",
                "position": "Инженер-конструктор",
                "role": "engineer",
                "role_title": "Инженер",
                "available_tabs": ["chat", "search", "checks", "history"],
                "permissions": {
                    "can_upload_documents": False,
                    "can_run_ocr": False,
                    "can_manage_users": False,
                    "can_manage_classifiers": False,
                    "can_manage_terminology": False,
                    "can_manage_registry": False,
                },
                "last_login_at": "2026-05-01T08:20:00Z",
                "created_at": "2025-12-01T08:00:00Z",
            }

        if endpoint == "/admin/roles" and method == "GET":
            return {
                "roles": [
                    {
                        "role_id": "r-engineer",
                        "name": "Инженер",
                        "permissions": ["documents:read", "search"],
                        "created_at": "2025-12-01T08:00:00Z",
                    },
                    {
                        "role_id": "r-admin",
                        "name": "Администратор",
                        "permissions": ["users:manage", "audit:read"],
                        "created_at": "2025-12-01T08:00:00Z",
                    },
                ]
            }

        if endpoint == "/admin/roles" and method == "POST":
            payload = kwargs.get("json", {})
            return {
                "role_id": "r-mock-new",
                "name": payload.get("name", "Новая роль"),
                "permissions": payload.get("permissions", []),
                "created_at": "2026-05-05T10:00:00Z",
                "updated_at": "2026-05-05T10:00:00Z",
            }

        if endpoint == "/admin/audit" and method == "GET":
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
                        "timestamp": "2026-05-05T09:30:00Z",
                    }
                ],
                "meta": {"total": 1, "page": 1, "page_size": 50},
            }

        if endpoint == "/admin/users" and method == "GET":
            return {
                "users": [
                    {
                        "user_id": "u-mock-001",
                        "email": "user1@example.com",
                        "full_name": "Иванов И.И.",
                        "roles": ["engineer"],
                        "is_active": True,
                        "created_at": "2025-12-01T08:00:00Z",
                    }
                ],
                "meta": {"total": 1, "page": 1, "page_size": 50},
            }

        if endpoint == "/admin/users" and method == "POST":
            payload = kwargs.get("json", {})
            return {
                "user_id": "u-mock-new",
                "email": payload.get("email", "new@example.com"),
                "full_name": payload.get("full_name", "Новый Пользователь"),
                "roles": payload.get("roles", ["engineer"]),
                "is_active": True,
                "created_at": "2026-05-05T10:00:00Z",
                "updated_at": "2026-05-05T10:00:00Z",
            }

        if endpoint.startswith("/admin/users/") and method == "GET":
            user_id = endpoint.split("/")[-1]
            return {
                "user_id": user_id,
                "email": f"user_{user_id}@example.com",
                "full_name": "Пользователь",
                "role": "engineer",
                "role_title": "Инженер",
                "position": "Сотрудник",
                "available_tabs": ["chat", "search"],
                "permissions": {
                    "can_upload_documents": True,
                    "can_run_ocr": False,
                    "can_manage_users": False,
                    "can_manage_classifiers": False,
                    "can_manage_terminology": False,
                    "can_manage_registry": False,
                },
                "is_active": True,
                "last_login_at": "2026-05-01T08:20:00Z",
                "created_at": "2025-12-01T08:00:00Z",
                "updated_at": "2026-05-05T10:00:00Z",
            }

        if endpoint.startswith("/admin/users/") and method == "PUT":
            user_id = endpoint.split("/")[-1]
            payload = kwargs.get("json", {})
            return {
                "user_id": user_id,
                "email": payload.get("email", f"user_{user_id}@example.com"),
                "full_name": payload.get("full_name", "Обновлённый Пользователь"),
                "role": payload.get("role", "engineer"),
                "role_title": payload.get("role_title", "Инженер"),
                "position": payload.get("position", "Сотрудник"),
                "available_tabs": payload.get("available_tabs", ["chat", "search"]),
                "permissions": payload.get(
                    "permissions",
                    {
                        "can_upload_documents": True,
                        "can_run_ocr": False,
                        "can_manage_users": False,
                        "can_manage_classifiers": False,
                        "can_manage_terminology": False,
                        "can_manage_registry": False,
                    },
                ),
                "is_active": True,
                "last_login_at": "2026-05-01T08:20:00Z",
                "created_at": "2025-12-01T08:00:00Z",
                "updated_at": "2026-05-05T12:00:00Z",
            }

        if endpoint.startswith("/admin/users/") and method == "PATCH":
            user_id = endpoint.split("/")[-1]
            payload = kwargs.get("json", {})
            merged = {
                "user_id": user_id,
                "email": f"user_{user_id}@example.com",
                "full_name": "Пользователь",
                "role": "engineer",
                "role_title": "Инженер",
                "position": "Сотрудник",
                "available_tabs": ["chat", "search"],
                "permissions": {
                    "can_upload_documents": True,
                    "can_run_ocr": False,
                    "can_manage_users": False,
                    "can_manage_classifiers": False,
                    "can_manage_terminology": False,
                    "can_manage_registry": False,
                },
                "is_active": True,
                "last_login_at": "2026-05-01T08:20:00Z",
                "created_at": "2025-12-01T08:00:00Z",
                "updated_at": "2026-05-05T12:00:00Z",
            }
            merged.update(payload)
            return merged

        if endpoint.startswith("/admin/users/") and method == "DELETE":
            user_id = endpoint.split("/")[-1]
            return {
                "message": f"Пользователь {user_id} деактивирован",
                "user_id": user_id,
                "is_active": False,
                "deactivated_at": "2026-05-05T12:00:00Z",
            }

        if endpoint == "/internal/auth/validate" and method == "POST":
            return {
                "valid": True,
                "user_id": "u-mock-001",
                "email": "user@example.com",
                "roles": ["engineer"],
                "permissions": ["documents:read", "search"],
                "exp": 1714900000,
            }

        return default_mock

    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate access token."""
        return await self.call(
            "POST",
            "/internal/auth/validate",
            mock_response={"valid": True, "user_id": "mock", "roles": []},
            json={"access_token": token},
        )

    async def get_me(self) -> Dict[str, Any]:
        """Get current user profile."""
        return await self.call(
            "GET",
            "/auth/me",
            mock_response={},
        )

    async def list_users(
        self,
        role: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """List users (admin)."""
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        if role:
            params["role"] = role
        if search:
            params["search"] = search
        return await self.call(
            "GET",
            "/admin/users",
            mock_response={
                "users": [],
                "meta": {"total": 0, "page": 1, "page_size": 50},
            },
            params=params,
        )

    async def create_user(
        self, email: str, full_name: str, password: str, roles: List[str]
    ) -> Dict[str, Any]:
        """Create user (admin)."""
        return await self.call(
            "POST",
            "/admin/users",
            mock_response={},
            json={
                "email": email,
                "full_name": full_name,
                "password": password,
                "roles": roles,
            },
        )

    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user details (admin)."""
        return await self.call(
            "GET",
            f"/admin/users/{user_id}",
            mock_response={},
        )

    async def update_user(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user (admin, PUT)."""
        return await self.call(
            "PUT",
            f"/admin/users/{user_id}",
            mock_response={},
            json=data,
        )

    async def patch_user(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Partially update user (admin, PATCH)."""
        return await self.call(
            "PATCH",
            f"/admin/users/{user_id}",
            mock_response={},
            json=data,
        )

    async def deactivate_user(self, user_id: str) -> Dict[str, Any]:
        """Deactivate user (admin)."""
        return await self.call(
            "DELETE",
            f"/admin/users/{user_id}",
            mock_response={},
        )

    async def list_roles(self) -> Dict[str, Any]:
        """List roles."""
        return await self.call(
            "GET",
            "/admin/roles",
            mock_response={"roles": []},
        )

    async def create_role(self, name: str, permissions: List[str]) -> Dict[str, Any]:
        """Create role (admin)."""
        return await self.call(
            "POST",
            "/admin/roles",
            mock_response={},
            json={"name": name, "permissions": permissions},
        )

    async def get_audit_log(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """Get audit log (admin)."""
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        if user_id:
            params["user_id"] = user_id
        if action:
            params["action"] = action
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        return await self.call(
            "GET",
            "/admin/audit",
            mock_response={
                "events": [],
                "meta": {"total": 0, "page": 1, "page_size": 50},
            },
            params=params,
        )
