#!/usr/bin/env python3
"""
PKB Neuroassistant — Pipeline: orchestrator_full_document_lifecycle

Полный сквозной цикл документа через Orchestrator: от черновика до удаления.

Проверяет: создание → preview → approve → Registry → RAG Builder → RAG Search → удаление.
Весь путь проходит через Orchestrator как единую точку входа.
"""

from __future__ import annotations

from datetime import datetime
from json import JSONDecodeError
from pathlib import Path
from typing import List, Optional, Tuple

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

_HERE = Path(__file__).resolve().parent.parent
TEST_PDF_PATH = _HERE / "pdf" / "7bd97d737317a8a272bb18a405ab2d04.pdf"
TEST_PDF_BYTES = TEST_PDF_PATH.read_bytes()


def _on_draft_failed(body: Optional[str], ctx: PipelineContext) -> None:
    ctx.set("draft_failed", True)


def _draft_skipped(ctx: PipelineContext) -> bool:
    return ctx.get("draft_failed", False)


class OrchestratorFullDocumentLifecyclePipeline(PipelineDef):
    """Пайплайн: полный цикл документа через Orchestrator — от черновика до удаления."""

    name = "orchestrator_full_document_lifecycle"
    description = "Полный сквозной цикл документа через Orchestrator (создание → preview → approve → Registry → индексация → удаление)"
    services = ["auth", "orchestrator", "registry", "rag_builder", "rag_search"]

    def build_steps(self, context: PipelineContext) -> List[PipelineStep]:
        steps: List[PipelineStep] = []
        ts = datetime.now().strftime("%Y%m%d%H%M%S%f")

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

        # ── Шаг 2: Создание черновика ────────────────────────────────
        pdf_name = f"fullcycle-draft-{ts}.pdf"
        steps.append(PipelineStep(
            name="Создание черновика",
            service="orchestrator",
            method="POST",
            path="/api/v1/drafts/",
            port=8081,
            form_body={
                "document_key": f"fullcycle-key-{ts}",
                "title": f"FullCycle тест {ts}",
                "source_type": "GOST",
            },
            form_files={
                "file": (pdf_name, TEST_PDF_BYTES, "application/pdf"),
            },
            expected_status={202, 409},
            extract_keys=["draft_id", "task_id"],
            check=check_json_field("draft_id", int),
            needs_auth=True,
            on_error=_on_draft_failed,
        ))

        # ── Шаг 3: Статус задачи ─────────────────────────────────────
        steps.append(PipelineStep(
            name="Статус задачи (longpoll)",
            service="orchestrator",
            method="GET",
            path="/api/v1/tasks/{task_id}/status",
            port=8081,
            expected_status=200,
            check=check_json_field("status", str),
            needs_auth=True,
            skip_if=_draft_skipped,
        ))

        # ── Шаг 4: Детали черновика ──────────────────────────────────
        steps.append(PipelineStep(
            name="Детали черновика",
            service="orchestrator",
            method="GET",
            path="/api/v1/drafts/{draft_id}",
            port=8081,
            expected_status=200,
            check=check_json_fields({
                "draft_id": int,
                "document_id": (int, type(None)),
                "version_id": (int, type(None)),
                "is_new_document": bool,
            }),
            needs_auth=True,
            skip_if=_draft_skipped,
        ))

        # ── Шаг 5: Запуск превью ─────────────────────────────────────
        steps.append(PipelineStep(
            name="Запуск превью черновика",
            service="orchestrator",
            method="POST",
            path="/api/v1/drafts/{draft_id}/preview",
            port=8081,
            body={},
            expected_status={200, 202, 404},
            needs_auth=True,
            skip_if=_draft_skipped,
        ))

        # ── Шаг 6: Статус превью ─────────────────────────────────────
        steps.append(PipelineStep(
            name="Статус превью",
            service="orchestrator",
            method="GET",
            path="/api/v1/drafts/{draft_id}/preview/status",
            port=8081,
            params={"longpoll": 1},
            expected_status={200, 404},
            needs_auth=True,
            skip_if=_draft_skipped,
        ))

        # ── Шаг 7: Approve ───────────────────────────────────────────
        def _on_approved(body: Optional[str], ctx: PipelineContext) -> Tuple[bool, str]:
            """Извлечь document_id из ответа approve и сохранить как approved_doc_id."""
            if not body:
                return True, "no body"
            try:
                import json
                data = json.loads(body)
                doc_id = data.get("document_id")
                if doc_id:
                    ctx.set("approved_doc_id", doc_id)
                    return True, f"approved_doc_id={doc_id}"
            except json.JSONDecodeError:
                pass
            return True, "document_id not found in approve response"

        steps.append(PipelineStep(
            name="Решение по черновику (approve)",
            service="orchestrator",
            method="PATCH",
            path="/api/v1/drafts/{draft_id}/decide",
            port=8081,
            body={
                "action": "approve",
                "comment": "Pipeline тест — approved",
            },
            expected_status={200, 409},
            check=_on_approved,
            needs_auth=True,
            skip_if=_draft_skipped,
        ))

        # ── Шаг 9: Проверка документа в Registry ─────────────────────
        steps.append(PipelineStep(
            name="Проверка документа в Registry",
            service="registry",
            method="GET",
            path="/api/v1/registry/documents/{approved_doc_id}",
            port=8084,
            expected_status={200, 404},
            needs_auth=True,
            skip_if=lambda ctx: not ctx.has("approved_doc_id"),
        ))

        # ── Шаг 10: Индексация в RAG Builder ─────────────────────────
        steps.append(PipelineStep(
            name="Индексация документа",
            service="rag_builder",
            method="POST",
            path="/api/v1/rag/build",
            port=8090,
            body={
                "document_id": "{approved_doc_id}",
                "sections": [{
                    "section_id": 1,
                    "document_id": "{approved_doc_id}",
                    "clause": "1",
                    "level": 1,
                    "path": "1",
                    "page": 1,
                    "type": "text",
                    "content": {"text": "Содержимое тестового документа fullcycle"},
                }],
            },
            expected_status={200, 201, 202},
            needs_auth=True,
            check=check_json_field("status", str),
            skip_if=lambda ctx: not ctx.has("approved_doc_id"),
        ))

        # ── Шаг 11: Поиск RAG Search ─────────────────────────────────
        steps.append(PipelineStep(
            name="Поиск RAG Search",
            service="rag_search",
            method="POST",
            path="/api/v1/rag/search",
            port=8091,
            body={
                "query": "тестовый документ",
                "top_k": 3,
                "valid_at": "2026-06-23",
            },
            expected_status=200,
            needs_auth=True,
            skip_if=lambda ctx: not ctx.has("approved_doc_id"),
        ))

        # ── Шаг 12: Удаление черновика ───────────────────────────────
        steps.append(PipelineStep(
            name="Удаление черновика",
            service="orchestrator",
            method="DELETE",
            path="/api/v1/drafts/{draft_id}",
            port=8081,
            expected_status={200, 204},
            needs_auth=True,
            skip_if=_draft_skipped,
        ))

        return steps
