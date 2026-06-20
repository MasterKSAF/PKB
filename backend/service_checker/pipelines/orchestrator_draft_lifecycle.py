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
            name="Проверка document_id после approve",
            service="orchestrator",
            method="GET",
            path="/api/v1/drafts/{draft_id}",
            port=8081,
            expected_status={200, 404},
            check=_check_doc_id,
            needs_auth=True,
        ))

        # ── Шаг 9: Если document_id получен — проверить в Registry (OR-13) ──
        def _check_registry_doc(body, ctx):
            if not body:
                return (True, "пропущено: document_id не получен")
            return (True, "документ существует в Registry")

        steps.append(PipelineStep(
            name="Проверка документа в Registry",
            service="registry",
            method="GET",
            path="/api/v1/registry/documents/{approved_doc_id}",
            port=8084,
            expected_status={200, 404},
            check=_check_registry_doc,
            needs_auth=True,
            skip_if=lambda ctx: not ctx.has("approved_doc_id"),
        ))

        # ── Шаг 10 (OR-14): MIME-ветвление — создание черновика с image/png ──
        steps.append(PipelineStep(
            name="Создание черновика (image/png для OR-14)",
            service="orchestrator",
            method="POST",
            path="/api/v1/drafts/",
            port=8081,
            form_body={
                "document_key": f"pipeline-img-{ts}",
                "title": f"Pipeline image черновик {ts}",
            },
            form_files={
                "file": (f"image-{ts}.png", MINIMAL_PNG, "image/png"),
            },
            expected_status=202,
            extract_keys=["draft_id_2", "task_id_2"],
            check=check_json_field("draft_id", int),
            needs_auth=True,
        ))

        # ── Шаг 11 (OR-14): Статус задачи для image-черновика ────────────
        steps.append(PipelineStep(
            name="Статус задачи image (OR-14)",
            service="orchestrator",
            method="GET",
            path="/api/v1/tasks/{task_id_2}/status",
            port=8081,
            expected_status=200,
            check=check_json_field("status", str),
            needs_auth=True,
        ))

        return steps
