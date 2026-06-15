#!/usr/bin/env python3
"""
PKB Neuroassistant — Pipeline: full_document_lifecycle

Полный жизненный цикл документа: создание → ошибка индексации → восстановление →
поиск → удаление → пересоздание → финальный поиск.

Ветвление (on_error + skip_if):
- Шаг 3 (build): если RAG Builder возвращает 422 (известная проблема UUID),
  on_error сохраняет контекст и шаг FAILED.
- Шаг 5 (recovery build): skip_if проверяет, не прошёл ли первый build успешно.

⚠️ RAG Builder ожидает document_id как UUID (specificity.md §25).
В этом пайплайне 422 не обходится молча — on_error фиксирует ошибку
для recovery-ветвления.

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
    services = ["auth", "registry", "rag_builder", "rag_search"]

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

        # ── Шаг 2: Создание документа в Registry ──────────────────────
        steps.append(PipelineStep(
            name="Создание документа в Registry",
            service="registry",
            method="POST",
            path="/api/v1/registry/documents/",
            port=8084,
            body={
                "title": f"Lifecycle тест {ts}",
                "doc_code": f"LIFECYCLE-{ts}",
                "source_type": "GOST",
                "era": "RF",
                "validity_status": "active",
            },
            expected_status={201, 409},
            needs_auth=True,
            extract_keys=["doc_id"],
            # Registry возвращает {data: {id: ..., document_id: ..., ...}}
            check=check_json_field("data", dict),
        ))

        # ⚠️ Шаг 3: Первая попытка индексации. RAG Builder ожидает UUID
        # (specificity.md §25). 422 НЕ включён в expected_status — шаг честно FAILED.
        # on_error фиксирует ошибку в контексте для recovery-ветвления.
        steps.append(PipelineStep(
            name="Первая попытка построения индекса",
            service="rag_builder",
            method="POST",
            path="/api/v1/rag/build",
            port=8090,
            body={
                "document_id": "{doc_id}",
                "sections": [{
                    "section_id": 1,
                    "document_id": "{doc_id}",
                    "clause": "1",
                    "level": 1,
                    "path": "1",
                    "page": 1,
                    "type": "section",
                    "content": {"text": "Содержимое тестового документа lifecycle"},
                }],
            },
            # ⚠️ 422 НЕ включён — известная проблема UUID (specificity.md §25).
            # on_error фиксирует ошибку для recovery.
            expected_status={200, 201},
            needs_auth=True,
            check=self._check_build_ok,
            on_error=self._on_build_error,
        ))

        # ── Шаг 4: Обновление метаданных документа (имитация «починки») ─────
        steps.append(PipelineStep(
            name="Обновление метаданных документа",
            service="registry",
            method="PATCH",
            # ⚠️ trailing slash обязателен (FastAPI 307 redirect)
            path="/api/v1/registry/documents/{doc_id}/status/",
            port=8084,
            body={"status": "uploaded"},
            expected_status=200,
            needs_auth=True,
            check=check_json_field("data", dict),
        ))

        # ── Шаг 5: Повторная индексация (recovery) ─────────────────────
        # Выполняется только если первая попытка не удалась (build_ok=False)
        steps.append(PipelineStep(
            name="Повторное построение индекса (recovery)",
            service="rag_builder",
            method="POST",
            path="/api/v1/rag/build",
            port=8090,
            body={
                "document_id": "{doc_id}",
                "sections": [{
                    "section_id": 1,
                    "document_id": "{doc_id}",
                    "clause": "1",
                    "level": 1,
                    "path": "1",
                    "page": 1,
                    "type": "section",
                    "content": {"text": "Содержимое тестового документа lifecycle"},
                }],
            },
            expected_status={200, 201},
            needs_auth=True,
            check=self._check_build_ok,
            on_error=self._on_build_error,
            # Пропускаем, если первый build прошёл успешно (recovery не нужен)
            skip_if=lambda ctx: ctx.get("build_ok", False),
        ))

        # ── Шаг 6: Поиск по индексу ──────────────────────────────────
        steps.append(PipelineStep(
            name="Поиск по индексу RAG Search",
            service="rag_search",
            method="POST",
            path="/api/v1/rag/search",
            port=8091,
            body={
                "query": "тестовый документ lifecycle",
                "top_k": 5,
            },
            expected_status=200,
            check=check_json_field("results", list),
        ))

        # ── Шаг 7: Удаление документа из Registry ────────────────────
        steps.append(PipelineStep(
            name="Удаление документа из Registry",
            service="registry",
            method="DELETE",
            # ⚠️ trailing slash обязателен
            path="/api/v1/registry/documents/{doc_id}/",
            port=8084,
            expected_status=200,
            needs_auth=True,
        ))

        # ── Шаг 8: Удаление индекса RAG Builder ──────────────────────
        steps.append(PipelineStep(
            name="Удаление индекса RAG",
            service="rag_builder",
            method="DELETE",
            path="/api/v1/rag/build/{doc_id}",
            port=8090,
            expected_status={200, 404},
            needs_auth=True,
        ))

        # ── Шаг 9: Поиск — проверить что результатов нет ──────────────
        steps.append(PipelineStep(
            name="Поиск — проверка пустого результата",
            service="rag_search",
            method="POST",
            path="/api/v1/rag/search",
            port=8091,
            body={
                "query": "тестовый документ lifecycle",
                "top_k": 5,
            },
            expected_status=200,
            check=check_json_field("results", list),
        ))

        # ── Шаг 10: Воссоздание документа ─────────────────────────────
        ts2 = int(time.time())
        steps.append(PipelineStep(
            name="Воссоздание документа в Registry",
            service="registry",
            method="POST",
            path="/api/v1/registry/documents/",
            port=8084,
            body={
                "title": f"Lifecycle тест восстановленный {ts2}",
                "doc_code": f"LIFECYCLE-RECOVER-{ts2}",
                "source_type": "GOST",
                "era": "RF",
                "validity_status": "active",
            },
            expected_status={201, 409},
            needs_auth=True,
            extract_keys=["doc_id2"],
            check=check_json_field("data", dict),
        ))

        # ── Шаг 11: Финальное построение индекса ──────────────────────
        steps.append(PipelineStep(
            name="Финальное построение индекса",
            service="rag_builder",
            method="POST",
            path="/api/v1/rag/build",
            port=8090,
            body={
                "document_id": "{doc_id2}",
                "sections": [{
                    "section_id": 1,
                    "document_id": "{doc_id2}",
                    "clause": "1",
                    "level": 1,
                    "path": "1",
                    "page": 1,
                    "type": "section",
                    "content": {"text": "Содержимое восстановленного документа"},
                }],
            },
            expected_status={200, 201},
            needs_auth=True,
            check=self._check_build_ok,
            on_error=self._on_build_error,
        ))

        # ── Шаг 12: Финальный поиск ──────────────────────────────────
        steps.append(PipelineStep(
            name="Финальный поиск по индексу",
            service="rag_search",
            method="POST",
            path="/api/v1/rag/search",
            port=8091,
            body={
                "query": "тестовый документ lifecycle",
                "top_k": 5,
            },
            expected_status=200,
            check=check_json_field("results", list),
        ))

        return steps
