#!/usr/bin/env python3
"""
PKB Neuroassistant — Pipeline: orchestrator_document_reject

Reject-ветка черновика: создание → решение reject → проверка статуса.

Проверяет альтернативную ветку решения по черновику (reject).
"""

from __future__ import annotations

from datetime import datetime
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


class OrchestratorDocumentRejectPipeline(PipelineDef):
    """Пайплайн: reject черновика — создание → решение → проверка статуса."""

    name = "orchestrator_document_reject"
    description = "Reject черновика Orchestrator (создание → reject → проверка статуса)"
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

        # ── Шаг 2: Создание черновика (через Gateway) ─────────────────
        pdf_name = f"reject-draft-{ts}.pdf"
        steps.append(PipelineStep(
            name="Создание черновика (через Gateway)",
            service="gateway",
            method="POST",
            path="/api/v1/drafts",  # без слеша — проверка, что нет 307
            port=8080,
            form_body={
                "document_key": f"reject-key-{ts}",
                "title": f"Reject тест {ts}",
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

        # ── Шаг 3: Статус задачи (через Gateway) ──────────────────────
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

        # ── Шаг 4: Детали черновика (через Gateway) ───────────────────
        steps.append(PipelineStep(
            name="Детали черновика (через Gateway)",
            service="gateway",
            method="GET",
            path="/api/v1/drafts/{draft_id}",
            port=8080,
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

        # ── Шаг 5: Решение reject (через Gateway) ─────────────────────
        steps.append(PipelineStep(
            name="Решение по черновику (reject, через Gateway)",
            service="gateway",
            method="PATCH",
            path="/api/v1/drafts/{draft_id}/decide",
            port=8080,
            body={
                "action": "reject",
                "comment": "Pipeline тест — rejected",
            },
            expected_status={200, 409},
            check=check_json_field("status", str),
            needs_auth=True,
            skip_if=_draft_skipped,
        ))

        # ── Шаг 6: Проверка статуса после reject (через Gateway) ─────
        steps.append(PipelineStep(
            name="Проверка статуса после reject (через Gateway)",
            service="gateway",
            method="GET",
            path="/api/v1/drafts/{draft_id}",
            port=8080,
            expected_status={200, 404},
            needs_auth=True,
            skip_if=_draft_skipped,
        ))

        return steps
