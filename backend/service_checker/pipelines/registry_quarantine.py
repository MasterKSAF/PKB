#!/usr/bin/env python3
"""
PKB Neuroassistant — Pipeline: registry_quarantine

Карантин классификаторов Registry: создание документа с неизвестным кодом →
попадание в карантин → accept/reject → валидация.

Проверяет бизнес-логику Registry: принятие/отклонение классификаторов.
"""

from __future__ import annotations

from datetime import datetime
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


class RegistryQuarantinePipeline(PipelineDef):
    """Пайплайн: карантин классификаторов — accept и reject."""

    name = "registry_quarantine"
    description = "Карантин классификаторов: accept/reject + валидация"
    services = ["gateway"]

    def build_steps(self, context: PipelineContext) -> List[PipelineStep]:
        """Построить 10 шагов пайплайна registry_quarantine."""
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

        # ── Шаг 2: Создать классификатор (через Gateway) ──────────────
        classifier_code = f"98.{ts[-6:]}"
        steps.append(PipelineStep(
            name="Создать классификатор (через Gateway)",
            service="gateway",
            method="POST",
            path="/api/v1/registry/classifiers",
            port=18080,
            body={
                "classifier_system": "MKS",
                "code": classifier_code,
                "full_name": f"Pipeline quarantine классификатор {ts}",
                "status": "active",
            },
            expected_status={201, 409},
            extract_keys=["classifier_code"],
            check=lambda body, ctx: (True, ""),
            needs_auth=True,
        ))

        # ── Шаг 3: Создать документ с неизвестным кодом (через Gateway) ─
        unknown_code = f"97.{ts[-6:]}"
        steps.append(PipelineStep(
            name="Создать документ с неизвестным кодом (через Gateway)",
            service="gateway",
            method="POST",
            path="/api/v1/registry/documents",
            port=18080,
            body={
                "title": f"Pipeline quarantine документ {ts}",
                "doc_code": f"QUAR-TEST-{ts}",
                "source_type": "GOST",
                "era": "RF",
                "validity_status": "active",
                "mks_oks_code": unknown_code,
            },
            expected_status={201, 409},
            extract_keys=["quar_doc_id"],
            # Registry возвращает {data: {id: ..., document_id: ..., title: ..., ...}}
            # _extract_context ищет id/document_id через alt_map
            check=check_json_field("data", dict),
            needs_auth=True,
        ))

        # ── Шаг 4: Список карантина — получить pending_id (через Gateway) ─
        steps.append(PipelineStep(
            name="Список карантина (pending, через Gateway)",
            service="gateway",
            method="GET",
            path="/api/v1/registry/classifiers/pending",
            port=18080,
            params={"page": 1, "page_size": 10},
            expected_status=200,
            extract_keys=["pending_id"],
            check=check_json_field("data", list),
            needs_auth=True,
        ))

        # ── Шаг 5: Принять из карантина (accept, через Gateway) ───────
        steps.append(PipelineStep(
            name="Принять из карантина (accept, через Gateway)",
            service="gateway",
            method="POST",
            path="/api/v1/registry/classifiers/pending/{pending_id}/accept",
            port=18080,
            body={
                "parent_code": classifier_code,
                "full_name": f"Pipeline принятый классификатор {ts}",
            },
            expected_status={200, 307},
            check=check_json_field("data", dict),
            needs_auth=True,
        ))

        # ── Шаг 6: Валидация классификации после accept (через Gateway) ─
        steps.append(PipelineStep(
            name="Валидация классификации (accept, через Gateway)",
            service="gateway",
            method="POST",
            path="/api/v1/registry/classifiers/validate",
            port=18080,
            body={
                "classification": {
                    "mks_oks_code": unknown_code,
                    "okstu_code": None,
                    "udk_code": None,
                }
            },
            expected_status=200,
            # validate возвращает {data: {mks_status: ..., overall_status: ..., ...}}
            check=check_json_field("data.mks_status", str),
            needs_auth=True,
        ))

        # ── Шаг 7: Создать второй документ с другим неизвестным кодом (через Gateway) ─
        unknown_code2 = f"96.{ts[-6:]}"
        steps.append(PipelineStep(
            name="Создать второй документ с неизвестным кодом (через Gateway)",
            service="gateway",
            method="POST",
            path="/api/v1/registry/documents",
            port=18080,
            body={
                "title": f"Pipeline quarantine документ 2 {ts}",
                "doc_code": f"QUAR-TEST2-{ts}",
                "source_type": "GOST",
                "era": "RF",
                "validity_status": "active",
                "mks_oks_code": unknown_code2,
            },
            expected_status={201, 409},
            extract_keys=["quar_doc_id2"],
            # Registry возвращает {data: {id: ..., document_id: ..., ...}}
            check=check_json_field("data", dict),
            needs_auth=True,
        ))

        # ── Шаг 8: Список карантина — получить второй pending_id (через Gateway) ─
        steps.append(PipelineStep(
            name="Список карантина (второй pending, через Gateway)",
            service="gateway",
            method="GET",
            path="/api/v1/registry/classifiers/pending",
            port=18080,
            params={"page": 1, "page_size": 10},
            expected_status=200,
            extract_keys=["pending_id2"],
            check=check_json_field("data", list),
            needs_auth=True,
        ))

        # ── Шаг 9: Отклонить из карантина (reject, через Gateway) ─────
        steps.append(PipelineStep(
            name="Отклонить из карантина (reject, через Gateway)",
            service="gateway",
            method="POST",
            path="/api/v1/registry/classifiers/pending/{pending_id2}/reject",
            port=18080,
            body={
                "admin_comment": "Отклонено pipeline тестом",
            },
            expected_status={200, 307},
            check=check_json_field("data", dict),
            needs_auth=True,
        ))

        # ── Шаг 10: Валидация после reject (через Gateway) ────────────
        steps.append(PipelineStep(
            name="Валидация классификации (reject, через Gateway)",
            service="gateway",
            method="POST",
            path="/api/v1/registry/classifiers/validate",
            port=18080,
            body={
                "classification": {
                    "mks_oks_code": unknown_code2,
                    "okstu_code": None,
                    "udk_code": None,
                }
            },
            expected_status=200,
            # validate возвращает {data: {mks_status: ..., overall_status: ..., ...}}
            check=check_json_field("data.mks_status", str),
            needs_auth=True,
        ))

        return steps
