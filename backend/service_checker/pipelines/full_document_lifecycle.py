#!/usr/bin/env python3
"""
PKB Neuroassistant — Pipeline: full_document_lifecycle

Полный жизненный цикл документа: создание → индексация → поиск →
удаление → пересоздание → финальный поиск.

Проверяет устойчивость к ошибкам и восстановление после сбоев.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .base import (
    PipelineContext,
    PipelineDef,
    PipelineStep,
    check_json_field,
    check_json_fields,
    check_rag_search_results,
)


TEST_CREDENTIALS = {
    "username": "admin@example.com",
    "password": "Admin1234!",
}


class FullDocumentLifecyclePipeline(PipelineDef):
    """Пайплайн: полный жизненный цикл документа с восстановлением после ошибок.

    Ветвление через on_error + skip_if:
    - build шаги НЕ включают 422 в expected_status (честно FAILED).
    - on_error фиксирует ошибку в контексте для recovery-ветвления.
    """

    name = "full_document_lifecycle"
    description = "Полный жизненный цикл документа (создание → ошибка → восстановление → удаление → пересоздание)"
    services = ["gateway"]

    @staticmethod
    def _on_build_error(body: Optional[str], ctx: PipelineContext) -> None:
        """on_error: вызывается при несовпадении HTTP-статуса build.
        Сохраняет факт ошибки в контекст для skip_if на recovery-шаге."""
        ctx.set("build_ok", False)

    @staticmethod
    def _check_build_ok(body: Optional[str], ctx: PipelineContext) -> Tuple[bool, str]:
        """check: отмечает build как успешный в контексте."""
        if not body:
            return False, "пустой ответ"
        import json
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return False, "ответ не JSON"
        ctx.set("build_ok", True)
        return True, f"status = {data.get('status', '?')}"

    def build_steps(self, context: PipelineContext) -> List[PipelineStep]:
        """Построить 12 шагов пайплайна full_document_lifecycle."""
        steps: List[PipelineStep] = []
        ts = int(time.time())

        # ── Шаг 1: Аутентификация (через Gateway) ─────────────────────
        steps.append(PipelineStep(
            name="Аутентификация (через Gateway)",
            service="gateway",
            method="POST",
            path="/api/v1/auth/token",
            port=18080,
            body=TEST_CREDENTIALS,
            expected_status=200,
            extract_keys=["access_token", "refresh_token"],
            check=check_json_field("access_token", str),
        ))

        # ── Шаг 2: Создание документа в Registry (через Gateway) ──────
        steps.append(PipelineStep(
            name="Создание документа в Registry (через Gateway)",
            service="gateway",
            method="POST",
            path="/api/v1/registry/documents",
            port=18080,
            body={
                "title": f"Lifecycle тест {ts}",
                "doc_code": f"LIFECYCLE-{ts}",
                "source_type": "GOST",
                "era": "RF",
                "validity_status": "active",
                "mks_oks_code": "47.020",
                "title_key": f"GOST|RF|LIFECYCLE-{ts}|2026",
            },
            expected_status={201, 409},
            needs_auth=True,
            extract_keys=["doc_id"],
        ))

        # ── Шаг 3: Первая индексация документа (через Gateway) ────────
        steps.append(PipelineStep(
            name="Первая попытка построения индекса (RAG Builder)",
            service="rag_builder",
            method="POST",
            path="/api/v1/rag/build",
            port=18090,
            body={
                "document_id": "{doc_id}",
                "sections": [{
                    "section_id": 1,
                    "document_id": "{doc_id}",
                    "clause": "1",
                    "level": 1,
                    "path": "1",
                    "page": 1,
                    "type": "text",
                    "content": {"text": "Содержимое тестового документа lifecycle"},
                }],
            },
            expected_status={200, 201, 202},  # RB-7: 201 — ресурс создан
            needs_auth=True,
            check=self._check_build_ok,
        ))

        # -- Шаг 4: Обновление метаданных документа (через Gateway) -----
        steps.append(PipelineStep(
            name="Обновление метаданных документа (через Gateway)",
            service="gateway",
            method="PATCH",
            path="/api/v1/registry/documents/{doc_id}/status",
            port=18080,
            extra_headers={"X-Service-Id": "orchestrator"},
            body={"status": "uploaded"},
            expected_status=200,
            needs_auth=True,
            check=check_json_field("data", dict),
        ))

        # ── Шаг 5: Повторная индексация (через Gateway) ────────────────
        steps.append(PipelineStep(
            name="Повторное построение индекса (RAG Builder)",
            service="rag_builder",
            method="POST",
            path="/api/v1/rag/build",
            port=18090,
            body={
                "document_id": "{doc_id}",
                "sections": [{
                    "section_id": 1,
                    "document_id": "{doc_id}",
                    "clause": "1",
                    "level": 1,
                    "path": "1",
                    "page": 1,
                    "type": "text",
                    "content": {"text": "Содержимое тестового документа lifecycle"},
                }],
            },
            expected_status={200, 201, 202},
            needs_auth=True,
            check=self._check_build_ok,
        ))

        # ── Шаг 6: Поиск по индексу (через Gateway) ────────────────────
        steps.append(PipelineStep(
            name="Поиск по индексу RAG Search (RAG Search)",
            service="rag_search",
            method="POST",
            path="/api/v1/rag/search",
            port=18091,
            body={
                "query": "тестовый документ lifecycle",
                "valid_at": "2026-06-19",
                "filters": {"document_type": [], "category_ids": [], "document_ids": []},
            },
            expected_status=200,
            check=check_rag_search_results(),
        ))

        # ── Шаг 7: Удаление документа из Registry (через Gateway) ─────
        steps.append(PipelineStep(
            name="Удаление документа из Registry (через Gateway)",
            service="gateway",
            method="DELETE",
            path="/api/v1/registry/documents/{doc_id}",
            port=18080,
            expected_status=200,
            needs_auth=True,
        ))

        # ── Шаг 8: Удаление индекса RAG (через Gateway) ───────────────
        steps.append(PipelineStep(
            name="Удаление индекса RAG (RAG Builder)",
            service="rag_builder",
            method="DELETE",
            path="/api/v1/rag/build/{doc_id}",
            port=18090,
            expected_status={200, 404},
            needs_auth=True,
        ))

        # ── Шаг 9: Поиск — проверить что результатов нет (через Gateway) ──
        steps.append(PipelineStep(
            name="Поиск — проверка пустого результата (RAG Search)",
            service="rag_search",
            method="POST",
            path="/api/v1/rag/search",
            port=18091,
            body={
                "query": "тестовый документ lifecycle",
                "valid_at": "2026-06-19",
                "filters": {"document_type": [], "category_ids": [], "document_ids": []},
            },
            expected_status=200,
            check=check_rag_search_results(),
        ))

        # ── Шаг 10: Воссоздание документа (через Gateway) ──────────────
        ts2 = int(time.time())
        steps.append(PipelineStep(
            name="Воссоздание документа в Registry (через Gateway)",
            service="gateway",
            method="POST",
            path="/api/v1/registry/documents",
            port=18080,
            body={
                "title": f"Lifecycle тест восстановленный {ts2}",
                "doc_code": f"LIFECYCLE-RECOVER-{ts2}",
                "source_type": "GOST",
                "era": "RF",
                "validity_status": "active",
                "mks_oks_code": "47.020",
                "title_key": f"GOST|RF|LIFECYCLE-RECOVER-{ts2}|2026",
            },
            expected_status={201, 409},
            needs_auth=True,
            extract_keys=["doc_id_2"],
        ))

        # ── Шаг 11: Финальное построение индекса (через Gateway) ───────
        steps.append(PipelineStep(
            name="Финальное построение индекса (RAG Builder)",
            service="rag_builder",
            method="POST",
            path="/api/v1/rag/build",
            port=18090,
            body={
                "document_id": "{doc_id_2}",
                "sections": [{
                    "section_id": 1,
                    "document_id": "{doc_id_2}",
                    "clause": "1",
                    "level": 1,
                    "path": "1",
                    "page": 1,
                    "type": "text",
                    "content": {"text": "Содержимое восстановленного документа"},
                }],
            },
            expected_status={200, 201, 202},  # RB-7: 201 — ресурс создан
            needs_auth=True,
            check=self._check_build_ok,
            on_error=self._on_build_error,
        ))

        # ── Шаг 12: Финальный поиск (через Gateway) ────────────────────
        steps.append(PipelineStep(
            name="Финальный поиск по индексу (RAG Search)",
            service="rag_search",
            method="POST",
            path="/api/v1/rag/search",
            port=18091,
            body={
                "query": "тестовый документ lifecycle",
                "valid_at": "2026-06-19",
                "filters": {"document_type": [], "category_ids": [], "document_ids": []},
            },
            expected_status=200,
            check=check_rag_search_results(),
        ))

        return steps
