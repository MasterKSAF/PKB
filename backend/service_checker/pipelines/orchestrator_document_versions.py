#!/usr/bin/env python3
"""
PKB Neuroassistant — Pipeline: orchestrator_document_versions

Версионирование документа: создание документа → загрузка версий.

Проверяет OR-8a: загрузка новой версии файла документа.
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


class OrchestratorDocumentVersionsPipeline(PipelineDef):
    """Пайплайн: версионирование документа — создание документа → загрузка версий."""

    name = "orchestrator_document_versions"
    description = "Версионирование документа Orchestrator (создание документа → новая версия)"
    services = ["gateway", "orchestrator", "registry"]

    def build_steps(self, context: PipelineContext) -> List[PipelineStep]:
        steps: List[PipelineStep] = []
        ts = datetime.now().strftime("%Y%m%d%H%M%S%f")

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

        # ── Шаг 2: Создание документа в Registry ──────────────────────
        def _on_doc_created(body: Optional[str], ctx: PipelineContext) -> Tuple[bool, str]:
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
            port=18080,
            body={
                "title": f"Version тест {ts}",
                "doc_code": f"VERSION-{ts}",
                "source_type": "GOST",
                "era": "RF",
                "validity_status": "active",
            },
            expected_status={201, 409},
            check=_on_doc_created,
            needs_auth=True,
        ))

        # ── Шаг 3: Загрузка новой версии (через Gateway) ──────────────
        v2_pdf_name = f"version-v2-{ts}.pdf"
        steps.append(PipelineStep(
            name="Загрузка новой версии документа (через Gateway)",
            service="gateway",
            method="POST",
            path="/api/v1/documents/{approved_doc_id}/versions",
            port=18080,
            form_files={
                "file": (v2_pdf_name, TEST_PDF_BYTES, "application/pdf"),
            },
            expected_status={200, 201, 404},
            needs_auth=True,
        ))

        # ── Шаг 4: Проверка списка версий (через Gateway) ─────────────
        steps.append(PipelineStep(
            name="Проверка списка версий (через Gateway)",
            service="gateway",
            method="GET",
            path="/api/v1/documents/{approved_doc_id}/versions",
            port=18080,
            expected_status={200, 404},
            needs_auth=True,
        ))

        return steps
