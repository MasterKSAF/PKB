#!/usr/bin/env python3
"""
PKB Neuroassistant — Pipeline: document_processing

Полный цикл обработки документа: PDF-файл -> MinIO -> Parser -> Converter ->
Registry -> RAG Builder -> RAG Search.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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

# Константы для пайплайна
TEST_TASK_ID = 12345
TEST_DOC_ID = 1
TEST_VERSION_ID = "pipeline-test-version"


def _check_minio_upload(body: Optional[str], ctx: PipelineContext) -> Tuple[bool, str]:
    """Проверка загрузки в MinIO: сохраняем file_key в контекст."""
    ctx.set("file_key", TEST_PDF_KEY)
    return True, ""


def _check_converter(body: Optional[str], ctx: PipelineContext) -> Tuple[bool, str]:
    """Проверка конвертации: извлекаем document_id из ответа."""
    if not body:
        return False, "пустой ответ"
    import json
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return False, "ответ не JSON"
    doc_id = data.get("document_id")
    if not doc_id:
        return False, f"нет поля document_id в ответе"
    ctx.set("doc_id", doc_id)
    return True, ""


class DocumentProcessingPipeline(PipelineDef):
    """Пайплайн обработки документа."""

    name = "document_processing"
    description = "Полный цикл обработки документа"
    services = ["minio", "parser", "converter_validator", "registry", "rag_builder", "rag_search"]
    TEST_PDF_KEY = TEST_PDF_KEY
    TEST_PDF_PATH = TEST_PDF_PATH
    TEST_TASK_ID = TEST_TASK_ID

    def build_steps(self, context: PipelineContext) -> List[PipelineStep]:
        """Построить 8 шагов пайплайна document_processing."""
        steps: List[PipelineStep] = []

        pdf_path = Path(self.TEST_PDF_PATH)
        pdf_bytes = pdf_path.read_bytes()

        # -- Шаг 1: Загрузка PDF в MinIO --
        steps.append(PipelineStep(
            name="Загрузка PDF в MinIO",
            service="minio",
            method="PUT",
            path=f"/documents/{self.TEST_PDF_KEY}",
            port=MINIO_PORT,
            content=pdf_bytes,
            expected_status=200,
            check=_check_minio_upload,
        ))

        # -- Шаг 2: Запуск парсинга --
        steps.append(PipelineStep(
            name="Запуск парсинга",
            service="parser",
            method="POST",
            path="/api/v1/parser/process",
            port=8087,
            body={
                "task_id": self.TEST_TASK_ID,
                "version_id": TEST_VERSION_ID,
                "file_key": self.TEST_PDF_KEY,
            },
            expected_status=202,
            extract_keys=["task_id"],
            check=check_json_field("task_id", int),
        ))

        # -- Шаг 3: Статус парсинга (longpoll) --
        steps.append(PipelineStep(
            name="Статус парсинга (longpoll)",
            service="parser",
            method="GET",
            path=f"/api/v1/parser/process/{self.TEST_TASK_ID}/status",
            port=8087,
            expected_status=200,
            check=check_json_field("status", str),
        ))

        # -- Шаг 4: Результат парсинга --
        steps.append(PipelineStep(
            name="Результат парсинга",
            service="parser",
            method="GET",
            path=f"/api/v1/parser/process/{self.TEST_TASK_ID}/result",
            port=8087,
            expected_status=200,
            retry_on={409},
            retry_delay=2.0,
            retry_max=30,
            check=check_json_fields({
                "content": dict,
            }),
        ))

        # -- Шаг 5: Конвертация JSON --
        steps.append(PipelineStep(
            name="Конвертация JSON",
            service="converter_validator",
            method="POST",
            path="/api/v1/converter/convert",
            port=8086,
            body={
                "task_id": self.TEST_TASK_ID,
                "version_id": TEST_VERSION_ID,
                "raw_json": {"pages": [], "blocks": [], "text": "тестовый текст"},
            },
            expected_status=200,
            check=_check_converter,
        ))

        # -- Шаг 6: Сохранение документа в Registry --
        steps.append(PipelineStep(
            name="Сохранение документа в Registry",
            service="registry",
            method="POST",
            path="/api/v1/registry/documents/",
            port=8084,
            body={
                "title": "Тестовый документ pipeline",
                "doc_code": "PIPELINE-TEST-001",
                "source_type": "GOST",
                "era": "RF",
                "validity_status": "active",
            },
            expected_status=201,
            needs_auth=True,
        ))

        # -- Шаг 7: Построение чанков + индексация RAG Builder --
        steps.append(PipelineStep(
            name="Построение чанков и индексация",
            service="rag_builder",
            method="POST",
            path="/api/v1/rag/build",
            port=8090,
            body={
                "document_id": "00000000-0000-0000-0000-000000000001",
                "sections": [{
                    "section_id": 1,
                    "document_id": "00000000-0000-0000-0000-000000000001",
                    "clause": "1",
                    "level": 1,
                    "path": "1",
                    "page": 1,
                    "type": "section",
                    "content": {"text": "Содержимое тестового документа"},
                }],
            },
            expected_status=200,
        ))

        # -- Шаг 8: Поиск по индексу RAG Search --
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
