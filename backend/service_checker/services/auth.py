"""
PKB Neuroassistant — Auth Service API Definitions.

Основано на: docs/api/auth_service_api.md
"""

from __future__ import annotations

from .base import (
    EndpointDef,
    ServiceDef,
    API_PREFIX,
    TEST_CREDENTIALS,
)

SERVICE_KEY = "auth"
PORT = 8082
DISPLAY_NAME = "Auth Service"


def get_service_def() -> ServiceDef:
    """Вернуть полное описание Auth Service."""

    # ── Prepare-эндпоинты (выполняются перед основными) ──────────────
    prepare_endpoints = [
        EndpointDef("POST", f"{API_PREFIX}/auth/token", "auth", "Получение JWT токена",
            body=TEST_CREDENTIALS,
            extract_keys=["access_token", "refresh_token"],
            response_schema={"access_token": str, "refresh_token": str, "token_type": str, "expires_in": int},
            is_preparation=True,
            expected_status=200),
        EndpointDef("GET", f"{API_PREFIX}/auth/me", "auth", "Профиль пользователя",
            # docs/api/auth_service_api.md: user_id, full_name, position, role, role_title, available_tabs, permissions, last_login_at, created_at
            response_schema={"user_id": str, "full_name": str, "role": str, "permissions": dict},
            is_preparation=True,
            expected_status=200),
    ]

    # ── Основные эндпоинты ──────────────────────────────────────────
    endpoints = [
        # Health
        EndpointDef("GET", f"{API_PREFIX}/health", "health", "Health check сервиса",
            response_schema={"status": str, "service": str}),
        EndpointDef("GET", f"{API_PREFIX}/system/health", "health", "System health",
            response_schema={"status": str}),
        # Auth group
        EndpointDef("POST", f"{API_PREFIX}/auth/token", "auth", "Получение JWT токена",
            body=TEST_CREDENTIALS,
            extract_keys=["access_token", "refresh_token"],
            response_schema={"access_token": str, "refresh_token": str, "token_type": str, "expires_in": int}),
        EndpointDef("GET", f"{API_PREFIX}/auth/me", "auth", "Профиль пользователя",
            # docs: user_id, full_name, position, role, role_title, available_tabs, permissions, last_login_at, created_at
            response_schema={"user_id": str, "full_name": str, "role": str, "permissions": dict}),
        EndpointDef("POST", f"{API_PREFIX}/auth/refresh", "auth", "Обновление токена",
            body={"refresh_token": "{refresh_token}"},
            response_schema={"access_token": str, "refresh_token": str}),
        EndpointDef("POST", f"{API_PREFIX}/auth/revoke", "auth", "Отзыв токена",
            body={"refresh_token": "{refresh_token}"},
            # docs: { message, revoked_at }
            response_schema={"message": str, "revoked_at": str}),
        # Admin group
        EndpointDef("GET", f"{API_PREFIX}/admin/users", "admin", "Список пользователей",
            params={"page": 1, "page_size": 10},
            response_schema={"users": list, "meta": dict}),
        EndpointDef("POST", f"{API_PREFIX}/admin/users", "admin", "Создать пользователя",
            body={"email": "test@test.com", "full_name": "Test User", "password": "test123", "roles": ["engineer"]},
            extract_keys=["user_id"],
            response_schema={"id": (int, str), "email": str}),
        EndpointDef("GET", f"{API_PREFIX}/admin/users/{{user_id}}", "admin", "Получить пользователя",
            # docs: { user_id, email, full_name, position, roles, permissions{}, is_active }
            response_schema={"user_id": str, "email": str, "is_active": bool}),
        EndpointDef("PUT", f"{API_PREFIX}/admin/users/{{user_id}}", "admin", "Обновить пользователя",
            body={"email": "updated@test.com", "full_name": "Updated User", "position": "Engineer", "roles": ["engineer"], "is_active": True},
            # docs: { id, email, full_name, roles, is_active, created_at }
            response_schema={"id": (int, str), "email": str, "is_active": bool}),
        EndpointDef("PATCH", f"{API_PREFIX}/admin/users/{{user_id}}", "admin", "Изменить роль",
            body={"role": "admin"},
            # docs: { user_id, roles, audit_log_id, updated_at }
            response_schema={"user_id": str, "roles": list}),
        EndpointDef("DELETE", f"{API_PREFIX}/admin/users/{{user_id}}", "admin", "Деактивировать пользователя",
            # docs: { user_id, is_active, deactivated_at }
            response_schema={"user_id": str, "is_active": bool}),
        EndpointDef("GET", f"{API_PREFIX}/admin/roles", "admin", "Список ролей",
            response_schema={"roles": list}),
        EndpointDef("POST", f"{API_PREFIX}/admin/roles", "admin", "Создать роль",
            body={"name": "viewer", "permissions": {"can_view_documents": True}},
            response_schema={"id": (int, str), "name": str}),
        EndpointDef("GET", f"{API_PREFIX}/admin/audit", "admin", "Журнал аудита",
            params={"page": 1, "page_size": 10},
            # docs: { events[], meta{total, page, page_size} }
            response_schema={"events": list, "meta": dict, "meta.total": int}),
        # Internal
        EndpointDef("POST", f"{API_PREFIX}/internal/auth/validate", "internal", "Валидация токена",
            body={"access_token": "{access_token}"},
            response_schema={"valid": bool}),
    ]

    return ServiceDef(
        service_key=SERVICE_KEY,
        display_name=DISPLAY_NAME,
        port=PORT,
        needs_auth=False,  # токен получаем внутри prepare
        endpoints=endpoints,
        prepare_endpoints=prepare_endpoints,
        depends_on=[],
        base_data={},
    )
