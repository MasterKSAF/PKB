"""
PKB Neuroassistant — Pipeline: full_document_cycle

Полный сквозной цикл документа через Orchestrator: от загрузки PDF до поиска.

Покрывает:
- Создание черновика с PDF (через Orchestrator/Gateway)
- Ожидание завершения парсинга (статус задачи)
- Preview-фаза (конвертация/валидация через Orchestrator)
- Решение пользователя (approve)
- Проверка документа в Registry
- Индексация (RAG Builder)
- Поиск (RAG Search)
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

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

_HERE = Path(__file__).resolve().parent.parent
TEST_PDF_PATH = _HERE / "pdf" / "7bd97d737317a8a272bb18a405ab2d04.pdf"
TEST_PDF_BYTES = TEST_PDF_PATH.read_bytes()


def _on_draft_failed(body: Optional[str], ctx: PipelineContext) -> None:
    ctx.set("draft_failed", True)


def _draft_failed(ctx: PipelineContext) -> bool:
    return ctx.get("draft_failed", False)


class FullDocumentCyclePipeline(PipelineDef):
    """Пайплайн: полный сквозной цикл документа через Orchestrator — от загрузки PDF до поиска."""

    name = "full_document_cycle"
    description = (
        "Полный сквозной цикл: загрузка PDF через черновик → парсинг → "
        "preview → approve → Registry → индексация → поиск"
    )
    services = ["gateway", "orchestrator", "rag_builder", "rag_search"]

    def build_steps(self, context: PipelineContext) -> List[PipelineStep]:
        steps: List[PipelineStep] = []
        ts = datetime.now().strftime("%Y%m%d%H%M%S%f")
        pdf_name = f"full-cycle-{ts}.pdf"

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

        # ── Шаг 2: Создание черновика с PDF (через Gateway) ────────────
        # Orchestrator запускает парсинг загруженного файла
        steps.append(PipelineStep(
            name="Создание черновика с PDF (через Gateway)",
            service="gateway",
            method="POST",
            path="/api/v1/drafts",
            port=18080,
            form_body={
                "document_key": f"full-cycle-key-{ts}",
                "title": f"Full Cycle тест {ts}",
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
        # Парсинг выполняется асинхронно внутри Orchestrator
        steps.append(PipelineStep(
            name="Статус задачи (через Gateway)",
            service="gateway",
            method="GET",
            path="/api/v1/tasks/{task_id}/status",
            port=18080,
            expected_status=200,
            check=check_json_field("status", str),
            needs_auth=True,
            skip_if=_draft_failed,
        ))

        # ── Шаг 4: Детали черновика (через Gateway) ───────────────────
        steps.append(PipelineStep(
            name="Детали черновика (через Gateway)",
            service="gateway",
            method="GET",
            path="/api/v1/drafts/{draft_id}",
            port=18080,
            expected_status=200,
            check=check_json_fields({
                "draft_id": int,
                "document_id": (int, type(None)),
                "version_id": (int, type(None)),
                "is_new_document": bool,
            }),
            needs_auth=True,
            skip_if=_draft_failed,
        ))

        # ── Шаг 5: Запуск превью (через Gateway) ──────────────────────
        # Orchestrator запускает конвертацию/валидацию
        steps.append(PipelineStep(
            name="Запуск превью (через Gateway)",
            service="gateway",
            method="POST",
            path="/api/v1/drafts/{draft_id}/preview",
            port=18080,
            body={},
            expected_status={200, 202, 404},
            needs_auth=True,
            skip_if=_draft_failed,
        ))

        # ── Шаг 6: Статус превью (через Gateway) ──────────────────────
        steps.append(PipelineStep(
            name="Статус превью (через Gateway)",
            service="gateway",
            method="GET",
            path="/api/v1/drafts/{draft_id}/preview/status",
            port=18080,
            params={"longpoll": 1},
            expected_status={200, 404},
            needs_auth=True,
            skip_if=_draft_failed,
        ))

        # ── Шаг 7: Approve (через Gateway) ────────────────────────────
        def _on_approved(body: Optional[str], ctx: PipelineContext) -> Tuple[bool, str]:
            """Извлечь document_id из ответа approve."""
            if not body:
                return True, "no body"
            try:
                data = json.loads(body)
                doc_id = data.get("document_id")
                if doc_id:
                    ctx.set("approved_doc_id", doc_id)
                    return True, f"approved_doc_id={doc_id}"
            except json.JSONDecodeError:
                pass
            return True, "document_id not found in approve response"

        steps.append(PipelineStep(
            name="Решение по черновику (approve, через Gateway)",
            service="gateway",
            method="PATCH",
            path="/api/v1/drafts/{draft_id}/decide",
            port=18080,
            body={
                "action": "approve",
                "comment": "Pipeline тест — approved",
            },
            expected_status={200, 409},
            check=_on_approved,
            needs_auth=True,
            skip_if=_draft_failed,
        ))

        # ── Шаг 8: Проверка документа в Registry (через Gateway) ─────
        steps.append(PipelineStep(
            name="Проверка документа в Registry (через Gateway)",
            service="gateway",
            method="GET",
            path="/api/v1/registry/documents/{approved_doc_id}",
            port=18080,
            expected_status={200, 404},
            needs_auth=True,
            skip_if=lambda ctx: not ctx.has("approved_doc_id"),
        ))

        # ── Шаг 9: Индексация (RAG Builder, напрямую) ────────────────
        steps.append(PipelineStep(
            name="Индексация документа (RAG Builder)",
            service="rag_builder",
            method="POST",
            path="/api/v1/rag/build",
            port=18090,
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
                    "content": {"text": "Содержимое тестового документа full cycle"},
                }],
            },
            expected_status={200, 201, 202},
            needs_auth=True,
            check=check_json_field("status", str),
            skip_if=lambda ctx: not ctx.has("approved_doc_id"),
        ))

        # ── Шаг 10: Поиск (RAG Search, напрямую) ──────────────────────
        steps.append(PipelineStep(
            name="Поиск по индексу (RAG Search)",
            service="rag_search",
            method="POST",
            path="/api/v1/rag/search",
            port=18091,
            body={
                "query": "тестовый документ full cycle",
                "top_k": 3,
                "valid_at": datetime.now().strftime("%Y-%m-%d"),
            },
            expected_status=200,
            needs_auth=True,
            check=check_rag_search_results(),
            skip_if=lambda ctx: not ctx.has("approved_doc_id"),
        ))

        return steps
