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

SERVICE_KEY = "rag_builder"
PORT = 8090
DISPLAY_NAME = "RAG Builder Service"


def get_service_def() -> ServiceDef:
    """Вернуть полное описание RAG Builder Service."""

    prepare_endpoints = [
        # Получение JWT токена через Auth (prepare для авторизованных запросов)
        # ⚠️ Документация не упоминает JWT, но реальный сервис требует bearer token
        EndpointDef("POST", f"{API_PREFIX}/auth/token", "auth",
            "Получение JWT токена (prepare)",
            body=TEST_CREDENTIALS,
            extract_keys=["access_token", "refresh_token"],
            is_preparation=True,
            expected_status=200,
            override_port=8082),
        EndpointDef("POST", f"{API_PREFIX}/rag/build", "rag",
            "Построение чанков и индексация (prepare)",
            body={
                "document_id": 1,
                "sections": [{
                    "section_id": 1, "document_id": 1,
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
                "document_id": 1,
                "sections": [{
                    "section_id": 1, "document_id": 1,
                    "clause": "1", "level": 1, "path": "1", "page": 1,
                    "type": "text",
                    "content": {"text": "Тестовое содержимое"},
                }],
            },
            response_schema={"status": str, "document_id": int}),
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
        warnings=[
            "⚠️ Документация не упоминает JWT, но реальный RAG Builder требует bearer token. Эндпоинты /rag/build возвращают 401 без него.",
            "⚠️ RAG Builder падал при старте: alembic migration 20260614_0002 не применилась — FK document_id UUID vs registry.documents.id BIGINT. Migration пропущена, таблица создана вручную с BIGINT document_id.",
            "⚠️ Подключена заглушка docker/patch_rag_tables.py — при full-report/coverage/patch-rag проверяет и создаёт таблицы, если их нет.",
        ],
    )
