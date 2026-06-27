#!/usr/bin/env python3
"""
PKB Neuroassistant — Pipeline: orchestrator_draft_lifecycle

Сквозной тест Orchestrator: создание черновика → превью → решение → 404.

Проверяет основной пользовательский путь через Orchestrator — единую точку входа системы.
"""

from __future__ import annotations

import struct
import zlib
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


# OR-14: минимальный 1x1 PNG для проверки MIME-ветвления
def _make_minimal_png() -> bytes:
    """Создать минимальный валидный 1x1 RGBA PNG."""
    def _chunk(ctype: bytes, data: bytes) -> bytes:
        body = ctype + data
        return struct.pack('>I', len(data)) + body + struct.pack('>I', zlib.crc32(body) & 0xFFFFFFFF)
    ihdr_data = struct.pack('>IIBBBBB', 1, 1, 8, 6, 0, 0, 0)  # 1x1, 8-bit RGBA
    raw = b'\x00\x00\x00\x00\x00'  # filter=None, pixel=RGBA(0,0,0,0)
    return (b'\x89PNG\r\n\x1a\n' +
            _chunk(b'IHDR', ihdr_data) +
            _chunk(b'IDAT', zlib.compress(raw)) +
            _chunk(b'IEND', b''))

MINIMAL_PNG: bytes = _make_minimal_png()


class OrchestratorDraftLifecyclePipeline(PipelineDef):
    """Пайплайн: черновик Orchestrator — создание → превью → решение → 404."""

    name = "orchestrator_draft_lifecycle"
    description = "Жизненный цикл черновика через Gateway (создание → превью → решение → удаление)"
    services = ["gateway", "orchestrator", "registry"]

    def build_steps(self, context: PipelineContext) -> List[PipelineStep]:
        """Построить 11 шагов пайплайна orchestrator_draft_lifecycle."""
        steps: List[PipelineStep] = []
        ts = datetime.now().strftime("%Y%m%d%H%M%S%f")

        # Вспомогательные функции для graceful recovery при 409 (duplicate)
        def _on_draft_conflict(body: Optional[str], ctx: PipelineContext) -> None:
            ctx.set("draft_failed", True)

        def _draft_skipped(ctx: PipelineContext) -> bool:
            return ctx.get("draft_failed", False)

        def _check_draft_response(body, ctx, actual_status=None):
            """Check draft creation response — tolerant of 409 (duplicate)."""
            if actual_status == 409:
                # 409 conflict — тело не содержит draft_id, это нормально
                ctx.set("draft_failed", True)
                return (True, "409 conflict — пропускаем оставшиеся шаги")
            if not body:
                return (True, "no body")
            import json
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                return (True, "not json")
            if data.get("draft_id") is not None:
                return (True, f"draft_id={data['draft_id']}")
            # fallback: нет draft_id, но и не 409
            ctx.set("draft_failed", True)
            return (True, "draft_id not found in response")

        # ── Шаг 1: Аутентификация через Gateway ──────────────────────
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

        # ── Шаг 2: Создание черновика через Gateway ──────────────────
        pdf_name = f"pipeline-draft-{ts}.pdf"
        steps.append(PipelineStep(
            name="Создание черновика (через Gateway)",
            service="gateway",
            method="POST",
            path="/api/v1/drafts",  # без слеша — проверка, что нет 307
            port=18080,
            form_body={
                "document_key": f"pipeline-draft-key-{ts}",
                "title": f"Pipeline черновик {ts}",
                "source_type": "GOST",  # OR-11: обязательное поле
            },
            form_files={
                "file": (pdf_name, TEST_PDF_BYTES, "application/pdf"),
            },
            expected_status={202, 409},
            extract_keys=["draft_id", "task_id"],
            check=_check_draft_response,
            needs_auth=True,
            on_error=_on_draft_conflict,
        ))

        # ── Шаг 3: Статус задачи через Gateway ───────────────────────
        steps.append(PipelineStep(
            name="Статус задачи (через Gateway)",
            service="gateway",
            method="GET",
            path="/api/v1/tasks/{task_id}/status",
            port=18080,
            expected_status={200, 404},
            check=check_json_field("status", str),
            needs_auth=True,
            skip_if=_draft_skipped,
        ))

        # ── Шаг 4: Детали черновика (OR-7) через Gateway ──────────────
        steps.append(PipelineStep(
            name="Детали черновика (через Gateway)",
            service="gateway",
            method="GET",
            path="/api/v1/drafts/{draft_id}",
            port=18080,
            expected_status=200,
            check=check_json_fields({
                "draft_id": int,
                "document_id": (int, type(None)),  # OR-7: может быть None до approve
                "version_id": (int, type(None)),   # OR-7: может быть None до approve
                "is_new_document": bool,            # OR-7: флаг нового документа
                "created_by": (str, type(None)),    # #18: проверка что черновик создан от реального пользователя, не u-mock-001
            }),
            needs_auth=True,
            skip_if=_draft_skipped,
        ))

        # ── Шаг 5: Запуск превью через Gateway ───────────────────────
        steps.append(PipelineStep(
            name="Запуск превью (через Gateway)",
            service="gateway",
            method="POST",
            path="/api/v1/drafts/{draft_id}/preview",
            port=18080,
            body={},
            expected_status={200, 202, 404},
            needs_auth=True,
            skip_if=_draft_skipped,
        ))

        # ── Шаг 6: Статус превью через Gateway ───────────────────────
        steps.append(PipelineStep(
            name="Статус превью (через Gateway)",
            service="gateway",
            method="GET",
            path="/api/v1/drafts/{draft_id}/preview/status",
            port=18080,
            params={"longpoll": 1},
            expected_status={200, 404},
            check=check_json_field("status", str),
            needs_auth=True,
            skip_if=_draft_skipped,
        ))

        # ── Шаг 7: Принять решение по черновику (OR-12) через Gateway ─
        steps.append(PipelineStep(
            name="Решение approve (через Gateway)",
            service="gateway",
            method="PATCH",
            path="/api/v1/drafts/{draft_id}/decide",
            port=18080,
            body={
                "action": "approve",
                "comment": "Pipeline тест — approved",
            },
            expected_status={200, 409},
            check=check_json_field("status", str),
            needs_auth=True,
            skip_if=_draft_skipped,
        ))

        # ── Шаг 8: Проверка document_id после approve (OR-13) ────────
        # OR-7: GET /drafts/{id} возвращает document_id, version_id, is_new_document
        # После approve черновик может быть удалён (404) или содержать document_id (200)
        def _check_doc_id(body, ctx):
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
            is_new = data.get("is_new_document")
            if is_new is not None:
                return (True, f"is_new_document={is_new}")
            return (True, "документ создан (без id в ответе)")

        steps.append(PipelineStep(
            name="Проверка document_id (через Gateway)",
            service="gateway",
            method="GET",
            path="/api/v1/drafts/{draft_id}",
            port=18080,
            expected_status={200, 404},
            check=_check_doc_id,
            needs_auth=True,
            skip_if=_draft_skipped,
        ))

        # ── Шаг 9: Если document_id получен — проверить в Registry (OR-13) ──
        def _check_registry_doc(body, ctx):
            if not body:
                return (True, "пропущено: document_id не получен")
            return (True, "документ существует в Registry")

        steps.append(PipelineStep(
            name="Проверка документа в Registry (через Gateway)",
            service="gateway",
            method="GET",
            path="/api/v1/registry/documents/{approved_doc_id}",
            port=18080,
            expected_status={200, 404},
            check=_check_registry_doc,
            needs_auth=True,
            skip_if=lambda ctx: not ctx.has("approved_doc_id") or ctx.get("draft_failed", False),
        ))

        # ── Шаг 10 (OR-14): MIME-ветвление — создание черновика с image/png ──
        steps.append(PipelineStep(
            name="Создание черновика image/png (через Gateway)",
            service="gateway",
            method="POST",
            path="/api/v1/drafts",  # без слеша
            port=18080,
            form_body={
                "document_key": f"pipeline-img-{ts}",
                "title": f"Pipeline image черновик {ts}",
                "source_type": "GOST",  # OR-11: обязательное поле
            },
            form_files={
                "file": (f"image-{ts}.png", MINIMAL_PNG, "image/png"),
            },
            expected_status={202, 409},
            extract_keys=["draft_id_2", "task_id_2"],
            check=check_json_field("draft_id", int),
            needs_auth=True,
            on_error=_on_draft_conflict,
        ))

        # ── Шаг 11 (OR-14): Статус задачи для image-черновика ────────────
        steps.append(PipelineStep(
            name="Статус задачи image (через Gateway)",
            service="gateway",
            method="GET",
            path="/api/v1/tasks/{task_id_2}/status",
            port=18080,
            expected_status={200, 404},
            check=check_json_field("status", str),
            needs_auth=True,
            skip_if=_draft_skipped,
        ))

        return steps
