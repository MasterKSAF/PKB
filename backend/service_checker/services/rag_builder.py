"""
PKB Neuroassistant — RAG Builder Service API Definitions.

Основано на: docs/api/rag_builder_service_api.md
"""

from __future__ import annotations

from .base import (
    EndpointDef,
    ServiceDef,
    API_PREFIX,
    TEST_CREDENTIALS,
)


# Документ для prepare (создаётся через Registry, ID извлекается в контекст)
_PREPARE_DOC = {
    "title": "RAG Builder prepare document",
    "doc_code": "RAG-PREPARE-DOC",
    "source_type": "GOST",
    "era": "RF",
    "validity_status": "active",
}

SERVICE_KEY = "rag_builder"
PORT = 8090
DISPLAY_NAME = "RAG Builder Service"


def get_service_def() -> ServiceDef:
    """Вернуть полное описание RAG Builder Service."""

    prepare_endpoints = [
        # Получение JWT токена через Auth (prepare для авторизованных запросов)
        EndpointDef("POST", f"{API_PREFIX}/auth/token", "auth",
            "Получение JWT токена (prepare)",
            body=TEST_CREDENTIALS,
            extract_keys=["access_token", "refresh_token"],
            is_preparation=True,
            expected_status=200,
            override_port=8082),
        # Создание документа через Registry — ID попадёт в контекст как doc_id
        EndpointDef("POST", f"{API_PREFIX}/registry/documents/", "documents",
            "Создать документ в Registry (prepare для build)",
            body=_PREPARE_DOC,
            extract_keys=["doc_id"],
            response_schema={"data": dict},
            is_preparation=True,
            expected_status={201, 409},
            override_port=8084),
        EndpointDef("POST", f"{API_PREFIX}/rag/build", "rag",
            "Построение чанков и индексация (prepare)",
            body={
                "document_id": "{doc_id}",
                "sections": [{
                    "section_id": 1, "document_id": "{doc_id}",
                    "clause": "1", "level": 1, "path": "1", "page": 1,
                    "type": "section",
                    "content": {"text": "Тестовое содержимое"},
                }],
            },
            response_schema={"status": str},
            is_preparation=True,
            expected_status={200, 201}),
    ]

    endpoints = [
        EndpointDef("GET", f"{API_PREFIX}/health", "health", "Health check сервиса",
            response_schema={"status": str}),
        EndpointDef("POST", f"{API_PREFIX}/rag/build", "rag",
            "Построение чанков и индексация",
            body={
                "document_id": "{doc_id}",
                "sections": [{
                    "section_id": 1, "document_id": "{doc_id}",
                    "clause": "1", "level": 1, "path": "1", "page": 1,
                    "type": "section",
                    "content": {"text": "Тестовое содержимое"},
                }],
            },
            response_schema={"status": str}),
        EndpointDef("DELETE", f"{API_PREFIX}/rag/build/{{doc_id}}", "rag",
            "Удаление чанков из индекса",
            response_schema={"status": str}),
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
        warnings=[
            "⚠️ Документация не упоминает JWT, но RAG Builder требует bearer token. Исправлено: supervisord передаёт JWT_SECRET (RAG Builder) = JWT_SECRET_KEY (Auth).",
        ],
    )
