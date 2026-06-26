#!/usr/bin/env python3
"""
PKB Neuroassistant — Pipeline: orchestrator_document_reprocess

Переиндексация документа: создание документа в Registry → POST /documents/{id}/reprocess.

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


class OrchestratorDocumentReprocessPipeline(PipelineDef):
    """Пайплайн: переиндексация документа — создание документа → reprocess."""

    name = "orchestrator_document_reprocess"
    description = "Переиндексация документа Orchestrator (создание документа → reprocess)"
    services = ["gateway"]

    def build_steps(self, context: PipelineContext) -> List[PipelineStep]:
        steps: List[PipelineStep] = []
        ts = datetime.now().strftime("%Y%m%d%H%M%S%f")

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

        # ── Шаг 2: Создание документа в Registry ──────────────────────
        def _on_doc_created(body: Optional[str], ctx: PipelineContext) -> Tuple[bool, str]:
            """Извлечь document_id из data.id ответа Registry."""
            if not body:
                return True, "no body"
            try:
                import json
                data = json.loads(body)
                doc_id = data.get("data", {}).get("id")
                if doc_id:
                    ctx.set("approved_doc_id", doc_id)
                    return True, f"approved_doc_id={doc_id}"
            except json.JSONDecodeError:
                pass
            return True, "document_id not found"

        steps.append(PipelineStep(
            name="Создание документа в Registry (через Gateway)",
            service="gateway",
            method="POST",
            path="/api/v1/registry/documents",
            port=8080,
            body={
                "title": f"Reprocess тест {ts}",
                "doc_code": f"REPROC-{ts}",
                "source_type": "GOST",
                "era": "RF",
                "validity_status": "active",
            },
            expected_status={201, 409},
            check=_on_doc_created,
            needs_auth=True,
        ))

        # ── Шаг 3: Создание черновика (через Gateway) ─────────────────
        pdf_name = f"reprocess-draft-{ts}.pdf"
        steps.append(PipelineStep(
            name="Создание черновика (через Gateway)",
            service="gateway",
            method="POST",
            path="/api/v1/drafts",  # без слеша — проверка, что нет 307
            port=8080,
            form_body={
                "document_key": f"reprocess-key-{ts}",
                "title": f"Reprocess тест {ts}",
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

        # ── Шаг 4: Статус задачи (через Gateway) ──────────────────────
        steps.append(PipelineStep(
            name="Статус задачи (через Gateway)",
            service="gateway",
            method="GET",
            path="/api/v1/tasks/{task_id}/status",
            port=8080,
            expected_status=200,
            check=check_json_field("status", str),
            needs_auth=True,
            skip_if=_draft_skipped,
        ))

        # ── Шаг 5: Переиндексация документа (через Gateway) ───────────
        steps.append(PipelineStep(
            name="Переиндексация документа (через Gateway)",
            service="gateway",
            method="POST",
            path="/api/v1/documents/{approved_doc_id}/reprocess",
            port=8080,
            body={
                "mode": "full",
                "options": {
                    "ocr_engine": "paddleocr",
                    "language": "ru",
                },
            },
            expected_status={202, 409},
            extract_keys=["reprocess_task_id"],
            needs_auth=True,
        ))

        # ── Шаг 6: Статус задачи переиндексации (через Gateway) ───────
        steps.append(PipelineStep(
            name="Статус задачи переиндексации (через Gateway)",
            service="gateway",
            method="GET",
            path="/api/v1/tasks/{reprocess_task_id}/status",
            port=8080,
            expected_status=200,
            check=check_json_field("status", str),
            needs_auth=True,
            skip_if=lambda ctx: not ctx.has("reprocess_task_id"),
        ))

        return steps
