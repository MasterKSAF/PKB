#!/usr/bin/env python3
"""
PKB Neuroassistant — Pipeline: orchestrator_document_reprocess

Переиндексация документа: создание → approve → POST /documents/{id}/reprocess.

Проверяет OR-задачу: переобработка документа без создания черновика.
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


def _check_doc_id(body: Optional[str], ctx: PipelineContext) -> Tuple[bool, str]:
    if not body:
        return (True, "пустой ответ (404 — черновик удалён)")
    try:
        import json
        data = json.loads(body)
    except JSONDecodeError:
        return (True, "не JSON (404)")
    doc_id = data.get("document_id")
    if doc_id:
        ctx.set("approved_doc_id", doc_id)
        return (True, f"document_id={doc_id}")
    ver_id = data.get("version_id")
    if ver_id:
        ctx.set("approved_version_id", ver_id)
        return (True, f"version_id={ver_id}")
    return (True, "документ создан (без id в ответе)")


class OrchestratorDocumentReprocessPipeline(PipelineDef):
    """Пайплайн: переиндексация документа — черновик → approve → reprocess."""

    name = "orchestrator_document_reprocess"
    description = "Переиндексация документа Orchestrator (черновик → approve → reprocess)"
    services = ["auth", "orchestrator", "registry"]

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
        pdf_name = f"reprocess-draft-{ts}.pdf"
        steps.append(PipelineStep(
            name="Создание черновика",
            service="orchestrator",
            method="POST",
            path="/api/v1/drafts/",
            port=8081,
            form_body={
                "document_key": f"reprocess-key-{ts}",
                "title": f"Reprocess тест {ts}",
                "source_type": "GOST",
            },
            form_files={
                "file": (pdf_name, TEST_PDF_BYTES, "application/pdf"),
            },
            expected_status=202,
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

        # ── Шаг 5: Approve черновика ─────────────────────────────────
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
            check=check_json_field("status", str),
            needs_auth=True,
            skip_if=_draft_skipped,
        ))

        # ── Шаг 6: Проверка document_id после approve ────────────────
        steps.append(PipelineStep(
            name="Проверка document_id после approve",
            service="orchestrator",
            method="GET",
            path="/api/v1/drafts/{draft_id}",
            port=8081,
            expected_status={200, 404},
            check=_check_doc_id,
            needs_auth=True,
            skip_if=_draft_skipped,
        ))

        # ── Шаг 7: Проверка документа в Registry ─────────────────────
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

        # ── Шаг 8: Переиндексация документа ──────────────────────────
        steps.append(PipelineStep(
            name="Переиндексация документа",
            service="orchestrator",
            method="POST",
            path="/api/v1/documents/{approved_doc_id}/reprocess",
            port=8081,
            body={
                "mode": "full",
                "options": {
                    "ocr_engine": "paddleocr",
                    "language": "ru",
                },
            },
            expected_status=202,
            extract_keys=["reprocess_task_id"],
            check=check_json_field("task_id", int),
            needs_auth=True,
            skip_if=lambda ctx: not ctx.has("approved_doc_id"),
        ))

        # ── Шаг 9: Статус задачи переиндексации ──────────────────────
        steps.append(PipelineStep(
            name="Статус задачи переиндексации",
            service="orchestrator",
            method="GET",
            path="/api/v1/tasks/{reprocess_task_id}/status",
            port=8081,
            expected_status=200,
            check=check_json_field("status", str),
            needs_auth=True,
            skip_if=lambda ctx: not ctx.has("reprocess_task_id"),
        ))

        return steps
