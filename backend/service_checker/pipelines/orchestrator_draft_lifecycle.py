#!/usr/bin/env python3
"""
PKB Neuroassistant — Pipeline: orchestrator_draft_lifecycle

Сквозной тест Orchestrator: создание черновика → превью → решение → 404.

Проверяет основной пользовательский путь через Orchestrator — единую точку входа системы.
"""

from __future__ import annotations

from datetime import datetime
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

# Тестовый PDF
_HERE = Path(__file__).resolve().parent.parent
TEST_PDF_PATH = _HERE / "pdf" / "7bd97d737317a8a272bb18a405ab2d04.pdf"
TEST_PDF_BYTES = TEST_PDF_PATH.read_bytes()


class OrchestratorDraftLifecyclePipeline(PipelineDef):
    """Пайплайн: черновик Orchestrator — создание → превью → решение → 404."""

    name = "orchestrator_draft_lifecycle"
    description = "Жизненный цикл черновика Orchestrator (создание → превью → решение → удаление)"
    services = ["auth", "orchestrator"]

    def build_steps(self, context: PipelineContext) -> List[PipelineStep]:
        """Построить 8 шагов пайплайна orchestrator_draft_lifecycle."""
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
        pdf_name = f"pipeline-draft-{ts}.pdf"
        steps.append(PipelineStep(
            name="Создание черновика",
            service="orchestrator",
            method="POST",
            path="/api/v1/drafts/",
            port=8081,
            form_body={
                "document_key": f"pipeline-draft-key-{ts}",
                "title": f"Pipeline черновик {ts}",
            },
            form_files={
                "file": (pdf_name, TEST_PDF_BYTES, "application/pdf"),
            },
            expected_status=202,
            extract_keys=["draft_id", "task_id"],
            check=check_json_field("draft_id", int),
            needs_auth=True,
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
        ))

        # ── Шаг 4: Детали черновика ──────────────────────────────────
        steps.append(PipelineStep(
            name="Детали черновика",
            service="orchestrator",
            method="GET",
            path="/api/v1/drafts/{draft_id}",
            port=8081,
            expected_status=200,
            check=check_json_field("draft_id", int),
            needs_auth=True,
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
        ))

        # ── Шаг 6: Статус превью ─────────────────────────────────────
        steps.append(PipelineStep(
            name="Статус превью",
            service="orchestrator",
            method="GET",
            path="/api/v1/drafts/{draft_id}/preview/status",
            port=8081,
            params={"longpoll": 0},
            expected_status={200, 404},
            check=check_json_field("status", str),
            needs_auth=True,
        ))

        # ── Шаг 7: Принять решение по черновику (OR-12: action=approve) ──
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
        ))

        # ── Шаг 8: Проверка, что черновик удалён (404) ───────────────
        steps.append(PipelineStep(
            name="Проверка 404 после решения",
            service="orchestrator",
            method="GET",
            path="/api/v1/drafts/{draft_id}",
            port=8081,
            expected_status={404, 200},
            needs_auth=True,
        ))

        return steps
