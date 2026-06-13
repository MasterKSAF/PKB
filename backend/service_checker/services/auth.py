"""
PKB Neuroassistant — Auth Service API Definitions.

Основано на: docs/api/auth_service_api.md
"""

from __future__ import annotations
import time

from .base import (
    EndpointDef,
    ServiceDef,
    API_PREFIX,
    TEST_CREDENTIALS,
)

SERVICE_KEY = "auth"
PORT = 8082
DISPLAY_NAME = "Auth Service"

_ts = str(int(time.time()))[-6:]


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
        # Создаём уникального пользователя для тестов {user_id} эндпоинтов
        EndpointDef("POST", f"{API_PREFIX}/admin/users", "admin", "Создать пользователя (prepare)",
            body={"email": f"prepare-user-{_ts}@test.com", "full_name": "Prepare User", "password": "Test1234!", "roles": ["engineer"]},
            extract_keys=["user_id"],
            response_schema={"id": int, "email": str},
            is_preparation=True,
            expected_status={201, 409}),
    ]

    # ── Основные эндпоинты ──────────────────────────────────────────
    endpoints = [
        # Health
        EndpointDef("GET", f"{API_PREFIX}/health", "health", "Health check сервиса",
            response_schema={"status": str, "service": str}),
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
            body={"email": "test@test.com", "full_name": "Test User", "password": "Test1234!", "roles": ["engineer"]},
            extract_keys=["user_id"],
            expected_status={201, 409},
            response_schema={"id": int, "email": str}),
        EndpointDef("GET", f"{API_PREFIX}/admin/users/{{user_id}}", "admin", "Получить пользователя",
            # docs: { user_id, email, full_name, position, roles, permissions{}, is_active }
            response_schema={"user_id": str, "email": str, "is_active": bool}),
        EndpointDef("PUT", f"{API_PREFIX}/admin/users/{{user_id}}", "admin", "Обновить пользователя",
            body={"full_name": "Updated User", "position": "Engineer", "roles": ["engineer"], "is_active": True},
            # docs: { id, email, full_name, roles, is_active, created_at } — auth возвращает user_id str
            response_schema={"user_id": str, "email": str, "is_active": bool}),
        EndpointDef("PATCH", f"{API_PREFIX}/admin/users/{{user_id}}", "admin", "Изменить роль",
            body={"role": "admin"},
            # docs: { user_id, roles, audit_log_id, updated_at }
            response_schema={"user_id": str, "roles": list}),
        EndpointDef("DELETE", f"{API_PREFIX}/admin/users/{{user_id}}", "admin", "Деактивировать пользователя",
            expected_status={200, 307},
            # docs: { user_id, is_active, deactivated_at }
            response_schema={"user_id": str, "is_active": bool}),
        EndpointDef("GET", f"{API_PREFIX}/admin/roles", "admin", "Список ролей",
            response_schema={"roles": list}),
        EndpointDef("POST", f"{API_PREFIX}/admin/roles", "admin", "Создать роль",
            body={"name": "viewer", "permissions": ["documents:read", "search"]},
            expected_status={201, 409},
            response_schema={"id": int, "name": str}),
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
