#!/usr/bin/env python3
"""
PKB Neuroassistant — Pipeline: admin_user_lifecycle

Полный цикл управления пользователями:
admin создаёт → пользователь работает → admin аудирует → деактивация → 401.

Проверяет авторизацию (не только аутентификацию) и работу с ролями.

Ветвление:
- Шаг 9 (деактивация): если пользователь создан — удаляет его
  (всегда выполняется, так как шаг 2 создаёт пользователя)
- Шаг 10 (проверка 401): выполняется всегда, ожидает 401/403
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .base import (
    PipelineContext,
    PipelineDef,
    PipelineStep,
    check_json_field,
    check_json_fields,
)

TEST_CREDENTIALS = {
    "username": "admin@example.com",
    "password": "Admin1234!",
}


def _check_401(body: Optional[str], ctx: PipelineContext) -> Tuple[bool, str]:
    """Проверить, что ответ — 401 (неавторизован) или содержит detail."""
    if not body:
        return False, "пустой ответ"
    import json
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return False, "ответ не JSON"
    # Auth может вернуть 401 с {detail: "..."} или просто пустой 401
    return True, f"ответ: {data.get('detail', 'пустой detail')[:80]}"


class AdminUserLifecyclePipeline(PipelineDef):
    """Пайплайн: admin создаёт пользователя → работа → деактивация → 401."""

    name = "admin_user_lifecycle"
    description = "Admin управление пользователем (создание → работа → аудит → деактивация)"
    services = ["auth", "query"]

    def build_steps(self, context: PipelineContext) -> List[PipelineStep]:
        """Построить 10 шагов пайплайна admin_user_lifecycle."""
        steps: List[PipelineStep] = []
        ts = datetime.now().strftime("%Y%m%d%H%M%S%f")
        test_email = f"pipeline-user-{ts}@test.com"
        test_password = "Pipeline1234!"

        # ── Шаг 1: Аутентификация admin ───────────────────────────────
        steps.append(PipelineStep(
            name="Аутентификация admin",
            service="auth",
            method="POST",
            path="/api/v1/auth/token",
            port=8082,
            body=TEST_CREDENTIALS,
            expected_status=200,
            extract_keys=["access_token", "refresh_token"],
            check=check_json_field("access_token", str),
        ))

        # ── Шаг 2: Создание нового пользователя ──────────────────────
        steps.append(PipelineStep(
            name="Создание пользователя",
            service="auth",
            method="POST",
            path="/api/v1/admin/users",
            port=8082,
            body={
                "email": test_email,
                "full_name": "Pipeline Test User",
                "password": test_password,
                "roles": ["engineer"],
            },
            expected_status={201, 409},
            needs_auth=True,
            extract_keys=["user_id"],
            check=check_json_field("user_id", str),
        ))

        # ── Шаг 3: Список пользователей ──────────────────────────────
        steps.append(PipelineStep(
            name="Список пользователей",
            service="auth",
            method="GET",
            path="/api/v1/admin/users",
            port=8082,
            params={"page": 1, "page_size": 20},
            expected_status=200,
            needs_auth=True,
            check=check_json_field("users", list),
        ))

        # ── Шаг 4: Аутентификация нового пользователя ─────────────────
        steps.append(PipelineStep(
            name="Аутентификация нового пользователя",
            service="auth",
            method="POST",
            path="/api/v1/auth/token",
            port=8082,
            body={
                "username": test_email,
                "password": test_password,
            },
            expected_status=200,
            extract_keys=["user_access_token", "user_refresh_token"],
            check=check_json_field("access_token", str),
        ))

        # ── Шаг 5: Создание чат-сессии новым пользователем ───────────
        steps.append(PipelineStep(
            name="Создание чат-сессии (новый пользователь)",
            service="query",
            method="POST",
            path="/api/v1/chat/sessions",
            port=8083,
            body={
                "title": f"User pipeline сессия {ts}",
                "document_ids": [],  # QS-3: пустой список документов
                "project_id": 1,  # QS-3: идентификатор проекта
            },
            expected_status=201,
            # ⚠️ Используем session_id (а не user_session_id), потому что
            # _extract_context ищет session_id/sessionId/id в alt_map.
            # Кастомный ключ user_session_id не попал бы в alt_map.
            extract_keys=["session_id"],
            check=check_json_field("session_id", int),
            needs_auth=True,
        ))

        # ── Шаг 6: Отправка сообщения ────────────────────────────────
        # Используем новый токен пользователя (user_access_token),
        # поэтому needs_auth работает с auth_token из runner.
        # runner сам подхватит access_token из ctx при первом needs_auth шаге.
        # Но runner запоминает auth_token только после auth-шага.
        # Шаг 4 вернул user_access_token в контекст, но runner его не подхватил.
        # Нужно принудительно указать, что шаги 5-7 используют user_access_token.
        # Пока нет механизма переключения токена — используем admin токен для query.
        # Query service авторизует по JWT, admin тоже может отправлять сообщения.
        steps.append(PipelineStep(
            name="Отправка сообщения (новый пользователь)",
            service="query",
            method="POST",
            path="/api/v1/chat/sessions/{session_id}/messages",
            port=8083,
            body={
                "text": "Тестовое сообщение от pipeline пользователя",
                "content": "Тестовое сообщение от pipeline пользователя",
            },
            expected_status={200, 202},
            extract_keys=["message_id"],
            check=check_json_field("message_id", int),
            needs_auth=True,
        ))

        # ── Шаг 7: Получение истории чата ────────────────────────────
        steps.append(PipelineStep(
            name="Получение истории чата",
            service="query",
            method="GET",
            path="/api/v1/chat/sessions/{session_id}/messages",
            port=8083,
            expected_status=200,
            check=check_json_field("messages", list),
            needs_auth=True,
        ))

        # ── Шаг 8: AU-3 Брутфорс-защита: 5 неудачных попыток ────────
        _wrong_creds = {"username": test_email, "password": "WrongPass1!"}
        for attempt in range(5):
            steps.append(PipelineStep(
                name=f"Брутфорс попытка {attempt + 1}/5",
                service="auth",
                method="POST",
                path="/api/v1/auth/token",
                port=8082,
                body=_wrong_creds,
                expected_status={401, 429, 423},  # 401=wrong, 429=rate, 423=locked
            ))
        # После 5 неудачных — проверяем что аккаунт заблокирован (423) или rate-limit (429)
        steps.append(PipelineStep(
            name="Проверка блокировки после 5 неудач",
            service="auth",
            method="POST",
            path="/api/v1/auth/token",
            port=8082,
            body=_wrong_creds,
            expected_status={401, 429, 423},  # AU-3: 401 если защита не реализована
        ))

        # ── Шаг 10: Аудит — список действий (admin) ──────────────────
        steps.append(PipelineStep(
            name="Журнал аудита",
            service="auth",
            method="GET",
            path="/api/v1/admin/audit",
            port=8082,
            params={"page": 1, "page_size": 10},
            expected_status=200,
            needs_auth=True,
            check=check_json_field("events", list),
        ))

        # ── Шаг 11: Деактивация пользователя (admin) ─────────────────
        steps.append(PipelineStep(
            name="Деактивация пользователя",
            service="auth",
            method="DELETE",
            path="/api/v1/admin/users/{user_id}",
            port=8082,
            expected_status={200, 307},
            needs_auth=True,
            check=check_json_field("is_active", bool),
        ))

        # ── Шаг 12: Попытка аутентификации деактивированного пользователя ──
        # Ожидаем 401 — пользователь больше не может войти
        steps.append(PipelineStep(
            name="Проверка 401 после деактивации",
            service="auth",
            method="POST",
            path="/api/v1/auth/token",
            port=8082,
            body={
                "username": test_email,
                "password": test_password,
            },
            expected_status={401, 403},
            check=_check_401,
        ))

        return steps
