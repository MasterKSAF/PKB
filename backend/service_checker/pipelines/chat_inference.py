#!/usr/bin/env python3
"""
PKB Neuroassistant — Pipeline: chat_inference

Чат-сессия с поиском по проиндексированным документам:
Auth → Query (Chat) → Query (Text Search) → RAG Search.

Описание: description.md → Пайплайн: chat_inference (4 шага)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pipelines.base import (
    PipelineContext,
    PipelineDef,
    PipelineStep,
    check_json_field,
)

# Тестовые учётные данные (admin — создаётся auth-сервисом при старте)
TEST_CREDENTIALS = {
    "username": "admin@example.com",
    "password": "Admin1234!",
}


class ChatInferencePipeline(PipelineDef):
    """Пайплайн чат-сессии: аутентификация → чат → текстовый поиск → гибридный поиск."""

    name = "chat_inference"
    description = "Чат-сессия с поиском по проиндексированным документам"
    services = ["auth", "query", "rag_search"]

    def build_steps(self, context: PipelineContext) -> List[PipelineStep]:
        """Построить шаги пайплайна chat_inference."""
        steps: List[PipelineStep] = []

        # ── Шаг 1: Аутентификация ────────────────────────────────────
        steps.append(PipelineStep(
            name="Аутентификация",
            service="auth",
            method="POST",
            path="/api/v1/auth/token",
            port=8082,
            body=TEST_CREDENTIALS,
            expected_status=200,
            extract_keys=["access_token", "refresh_token"],
            check=check_json_field("access_token", str),
        ))

        # ── Шаг 2: Создание чат-сессии ───────────────────────────────
        steps.append(PipelineStep(
            name="Создание чат-сессии",
            service="query",
            method="POST",
            path="/api/v1/chat/sessions",
            port=8083,
            body={"title": f"Pipeline тестовая сессия {datetime.now().isoformat()}"},
            expected_status=201,
            extract_keys=["session_id"],
            check=check_json_field("session_id", (int, str)),
            needs_auth=True,
        ))

        # ── Шаг 3: Отправка сообщения ────────────────────────────────
        steps.append(PipelineStep(
            name="Отправка сообщения",
            service="query",
            method="POST",
            path="/api/v1/chat/sessions/{session_id}/messages",
            port=8083,
            body={
                "text": "Какая толщина обшивки ледового пояса?",
                "content": "Какая толщина обшивки ледового пояса?",
            },
            expected_status={200, 202},
            extract_keys=["message_id"],
            check=check_json_field("message_id", (int, str)),
            needs_auth=True,
        ))

        # ── Шаг 4: Текстовый поиск ───────────────────────────────────
        steps.append(PipelineStep(
            name="Текстовый поиск",
            service="query",
            method="POST",
            path="/api/v1/text/search",
            port=8083,
            body={
                "text": "толщина обшивки ледового пояса",
                "top_k": 5,
            },
            expected_status=200,
            check=check_json_field("results", list),
            needs_auth=True,
        ))

        # ── Шаг 5: Гибридный поиск RAG Search ────────────────────────
        steps.append(PipelineStep(
            name="Гибридный поиск RAG Search",
            service="rag_search",
            method="POST",
            path="/api/v1/rag/search",
            port=8091,
            body={
                "query": "ледовый класс Arc4",
                "top_k": 5,
            },
            expected_status=200,
            check=check_json_field("results", list),
            needs_auth=True,
        ))

        return steps
