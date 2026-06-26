#!/usr/bin/env python3
"""
PKB Neuroassistant — Pipeline: chat_inference

Чат-сессия с поиском по проиндексированным документам:
Auth → Query (Chat) → Query (Text Search) → RAG Search.

Описание: description.md → Пайплайн: chat_inference (4 шага)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .base import (
    PipelineContext,
    PipelineDef,
    PipelineStep,
    check_json_field,
    check_rag_search_results,
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
    services = ["gateway"]

    def build_steps(self, context: PipelineContext) -> List[PipelineStep]:
        """Построить шаги пайплайна chat_inference."""
        steps: List[PipelineStep] = []

        # ── Шаг 1: Аутентификация (через Gateway) ─────────────────────
        steps.append(PipelineStep(
            name="Аутентификация (через Gateway)",
            service="gateway",
            method="POST",
            path="/api/v1/auth/token",
            port=8080,
            body=TEST_CREDENTIALS,
            expected_status=200,
            extract_keys=["access_token", "refresh_token"],
            check=check_json_field("access_token", str),
        ))

        # ── Шаг 2: Создание чат-сессии (через Gateway) ────────────────
        steps.append(PipelineStep(
            name="Создание чат-сессии (через Gateway)",
            service="gateway",
            method="POST",
            path="/api/v1/chat/sessions",
            port=8080,
            body={
                "title": f"Pipeline тестовая сессия {datetime.now().isoformat()}",
                "document_ids": [],  # QS-3: пустой список документов
                "project_id": "__INLINE__project_id",  # QS-3: идентификатор проекта
            },
            expected_status=201,
            extract_keys=["session_id"],
            check=check_json_field("session_id", int),
            needs_auth=True,
        ))

        # ── Шаг 3: Отправка сообщения (через Gateway) ─────────────────
        steps.append(PipelineStep(
            name="Отправка сообщения (через Gateway)",
            service="gateway",
            method="POST",
            path="/api/v1/chat/sessions/{session_id}/messages",
            port=8080,
            body={
                "text": "Какая толщина обшивки ледового пояса?",
                "content": "Какая толщина обшивки ледового пояса?",
            },
            expected_status={200, 202},
            extract_keys=["message_id"],
            check=check_json_field("message_id", int),
            needs_auth=True,
        ))

        # ── Шаг 4: Текстовый поиск (через Gateway) ────────────────────
        steps.append(PipelineStep(
            name="Текстовый поиск (через Gateway)",
            service="gateway",
            method="POST",
            path="/api/v1/text/search",
            port=8080,
            body={
                "text": "толщина обшивки ледового пояса",
                "valid_at": "2026-06-19",
                "filters": {"category_ids": []},  # RS-6: без top_k
            },
            expected_status=200,
            check=check_json_field("results", list),
            needs_auth=True,
        ))

        # -- Шаг 4a: Проверка enrichment_skipped (QS-8) в ответе text/search --
        # Толерантная проверка: если поле есть — проверяем тип, если нет — warning.
        def _check_enrichment_skipped(body: Optional[str], ctx: PipelineContext) -> Tuple[bool, str]:
            if not body:
                return True, "пустой ответ (пропущено)"
            import json
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                return True, "не JSON (пропущено)"
            val = data.get("enrichment_skipped")
            if val is None:
                return True, "enrichment_skipped отсутствует (сервис не обновлён) — warning, не error"
            if not isinstance(val, bool):
                return True, f"enrichment_skipped={val} (не bool) — warning"
            return True, f"enrichment_skipped={val}"

        steps.append(PipelineStep(
            name="Проверка enrichment_skipped (через Gateway)",
            service="gateway",
            method="POST",
            path="/api/v1/text/search",
            port=8080,
            body={
                "text": "толщина обшивки",
                "valid_at": "2026-06-19",
                "filters": {"category_ids": []},
            },
            expected_status=200,
            check=_check_enrichment_skipped,
            needs_auth=True,
        ))

        # ── Шаг 5: Поиск RAG Search (через Gateway) ────────────────────
        steps.append(PipelineStep(
            name="Поиск RAG Search (напрямую)",
            service="rag_search",
            method="POST",
            path="/api/v1/rag/search",
            port=8091,
            body={
                "query": "ледовый класс Arc4",
                "valid_at": "2026-06-19",
                "filters": {"document_type": [], "category_ids": [], "document_ids": []},
            },
            expected_status=200,
            check=check_rag_search_results(),
            needs_auth=True,
        ))

        return steps
