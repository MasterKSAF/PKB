#!/usr/bin/env python3
"""
PKB Neuroassistant — Pipeline: document_processing

Полный цикл обработки документа: PDF-файл -> MinIO -> Parser -> Converter ->
Registry -> RAG Builder -> RAG Search.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .base import (
    PipelineContext,
    PipelineDef,
    PipelineStep,
    check_json_field,
    check_json_fields,
    check_rag_search_results,
    s3_sign_headers,
    save_parser_result_as,
)

# Порт MinIO S3 API (обычно 9000)
MINIO_PORT = 19000

# Тестовый PDF-файл из каталога service_checker/pdf/ (путь относительно этого файла, а не CWD)
_HERE = Path(__file__).resolve().parent.parent
TEST_PDF_KEY = "test-document.pdf"
TEST_PDF_PATH = str(_HERE / "pdf" / "7bd97d737317a8a272bb18a405ab2d04.pdf")

# Константы для пайплайна
TEST_TASK_ID = 12345
TEST_DOC_ID = 1

# Тестовые учётные данные (admin — создаётся auth-сервисом при старте)
TEST_CREDENTIALS = {
    "username": "admin@example.com",
    "password": "Admin1234!",
}


def _check_minio_upload(body: Optional[str], ctx: PipelineContext) -> Tuple[bool, str]:
    """Проверка загрузки в MinIO: сохраняем file_key в контекст."""
    ctx.set("file_key", TEST_PDF_KEY)
    return True, f"file_key = {TEST_PDF_KEY}"


_save_parser_result = save_parser_result_as("parser_result")


def _check_converter(body: Optional[str], ctx: PipelineContext) -> Tuple[bool, str]:
    """Проверка конвертации: проверяем что ответ валидный JSON с task_id."""
    if not body:
        return False, "пустой ответ"
    import json
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return False, "ответ не JSON"
    if not data.get("task_id"):
        return False, "нет поля task_id в ответе"
    return True, f"task_id = {data.get('task_id')}"


class DocumentProcessingPipeline(PipelineDef):
    """Пайплайн обработки документа."""

    name = "document_processing"
    description = "Полный цикл обработки документа"
    services = ["auth", "minio", "parser", "converter_validator", "registry", "rag_builder", "rag_search"]
    TEST_PDF_KEY = TEST_PDF_KEY
    TEST_PDF_PATH = TEST_PDF_PATH
    TEST_TASK_ID = TEST_TASK_ID

    def build_steps(self, context: PipelineContext) -> List[PipelineStep]:
        """Построить 9 шагов пайплайна document_processing."""
        steps: List[PipelineStep] = []

        pdf_path = Path(self.TEST_PDF_PATH)
        pdf_bytes = pdf_path.read_bytes()

        # -- Шаг 1: Аутентификация (получаем токен для Registry) --
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

        # -- Шаг 2: Создание bucket в MinIO --
        bucket_url = f"http://127.0.0.1:{MINIO_PORT}/documents"
        bucket_headers = s3_sign_headers(
            method="PUT",
            url=bucket_url,
            access_key="minioadmin",
            secret_key="minioadmin",
        )
        steps.append(PipelineStep(
            name="Создание bucket documents",
            service="minio",
            method="PUT",
            path="/documents",
            port=MINIO_PORT,
            expected_status={200, 409},
            extra_headers=bucket_headers,
        ))

        # -- Шаг 3: Загрузка PDF в MinIO (S3 via AWS4-HMAC-SHA256) --
        minio_url = f"http://127.0.0.1:{MINIO_PORT}/documents/{self.TEST_PDF_KEY}"
        s3_headers = s3_sign_headers(
            method="PUT",
            url=minio_url,
            access_key="minioadmin",
            secret_key="minioadmin",
            body=pdf_bytes,
        )
        steps.append(PipelineStep(
            name="Загрузка PDF в MinIO",
            service="minio",
            method="PUT",
            path=f"/documents/{self.TEST_PDF_KEY}",
            port=MINIO_PORT,
            content=pdf_bytes,
            expected_status=200,
            extra_headers=s3_headers,
            check=_check_minio_upload,
        ))

        # -- Шаг 3: Запуск парсинга (PS-5: mode=full) --
        steps.append(PipelineStep(
            name="Запуск парсинга",
            service="parser",
            method="POST",
            path="/api/v1/parser/process",
            port=8087,
            body={
                "task_id": self.TEST_TASK_ID,
                "draft_id": 1,  # PS-3: обязательный draft_id
                "file_key": self.TEST_PDF_KEY,
                "version_id": "1",
                "mode": "full",  # PS-5: единый эндпоинт
            },
            expected_status=202,
            extract_keys=["task_id"],
            check=check_json_field("task_id", int),
        ))

        # -- Шаг 4: Статус парсинга (longpoll) --
        steps.append(PipelineStep(
            name="Статус парсинга (longpoll)",
            service="parser",
            method="GET",
            path=f"/api/v1/parser/process/{self.TEST_TASK_ID}/status",
            port=8087,
            expected_status=200,
            check=check_json_field("status", str),
        ))

        # -- Шаг 5: Результат парсинга --
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
            check=_save_parser_result,
        ))

        # -- Шаг 5a: Предпросмотр метаданных (CV-3) --
        steps.append(PipelineStep(
            name="Предпросмотр метаданных",
            service="converter_validator",
            method="POST",
            path="/api/v1/converter/preview",
            port=8086,
            body={
                "task_id": str(self.TEST_TASK_ID),
                "version_id": "1",
                "raw_json": "__INLINE__parser_result",
            },
            expected_status=200,
            check=check_json_fields({
                "doc_code": str,
                "title": str,
            }),
        ))

        # -- Шаг 5b (P1F-10): Валидация метаданных через /validate/metadata --
        # Вычисление бизнес-ключа после извлечения метаданных
        steps.append(PipelineStep(
            name="Валидация метаданных (бизнес-ключ)",
            service="converter_validator",
            method="POST",
            path="/api/v1/validate/metadata",
            port=8086,
            body={
                "title": "Тестовый документ",
                "doc_code": "TEST-P1F-10",
                "source_type": "GOST",
                "era": "RF",
                "year": 2026,
            },
            expected_status=200,
            check=check_json_fields({
                "title_hash_sha256": str,
                "title_key": str,
            }),
        ))

        # -- Шаг 5b (RG): Проверка уникальности документа в Registry --
        steps.append(PipelineStep(
            name="Проверка уникальности документа",
            service="registry",
            method="POST",
            path="/api/v1/registry/documents/import",
            port=8084,
            body={
                "title": "Тестовый документ",
                "doc_code": "TEST-P1F-10",
                "source_type": "GOST",
                "era": "RF",
            },
            expected_status={200, 422},  # 200=ok, 422=уже существует
            needs_auth=True,
        ))

        # -- Шаг 6: Конвертация JSON (CV-9: с version_id) --
        steps.append(PipelineStep(
            name="Конвертация JSON",
            service="converter_validator",
            method="POST",
            path="/api/v1/converter/convert",
            port=8086,
            body={
                "task_id": str(self.TEST_TASK_ID),
                "version_id": "1",  # CV-9: version_id обязателен
                "raw_json": "__INLINE__parser_result",
            },
            expected_status=200,
            check=_check_converter,
        ))

        # -- Шаг 7: Валидация документа (CV-8) --
        steps.append(PipelineStep(
            name="Валидация документа",
            service="converter_validator",
            method="POST",
            path="/api/v1/validate/document",
            port=8086,
            body={
                "task_id": str(self.TEST_TASK_ID),
                "version_id": "1",
                "raw_json": "__INLINE__parser_result",
            },
            expected_status=200,
            check=check_json_fields({
                "structure_valid": bool,
                "status": str,
            }),
        ))

        # -- Шаг 8: Сохранение документа в Registry --
        steps.append(PipelineStep(
            name="Сохранение документа в Registry",
            service="registry",
            method="POST",
            path="/api/v1/registry/documents",
            port=8084,
            body={
                "title": f"Тестовый документ pipeline {int(time.time())}",
                "doc_code": f"PIPELINE-TEST-{int(time.time())}",
                "source_type": "GOST",
                "era": "RF",
                "validity_status": "active",
                "mks_oks_code": "47.020",  # DB-9: классификатор
                "title_key": f"GOST|RF|PIPELINE-TEST-{int(time.time())}|2026",  # DB-28: бизнес-ключ
            },
            expected_status={201, 409},
            needs_auth=True,
            extract_keys=["doc_id"],
        ))

        # -- Шаг 7a (P1F-4/RG-10): Проверка preview_snapshot в документе --
        steps.append(PipelineStep(
            name="Проверка preview_snapshot в документе",
            service="registry",
            method="GET",
            path="/api/v1/registry/documents/{doc_id}",
            port=8084,
            expected_status=200,
            check=check_json_fields({
                "data.preview_snapshot": (dict, type(None)),
            }),
            needs_auth=True,
        ))

        # -- Шаг 8: Построение чанков + индексация RAG Builder --
        steps.append(PipelineStep(
            name="Построение чанков и индексация",
            service="rag_builder",
            method="POST",
            path="/api/v1/rag/build",
            port=8090,
            body={
                "document_id": TEST_DOC_ID,
                "sections": [{
                    "section_id": 1,
                    "document_id": TEST_DOC_ID,
                    "clause": "1",
                    "level": 1,
                    "path": "1",
                    "page": 1,
                    "type": "text",
                    "content": {"text": "Содержимое тестового документа"},
                }],
            },
            expected_status={200, 201, 202},  # RB-7: 201 — ресурс создан, 200/202 — асинхронный режим
            needs_auth=True,  # RAG Builder требует JWT (не отражено в docs)
        ))

        # -- Шаг 9: Поиск по индексу RAG Search (RS-6: без top_k, с valid_at) --
        steps.append(PipelineStep(
            name="Поиск по индексу RAG Search",
            service="rag_search",
            method="POST",
            path="/api/v1/rag/search",
            port=8091,
            body={
                "query": "тестовый документ",
                "valid_at": "2026-06-19",
                "filters": {"document_type": [], "category_ids": [], "document_ids": []},
            },
            expected_status=200,
            check=check_rag_search_results(),
        ))

        return steps
