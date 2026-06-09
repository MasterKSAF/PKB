#!/usr/bin/env python3
"""
PKB Neuroassistant — Pipeline: registry_lifecycle

Полный жизненный цикл классификаторов и терминов:
Auth → Registry: Classifiers CRUD → Registry: Terminology CRUD.

Описание: description.md → Пайплайн: registry_lifecycle (12 шагов)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pipelines.base import (
    PipelineContext,
    PipelineDef,
    PipelineStep,
    check_json_field,
    check_json_fields,
)

# Тестовые учётные данные
TEST_CREDENTIALS = {
    "username": "petrova@example.com",
    "password": "secret456",
}


class RegistryLifecyclePipeline(PipelineDef):
    """Пайплайн CRUD-операций классификаторов и терминов Registry."""

    name = "registry_lifecycle"
    description = "CRUD + импорт классификаторов и терминов"
    services = ["auth", "registry"]

    def build_steps(self, context: PipelineContext) -> List[PipelineStep]:
        """Построить 12 шагов пайплайна registry_lifecycle."""
        steps: List[PipelineStep] = []

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

        # ── Шаг 2: Профиль пользователя ──────────────────────────────
        steps.append(PipelineStep(
            name="Профиль пользователя",
            service="auth",
            method="GET",
            path="/api/v1/auth/me",
            port=8082,
            expected_status=200,
            check=check_json_fields({
                "email": str,
                "role": str,
            }),
            needs_auth=True,
        ))

        # ── Шаг 3: Создать классификатор ─────────────────────────────
        steps.append(PipelineStep(
            name="Создать классификатор",
            service="registry",
            method="POST",
            path="/api/v1/registry/classifiers",
            port=8084,
            body={
                "classifier_system": "MKS",
                "code": "99.999",
                "full_name": "Pipeline тестовый классификатор",
                "status": "active",
            },
            expected_status=201,
            extract_keys=["classifier_code"],
            check=check_json_field("data", dict),
            needs_auth=True,
        ))

        # ── Шаг 4: Список классификаторов ────────────────────────────
        steps.append(PipelineStep(
            name="Список классификаторов",
            service="registry",
            method="GET",
            path="/api/v1/registry/classifiers",
            port=8084,
            params={"page": 1, "page_size": 10},
            expected_status=200,
            check=check_json_field("data", list),
            needs_auth=True,
        ))

        # ── Шаг 5: Получить классификатор ────────────────────────────
        steps.append(PipelineStep(
            name="Получить классификатор",
            service="registry",
            method="GET",
            path="/api/v1/registry/classifiers/{classifier_code}",
            port=8084,
            expected_status=200,
            check=check_json_field("data", dict),
            needs_auth=True,
        ))

        # ── Шаг 6: Обновить классификатор ────────────────────────────
        steps.append(PipelineStep(
            name="Обновить классификатор",
            service="registry",
            method="PUT",
            path="/api/v1/registry/classifiers/{classifier_code}",
            port=8084,
            body={"full_name": "Обновлённый pipeline классификатор"},
            expected_status=200,
            check=check_json_field("data", dict),
            needs_auth=True,
        ))

        # ── Шаг 7: Частичное обновление классификатора ───────────────
        steps.append(PipelineStep(
            name="Частичное обновление классификатора",
            service="registry",
            method="PATCH",
            path="/api/v1/registry/classifiers/{classifier_code}",
            port=8084,
            body={"status": "inactive"},
            expected_status=200,
            check=check_json_field("data", dict),
            needs_auth=True,
        ))

        # ── Шаг 8: Удалить классификатор ─────────────────────────────
        steps.append(PipelineStep(
            name="Удалить классификатор",
            service="registry",
            method="DELETE",
            path="/api/v1/registry/classifiers/{classifier_code}",
            port=8084,
            expected_status=200,
            needs_auth=True,
        ))

        # ── Шаг 9: Импорт классификаторов ────────────────────────────
        steps.append(PipelineStep(
            name="Импорт классификаторов",
            service="registry",
            method="POST",
            path="/api/v1/registry/classifiers/import",
            port=8084,
            body={
                "classifiers": [{
                    "classifier_system": "MKS",
                    "code": "99.998",
                    "full_name": "Импортированный pipeline",
                }],
            },
            expected_status=200,
            needs_auth=True,
        ))

        # ── Шаг 10: Создать термин ──────────────────────────────────
        steps.append(PipelineStep(
            name="Создать термин",
            service="registry",
            method="POST",
            path="/api/v1/registry/terminology",
            port=8084,
            body={
                "raw_term": "Pipeline тест",
                "standard_term": "Pipeline тест",
                "normalized_value": "pipeline тест",
                "term_type": "abbreviation",
                "definition": "Тестовый термин из pipeline",
            },
            expected_status=201,
            extract_keys=["term_id"],
            check=check_json_field("data", dict),
            needs_auth=True,
        ))

        # ── Шаг 11: Нормализация термина ───────────────────────────
        steps.append(PipelineStep(
            name="Нормализация термина",
            service="registry",
            method="GET",
            path="/api/v1/registry/terminology/normalize",
            port=8084,
            params={"term": "Pipeline тест"},
            expected_status=200,
            needs_auth=True,
        ))

        # ── Шаг 12: Обновить термин ──────────────────────────────────
        steps.append(PipelineStep(
            name="Обновить термин",
            service="registry",
            method="PUT",
            path="/api/v1/registry/terminology/{term_id}",
            port=8084,
            body={"definition": "Обновлённое определение из pipeline"},
            expected_status=200,
            check=check_json_field("data", dict),
            needs_auth=True,
        ))

        # ── Шаг 13: Импорт терминов ──────────────────────────────────
        steps.append(PipelineStep(
            name="Импорт терминов",
            service="registry",
            method="POST",
            path="/api/v1/registry/terminology/import",
            port=8084,
            body={
                "terms": [{
                    "raw_term": "Импорт pipeline",
                    "standard_term": "Импорт pipeline",
                    "normalized_value": "импорт pipeline",
                    "term_type": "abbreviation",
                }],
            },
            expected_status=200,
            needs_auth=True,
        ))

        return steps
