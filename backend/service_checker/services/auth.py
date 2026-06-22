"""
PKB Neuroassistant — Auth Service API Definitions.

Основано на: docs/api/auth_service_api.md
Обновления (19.06.2026):
- AU-5: PATCH /admin/users/{id} — role → roles[] (массив)
- AU-2: ROLES таблица, GET /admin/roles
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

    _warnings: list = []

    # docs/api/auth_service_api.md: PATCH /admin/users/{id} ожидает audit_log_id в ответе,
    # но сервис пока не возвращает это поле
    _warnings.append(
        "PATCH /admin/users/{id}: docs ожидает audit_log_id, но сервис его не возвращает"
    )

    prepare_endpoints = [
        EndpointDef("POST", f"{API_PREFIX}/auth/token", "auth", "Получение JWT токена",
            body=TEST_CREDENTIALS,
            extract_keys=["access_token", "refresh_token"],
            response_schema={"access_token": str, "refresh_token": str, "token_type": str, "expires_in": int},
            is_preparation=True,
            expected_status=200),
        EndpointDef("GET", f"{API_PREFIX}/auth/me", "auth", "Профиль пользователя",
            response_schema={"user_id": str, "full_name": str, "role": str, "permissions": dict},
            is_preparation=True,
            expected_status=200),
        EndpointDef("POST", f"{API_PREFIX}/admin/users", "admin", "Создать пользователя (prepare)",
            body={"email": f"prepare-user-{_ts}@test.com", "full_name": "Prepare User",
                  "password": "Test1234!", "roles": ["engineer"]},
            extract_keys=["user_id"],
            response_schema={"user_id": str, "email": str},
            is_preparation=True,
            expected_status={201, 409}),
        # AU-5: создаём роль knowledge_admin для PATCH (per docs)
        EndpointDef("POST", f"{API_PREFIX}/admin/roles", "admin", "Создать роль knowledge_admin",
            body={"name": "knowledge_admin", "permissions": ["documents:read", "documents:write", "users:manage", "roles:manage", "audit:read", "search"]},
            expected_status={201, 409},
            response_schema={"role_id": str, "name": str},
            is_preparation=True),
    ]

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
            response_schema={"user_id": str, "full_name": str, "role": str, "permissions": dict}),
        EndpointDef("POST", f"{API_PREFIX}/auth/refresh", "auth", "Обновление токена",
            body={"refresh_token": "{refresh_token}"},
            response_schema={"access_token": str, "refresh_token": str}),
        EndpointDef("POST", f"{API_PREFIX}/auth/revoke", "auth", "Отзыв токена",
            body={"refresh_token": "{refresh_token}"},
            response_schema={"message": str, "revoked_at": str}),
        # Admin group
        EndpointDef("GET", f"{API_PREFIX}/admin/users", "admin", "Список пользователей",
            params={"page": 1, "page_size": 10},
            response_schema={"users": list, "meta": dict}),
        EndpointDef("POST", f"{API_PREFIX}/admin/users", "admin", "Создать пользователя",
            body={"email": "test@test.com", "full_name": "Test User", "password": "Test1234!", "roles": ["engineer"]},
            extract_keys=["user_id"],
            expected_status={201, 409},
            response_schema={"user_id": str, "email": str}),
        EndpointDef("GET", f"{API_PREFIX}/admin/users/{{user_id}}", "admin", "Получить пользователя",
            response_schema={"user_id": str, "email": str, "is_active": bool}),
        EndpointDef("PUT", f"{API_PREFIX}/admin/users/{{user_id}}", "admin", "Обновить пользователя",
            body={"full_name": "Updated User", "position": "Engineer", "roles": ["engineer"], "is_active": True},
            response_schema={"user_id": str, "email": str, "is_active": bool}),
        # AU-5: roles[] вместо role (per docs: knowledge_admin)
        # docs: ожидается audit_log_id, но сервис пока не возвращает
        EndpointDef("PATCH", f"{API_PREFIX}/admin/users/{{user_id}}", "admin", "Изменить роли",
            body={"roles": ["knowledge_admin"]},
            response_schema={"user_id": str, "roles": list, "updated_at": str}),
        EndpointDef("DELETE", f"{API_PREFIX}/admin/users/{{user_id}}", "admin", "Деактивировать пользователя",
            expected_status={200, 307},
            response_schema={"user_id": str, "is_active": bool}),
        # AU-2: ROLES таблица
        EndpointDef("GET", f"{API_PREFIX}/admin/roles", "admin", "Список ролей",
            response_schema={"roles": list}),
        EndpointDef("POST", f"{API_PREFIX}/admin/roles", "admin", "Создать роль",
            body={"name": "viewer", "permissions": ["documents:read", "search"]},
            expected_status={201, 409},
            response_schema={"role_id": str, "name": str}),
        EndpointDef("GET", f"{API_PREFIX}/admin/audit", "admin", "Журнал аудита",
            params={"page": 1, "page_size": 10},
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
        needs_auth=False,
        endpoints=endpoints,
        prepare_endpoints=prepare_endpoints,
        depends_on=[],
        base_data={},
        warnings=_warnings,
    )
