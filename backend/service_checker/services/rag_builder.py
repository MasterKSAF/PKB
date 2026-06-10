"""
PKB Neuroassistant — RAG Builder Service API Definitions.

Основано на: docs/api/rag_builder_service_api.md
"""

from __future__ import annotations

from .base import (
    EndpointDef,
    ServiceDef,
    API_PREFIX,
)

SERVICE_KEY = "rag_builder"
PORT = 8090
DISPLAY_NAME = "RAG Builder Service"


def get_service_def() -> ServiceDef:
    """Вернуть полное описание RAG Builder Service."""

    prepare_endpoints = [
        EndpointDef("POST", f"{API_PREFIX}/rag/build", "rag",
            "Построение чанков и индексация (prepare)",
            body={
                "document_id": "test-doc-001",
                "sections": [{
                    "section_id": 1, "document_id": "test-doc-001",
                    "clause": "1", "level": 1, "path": "1", "page": 1,
                    "type": "text",
                    "content": {"text": "Тестовое содержимое"},
                }],
            },
            response_schema={"status": str},
            is_preparation=True,
            expected_status=200),
    ]

    endpoints = [
        EndpointDef("GET", f"{API_PREFIX}/health", "health", "Health check сервиса",
            response_schema={"status": str}),
        EndpointDef("POST", f"{API_PREFIX}/rag/build", "rag",
            "Построение чанков и индексация",
            body={
                "document_id": "test-doc-001",
                "sections": [{
                    "section_id": 1, "document_id": "test-doc-001",
                    "clause": "1", "level": 1, "path": "1", "page": 1,
                    "type": "text",
                    "content": {"text": "Тестовое содержимое"},
                }],
            },
            response_schema={"status": str, "document_id": (int, str)}),
        EndpointDef("DELETE", f"{API_PREFIX}/rag/build/{{doc_id}}", "rag",
            "Удаление чанков из индекса",
            response_schema={"status": str}),
        EndpointDef("GET", f"{API_PREFIX}/rag/build/{{doc_id}}/status", "rag",
            "Статус индексации (longpoll)",
            response_schema={"status": str}),
    ]

    return ServiceDef(
        service_key=SERVICE_KEY,
        display_name=DISPLAY_NAME,
        port=PORT,
        needs_auth=False,
        endpoints=endpoints,
        prepare_endpoints=prepare_endpoints,
        depends_on=["registry"],
        base_data={},
    )
