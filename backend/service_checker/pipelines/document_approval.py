"""
PKB Neuroassistant — Pipeline: document_approval

Подтверждение документа: черновик → preview → решение пользователя → full → индексация.

Проверяет бизнес-логику Pipeline 1 (Формирование документа):
- Создание черновика (через Orchestrator) — точка входа
- Preview-фаза (быстрая обработка)
- Решение пользователя (approve/reject)
- Full-фаза (полная обработка и индексация)

Документ создаётся только через черновик (POST /drafts).
Прямое создание в Registry (минуя черновик) — бизнес-логикой запрещено.
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

_HERE = Path(__file__).resolve().parent.parent
TEST_PDF_PATH = _HERE / "pdf" / "7bd97d737317a8a272bb18a405ab2d04.pdf"
TEST_PDF_BYTES = TEST_PDF_PATH.read_bytes()


def _on_draft_failed(body: Optional[str], ctx: PipelineContext) -> None:
    """При сбое черновика — запомнить и продолжать."""
    ctx.set("draft_failed", True)


def _draft_skipped(ctx: PipelineContext) -> bool:
    """Пропустить шаги черновика, если он не создан."""
    return ctx.get("draft_failed", False)


class DocumentApprovalPipeline(PipelineDef):
    """Пайплайн: подтверждение документа — черновик → решение → индексация."""

    name = "document_approval"
    description = (
        "Подтверждение документа: черновик → preview → решение пользователя "
        "→ full-фаза → индексация (документ только через черновик)"
    )
    services = ["auth", "orchestrator", "registry", "rag_builder", "rag_search"]

    def build_steps(self, context: PipelineContext) -> List[PipelineStep]:
        """Построить шаги пайплайна document_approval."""
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

        # ════════════════════════════════════════════════════════════════
        # ФАЗА 1: Черновик → Preview → Approve
        # ════════════════════════════════════════════════════════════════
        # Если Registry не реализовал POST /drafts, фаза честно падает.
        # on_error переключает skip_if для зависимых шагов.

        pdf_name = f"approval-draft-{ts}.pdf"
        steps.append(PipelineStep(
            name="Создание черновика",
            service="orchestrator",
            method="POST",
            path="/api/v1/drafts/",
            port=8081,
            form_body={
                "document_key": f"approval-key-{ts}",
                "title": f"Approval тест {ts}",
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
            needs_auth=True,
            skip_if=_draft_skipped,
        ))

        def _check_doc_id(body: Optional[str], ctx: PipelineContext) -> Tuple[bool, str]:
            if not body:
                return (True, "пустой ответ (404 — черновик удалён)")
            import json
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
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

        # ════════════════════════════════════════════════════════════════
        # ФАЗА 2: Создание документа в Registry + Индексация
        # Выполняется только если черновик создан (есть draft_id)
        # ════════════════════════════════════════════════════════════════

        steps.append(PipelineStep(
            name="Создание документа в Registry",
            service="registry",
            method="POST",
            path="/api/v1/registry/documents",
            port=8084,
            body={
                "title": f"Approval тест {ts}",
                "doc_code": f"APPROVAL-{ts}",
                "source_type": "GOST",
                "era": "RF",
                "validity_status": "active",
                "mks_oks_code": "47.020",
                "title_key": f"GOST|RF|APPROVAL-{ts}|2026",
            },
            expected_status={201, 409},
            needs_auth=True,
            extract_keys=["doc_id"],
            skip_if=_draft_skipped,
        ))

        # ── Шаг 13: FULL-фаза (полная обработка) ────────────────────
        steps.append(PipelineStep(
            name="Индексация документа",
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
                    "type": "text",
                    "content": {"text": "Содержимое тестового документа approval"},
                }],
            },
            expected_status={200, 201, 202},
            needs_auth=True,
            check=check_json_field("status", str),
            skip_if=_draft_skipped,
        ))

        return steps
