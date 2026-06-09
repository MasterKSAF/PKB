#!/usr/bin/env python3
"""
PKB Neuroassistant — Pipeline: document_processing

Полный цикл обработки документа: PDF-файл → MinIO → Parser → Converter →
Registry → RAG Builder → RAG Search.

Описание: description.md → Пайплайн: document_processing (8 шагов)
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

# Порт MinIO S3 API (обычно 9000)
MINIO_PORT = 9000

# Тестовый PDF-файл из каталога pdf/
TEST_PDF_KEY = "test-document.pdf"
TEST_PDF_PATH = "pdf/7bd97d737317a8a272bb18a405ab2d04.pdf"


class DocumentProcessingPipeline(PipelineDef):
    """Пайплайн обработки документа: загрузка → парсинг → конвертация → регистрация → индексация → поиск."""

    name = "document_processing"
    description = "Полный цикл обработки документа"
    services = ["minio", "parser", "converter_validator", "registry", "rag_builder", "rag_search"]

    def build_steps(self, context: PipelineContext) -> List[PipelineStep]:
        """Построить 8 шагов пайплайна document_processing."""
        steps: List[PipelineStep] = []

        # ── Шаг 1: Загрузка PDF в MinIO ──────────────────────────────
        steps.append(PipelineStep(
            name="Загрузка PDF в MinIO",
            service="minio",
            method="PUT",
            path="/minio/documents/",
            port=MINIO_PORT,
            expected_status=200,
            extract_keys=["file_key"],
            check=check_json_field("file_key", str),
        ))

        # ── Шаг 2: Запуск парсинга ───────────────────────────────────
        steps.append(PipelineStep(
            name="Запуск парсинга",
            service="parser",
            method="POST",
            path="/api/v1/parser/process",
            port=8087,
            body={
                "task_id": "pipeline-test-task",
                "version_id": "pipeline-test-version",
                "file_key": "{file_key}",
            },
            expected_status=202,
            extract_keys=["task_id"],
            check=check_json_field("task_id", str),
        ))

        # ── Шаг 3: Статус парсинга (longpoll) ────────────────────────
        steps.append(PipelineStep(
            name="Статус парсинга (longpoll)",
            service="parser",
            method="GET",
            path="/api/v1/parser/process/{task_id}/status",
            port=8087,
            expected_status=200,
            check=check_json_field("status", str),
        ))

        # ── Шаг 4: Результат парсинга ────────────────────────────────
        steps.append(PipelineStep(
            name="Результат парсинга",
            service="parser",
            method="GET",
            path="/api/v1/parser/process/{task_id}/result",
            port=8087,
            expected_status=200,
            check=check_json_fields({
                "pages": list,
                "blocks": list,
                "text": str,
            }),
        ))

        # ── Шаг 5: Конвертация JSON ──────────────────────────────────
        steps.append(PipelineStep(
            name="Конвертация JSON",
            service="converter_validator",
            method="POST",
            path="/api/v1/converter/convert",
            port=8086,
            body={
                "task_id": "{task_id}",
                "version_id": "pipeline-test-version",
                "raw_json": {"pages": [], "blocks": [], "text": "тестовый текст"},
            },
            expected_status=200,
            check=check_json_field("data", dict),
        ))

        # ── Шаг 6: Сохранение документа в Registry ───────────────────
        steps.append(PipelineStep(
            name="Сохранение документа в Registry",
            service="registry",
            method="POST",
            path="/api/v1/registry/documents",
            port=8084,
            body={
                "title": "Тестовый документ pipeline",
                "doc_code": "PIPELINE-TEST-001",
                "source_type": "GOST",
                "era": "RF",
                "validity_status": "active",
            },
            expected_status=201,
            extract_keys=["doc_id"],
            check=check_json_field("data", dict),
            needs_auth=True,
        ))

        # ── Шаг 7: Построение чанков + индексация RAG Builder ────────
        steps.append(PipelineStep(
            name="Построение чанков и индексация",
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
                    "content": {"text": "Содержимое тестового документа"},
                }],
            },
            expected_status=200,
            check=check_json_field("status", str),
        ))

        # ── Шаг 8: Поиск по индексу RAG Search ───────────────────────
        steps.append(PipelineStep(
            name="Поиск по индексу RAG Search",
            service="rag_search",
            method="POST",
            path="/api/v1/rag/search",
            port=8091,
            body={
                "query": "тестовый документ",
                "top_k": 5,
            },
            expected_status=200,
            check=check_json_field("results", list),
        ))

        return steps
