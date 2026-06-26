"""
PKB Neuroassistant — RAG Builder Service API Definitions.

Основано на: docs/api/rag_builder_service_api.md
Обновления (19.06.2026):
- RB-7: Код ответа 201 (ресурс создан) или 202 (асинхронный запуск)
- RB-8: "completed" → "indexed"
"""

from __future__ import annotations

from .base import (
    EndpointDef,
    ServiceDef,
    API_PREFIX,
    TEST_CREDENTIALS,
)


SERVICE_KEY = "rag_builder"
PORT = 18090
DISPLAY_NAME = "RAG Builder Service"


def get_service_def() -> ServiceDef:
    """Вернуть полное описание RAG Builder Service."""

    prepare_endpoints = [
        EndpointDef("POST", f"{API_PREFIX}/auth/token", "auth",
            "Получение JWT токена (prepare)",
            body=TEST_CREDENTIALS,
            extract_keys=["access_token", "refresh_token"],
            is_preparation=True,
            expected_status=200,
            override_port=18082),
        EndpointDef("POST", f"{API_PREFIX}/registry/documents/", "documents",
            "Создать документ в Registry (prepare для build)",
            body={
                "title": "RAG Builder prepare document",
                "doc_code": "RAG-PREPARE-{timestamp}",
                "source_type": "GOST",
                "era": "RF",
                "validity_status": "active",
            },
            extract_keys=["doc_id"],
            response_schema={"data": dict},
            is_preparation=True,
            expected_status={201, 409},
            override_port=18084),
        EndpointDef("POST", f"{API_PREFIX}/rag/build", "rag",
            "Построение чанков и индексация (prepare)",
            body={
                "document_id": "{doc_id}",
                "sections": [{
                    "section_id": "{section_id}",
                    "document_id": "{doc_id}",
                    "clause": "1", "level": 1, "path": "1", "page": 1,
                    "type": "text",
                    "content": {"text": "Тестовое содержимое"},
                }],
            },
            response_schema={"status": str},
            is_preparation=True,
            expected_status={200, 201, 202}),  # RB-7: 201 (ресурс создан) или 202
    ]

    endpoints = [
        EndpointDef("GET", f"{API_PREFIX}/health", "health", "Health check сервиса",
            response_schema={"status": str}),
        # RB-7: 202 для асинхронного запуска
        EndpointDef("POST", f"{API_PREFIX}/rag/build", "rag",
            "Построение чанков и индексация",
            body={
                "document_id": "{doc_id}",
                "sections": [{
                    "section_id": "{section_id}",
                    "document_id": "{doc_id}",
                    "clause": "1", "level": 1, "path": "1", "page": 1,
                    "type": "text",
                    "content": {"text": "Тестовое содержимое"},
                }],
            },
            response_schema={"status": str}),
        EndpointDef("DELETE", f"{API_PREFIX}/rag/build/{{doc_id}}", "rag",
            "Удаление чанков из индекса",
            response_schema={"status": str}),
        # RB-8: "indexed" вместо "completed"
        # P2I-1: "partially_indexed" при chunk_count_actual < expected
        EndpointDef("GET", f"{API_PREFIX}/rag/build/{{doc_id}}/status", "rag",
            "Статус индексации (longpoll)",
            params={"longpoll": 0},
            response_schema={"status": str}),

    ]

    return ServiceDef(
        service_key=SERVICE_KEY,
        display_name=DISPLAY_NAME,
        port=PORT,
        needs_auth=False,
        endpoints=endpoints,
        prepare_endpoints=prepare_endpoints,
        depends_on=["registry", "auth"],
        base_data={},
        warnings=[],
    )
