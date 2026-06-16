#!/usr/bin/env python3
"""
PKB Neuroassistant — Pipeline: multi_document_cross_search

Загрузка 2 разных документов → индексация обоих → кросс-поиск → удаление одного → фильтрация.

Проверяет работу RAG Search с несколькими документами.
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
    s3_sign_headers,
)

MINIO_PORT = 9000
_HERE = Path(__file__).resolve().parent.parent
TEST_PDF_KEY = "test-document.pdf"
TEST_PDF_PATH = str(_HERE / "pdf" / "7bd97d737317a8a272bb18a405ab2d04.pdf")

TEST_CREDENTIALS = {
    "username": "admin@example.com",
    "password": "Admin1234!",
}

TEST_TASK_ID_1 = 20001
TEST_TASK_ID_2 = 20002


class MultiDocumentCrossSearchPipeline(PipelineDef):
    """Пайплайн: мульти-документный поиск — 2 документа → кросс-поиск → удаление → фильтрация."""

    name = "multi_document_cross_search"
    description = "Мульти-документный поиск: 2 документа → индексация → кросс-поиск → удаление → фильтрация"
    services = ["auth", "minio", "parser", "converter_validator", "registry", "rag_builder", "rag_search"]
    TEST_PDF_KEY = TEST_PDF_KEY
    TEST_PDF_PATH = TEST_PDF_PATH

    def build_steps(self, context: PipelineContext) -> List[PipelineStep]:
        """Построить 19 шагов пайплайна multi_document_cross_search."""
        steps: List[PipelineStep] = []
        ts = int(time.time())

        pdf_bytes = b""
        pdf_path = Path(self.TEST_PDF_PATH)
        if pdf_path.exists():
            pdf_bytes = pdf_path.read_bytes()

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

        # ── Шаг 2: Создание bucket в MinIO ────────────────────────────
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

        # ── Шаг 3: Загрузка PDF #1 в MinIO ────────────────────────────
        pdf_key_1 = f"multi-doc-1-{ts}.pdf"
        minio_url_1 = f"http://127.0.0.1:{MINIO_PORT}/documents/{pdf_key_1}"
        s3_headers_1 = s3_sign_headers(
            method="PUT",
            url=minio_url_1,
            access_key="minioadmin",
            secret_key="minioadmin",
            body=pdf_bytes,
        )
        steps.append(PipelineStep(
            name="Загрузка PDF #1 в MinIO",
            service="minio",
            method="PUT",
            path=f"/documents/{pdf_key_1}",
            port=MINIO_PORT,
            content=pdf_bytes,
            expected_status=200,
            extra_headers=s3_headers_1,
        ))

        # ── Шаг 4: Запуск парсинга #1 ─────────────────────────────────
        steps.append(PipelineStep(
            name="Запуск парсинга #1",
            service="parser",
            method="POST",
            path="/api/v1/parser/process",
            port=8087,
            body={
                "task_id": TEST_TASK_ID_1,
                "file_key": pdf_key_1,
                "version_id": "1",
            },
            expected_status=202,
            extract_keys=["task_id"],
            check=check_json_field("task_id", int),
        ))

        # ── Шаг 5: Статус парсинга #1 ─────────────────────────────────
        steps.append(PipelineStep(
            name="Статус парсинга #1 (longpoll)",
            service="parser",
            method="GET",
            path=f"/api/v1/parser/process/{TEST_TASK_ID_1}/status",
            port=8087,
            expected_status=200,
            check=check_json_field("status", str),
        ))

        # ── Шаг 6: Результат парсинга #1 ──────────────────────────────
        steps.append(PipelineStep(
            name="Результат парсинга #1",
            service="parser",
            method="GET",
            path=f"/api/v1/parser/process/{TEST_TASK_ID_1}/result",
            port=8087,
            expected_status=200,
            retry_on={409},
            retry_delay=2.0,
            retry_max=30,
            check=check_json_fields({"document": dict}),
        ))

        # ── Шаг 7: Конвертация #1 ─────────────────────────────────────
        steps.append(PipelineStep(
            name="Конвертация JSON #1",
            service="converter_validator",
            method="POST",
            path="/api/v1/converter/convert",
            port=8086,
            body={
                "task_id": str(TEST_TASK_ID_1),
                "version_id": "1",
                "raw_json": {"pages": [], "blocks": [], "text": f"Текст документа 1 {ts}"},
            },
            expected_status=200,
        ))

        # ── Шаг 8: Сохранение документа #1 в Registry ─────────────────
        steps.append(PipelineStep(
            name="Сохранение документа #1 в Registry",
            service="registry",
            method="POST",
            path="/api/v1/registry/documents/",
            port=8084,
            body={
                "title": f"Multi-doc тест 1 {ts}",
                "doc_code": f"MULTI1-{ts}",
                "source_type": "GOST",
                "era": "RF",
                "validity_status": "active",
            },
            expected_status={201, 409},
            needs_auth=True,
            extract_keys=["doc_id_1"],
        ))

        # ── Шаг 9: Построение индекса для документа #1 ────────────────
        steps.append(PipelineStep(
            name="Построение индекса #1",
            service="rag_builder",
            method="POST",
            path="/api/v1/rag/build",
            port=8090,
            body={
                "document_id": "{doc_id_1}",
                "sections": [{
                    "section_id": 1,
                    "document_id": "{doc_id_1}",
                    "clause": "1",
                    "level": 1,
                    "path": "1",
                    "page": 1,
                    "type": "section",
                    "content": {"text": f"Содержимое документа 1 {ts}"},
                }],
            },
            expected_status={200, 201},
            needs_auth=True,
            check=check_json_field("status", str),
        ))

        # ── Шаг 10: Загрузка PDF #2 в MinIO ───────────────────────────
        pdf_key_2 = f"multi-doc-2-{ts}.pdf"
        minio_url_2 = f"http://127.0.0.1:{MINIO_PORT}/documents/{pdf_key_2}"
        s3_headers_2 = s3_sign_headers(
            method="PUT",
            url=minio_url_2,
            access_key="minioadmin",
            secret_key="minioadmin",
            body=pdf_bytes,
        )
        steps.append(PipelineStep(
            name="Загрузка PDF #2 в MinIO",
            service="minio",
            method="PUT",
            path=f"/documents/{pdf_key_2}",
            port=MINIO_PORT,
            content=pdf_bytes,
            expected_status=200,
            extra_headers=s3_headers_2,
        ))

        # ── Шаг 11-13: Парсинг #2 ─────────────────────────────────────
        steps.append(PipelineStep(
            name="Запуск парсинга #2",
            service="parser",
            method="POST",
            path="/api/v1/parser/process",
            port=8087,
            body={
                "task_id": TEST_TASK_ID_2,
                "file_key": pdf_key_2,
                "version_id": "1",
            },
            expected_status=202,
            extract_keys=["task_id_2"],
            check=check_json_field("task_id", int),
        ))

        steps.append(PipelineStep(
            name="Статус парсинга #2 (longpoll)",
            service="parser",
            method="GET",
            path=f"/api/v1/parser/process/{TEST_TASK_ID_2}/status",
            port=8087,
            expected_status=200,
            check=check_json_field("status", str),
        ))

        steps.append(PipelineStep(
            name="Результат парсинга #2",
            service="parser",
            method="GET",
            path=f"/api/v1/parser/process/{TEST_TASK_ID_2}/result",
            port=8087,
            expected_status=200,
            retry_on={409},
            retry_delay=2.0,
            retry_max=30,
            check=check_json_fields({"document": dict}),
        ))

        # ── Шаг 14-16: Конвертация #2 + Registry #2 + Build #2 ────────
        steps.append(PipelineStep(
            name="Конвертация JSON #2",
            service="converter_validator",
            method="POST",
            path="/api/v1/converter/convert",
            port=8086,
            body={
                "task_id": str(TEST_TASK_ID_2),
                "version_id": "1",
                "raw_json": {"pages": [], "blocks": [], "text": f"Текст документа 2 {ts}"},
            },
            expected_status=200,
        ))

        steps.append(PipelineStep(
            name="Сохранение документа #2 в Registry",
            service="registry",
            method="POST",
            path="/api/v1/registry/documents/",
            port=8084,
            body={
                "title": f"Multi-doc тест 2 {ts}",
                "doc_code": f"MULTI2-{ts}",
                "source_type": "GOST",
                "era": "RF",
                "validity_status": "active",
            },
            expected_status={201, 409},
            needs_auth=True,
            extract_keys=["doc_id_2"],
        ))

        # ── Шаг 16: Построение индекса #2 ──────────────────────────────
        steps.append(PipelineStep(
            name="Построение индекса #2",
            service="rag_builder",
            method="POST",
            path="/api/v1/rag/build",
            port=8090,
            body={
                "document_id": "{doc_id_2}",
                "sections": [{
                    "section_id": 1,
                    "document_id": "{doc_id_2}",
                    "clause": "1",
                    "level": 1,
                    "path": "1",
                    "page": 1,
                    "type": "section",
                    "content": {"text": f"Содержимое документа 2 {ts}"},
                }],
            },
            expected_status={200, 201},
            needs_auth=True,
            check=check_json_field("status", str),
        ))

        # ── Шаг 17: Поиск ────────────────────────────────────────────
        steps.append(PipelineStep(
            name="Поиск по общему запросу",
            service="rag_search",
            method="POST",
            path="/api/v1/rag/search",
            port=8091,
            body={
                "query": "тестовый документ multi-doc",
                "top_k": 10,
            },
            expected_status=200,
            check=check_json_field("results", list),
        ))

        # ── Шаг 18: Удаление первого документа ────────────────────────
        steps.append(PipelineStep(
            name="Удаление документа #1 из Registry",
            service="registry",
            method="DELETE",
            path="/api/v1/registry/documents/{doc_id_1}/",
            port=8084,
            expected_status=200,
            needs_auth=True,
        ))

        # ── Шаг 19: Поиск после удаления ──────────────────────────────
        steps.append(PipelineStep(
            name="Поиск после удаления документа #1",
            service="rag_search",
            method="POST",
            path="/api/v1/rag/search",
            port=8091,
            body={
                "query": "тестовый документ multi-doc",
                "top_k": 10,
            },
            expected_status=200,
            check=check_json_field("results", list),
        ))

        return steps
