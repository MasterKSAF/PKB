"""
PKB Neuroassistant — Orchestrator Service API Definitions.

Основано на: docs/api/orchestrator_service_api.md
"""

from __future__ import annotations

from .base import (
    EndpointDef,
    ServiceDef,
    API_PREFIX,
)

SERVICE_KEY = "orchestrator"
PORT = 8000
DISPLAY_NAME = "Orchestrator Service"

# Prepare-данные
PREPARE_DOCUMENT = {
    "title": "Тестовый документ Orchestra",
    "source_type": "OTHER",
    "content_hash": "abc123",
}


def get_service_def() -> ServiceDef:
    """Вернуть полное описание Orchestrator Service."""

    prepare_endpoints = [
        # Создать документ → context.task_id
        EndpointDef("POST", f"{API_PREFIX}/documents", "documents",
            "Загрузить документ (prepare)",
            body=PREPARE_DOCUMENT,
            extract_keys=["task_id"],
            response_schema={"task_id": str, "status": str},
            is_preparation=True,
            expected_status=201),
    ]

    endpoints = [
        # Health / Monitor
        EndpointDef("GET", f"{API_PREFIX}/monitor/health", "monitor",
            "Health Orchestrator",
            response_schema={"status": str}),
        EndpointDef("GET", f"{API_PREFIX}/monitor/metrics", "monitor",
            "Метрики",
            response_schema={"control_metrics": dict}),
        # Documents
        EndpointDef("POST", f"{API_PREFIX}/documents", "documents",
            "Загрузить документ",
            body=PREPARE_DOCUMENT,
            extract_keys=["task_id"],
            response_schema={"task_id": str, "status": str}),
        EndpointDef("GET", f"{API_PREFIX}/documents", "documents",
            "Список документов",
            response_schema={"summary": dict, "items": list}),
        EndpointDef("GET", f"{API_PREFIX}/documents/{{doc_id}}", "documents",
            "Детали документа",
            response_schema={"document_id": str}),
        EndpointDef("GET", f"{API_PREFIX}/documents/{{doc_id}}/status", "documents",
            "Статус документа",
            response_schema={"status": str}),
        EndpointDef("GET", f"{API_PREFIX}/documents/{{doc_id}}/file", "documents",
            "Файл документа"),
        EndpointDef("GET", f"{API_PREFIX}/documents/{{doc_id}}/history", "documents",
            "История изменений",
            response_schema={"history": list}),
        EndpointDef("GET", f"{API_PREFIX}/documents/{{doc_id}}/errors", "documents",
            "Ошибки документа",
            response_schema={"errors": list}),
        EndpointDef("GET", f"{API_PREFIX}/documents/{{doc_id}}/versions", "documents",
            "Список версий",
            response_schema={"versions": list}),
        EndpointDef("POST", f"{API_PREFIX}/documents/{{doc_id}}/versions", "documents",
            "Добавить версию", body={},
            response_schema={"version_id": (int, str)}),
        EndpointDef("POST", f"{API_PREFIX}/documents/{{doc_id}}/approve", "documents",
            "Аппрув документа",
            body={"comment": "Утверждено тестом"},
            response_schema={"status": str}),
        EndpointDef("POST", f"{API_PREFIX}/documents/{{doc_id}}/reprocess", "documents",
            "Переобработка", body={"mode": "full"},
            response_schema={"status": str, "task_id": (int, str)}),
        EndpointDef("DELETE", f"{API_PREFIX}/documents/{{doc_id}}", "documents",
            "Удалить документ",
            response_schema={"document_id": (int, str)}),
        EndpointDef("GET", f"{API_PREFIX}/documents/queue", "documents",
            "Очередь документов",
            response_schema={"queue": list, "meta": dict}),
        EndpointDef("GET", f"{API_PREFIX}/documents/{{doc_id}}/pages", "documents",
            "Список страниц",
            response_schema={"pages": list}),
        EndpointDef("GET", f"{API_PREFIX}/documents/{{doc_id}}/pages/{{page_num}}",
            "documents", "Получить страницу",
            response_schema={"page": dict}),
        EndpointDef("GET", f"{API_PREFIX}/documents/{{doc_id}}/pages/{{page_num}}/text",
            "documents", "Текст страницы",
            response_schema={"blocks": list}),
        EndpointDef("GET", f"{API_PREFIX}/documents/{{doc_id}}/pages/{{page_num}}/preview",
            "documents", "Превью страницы",
            response_schema={"page": dict}),
        EndpointDef("GET", f"{API_PREFIX}/documents/{{doc_id}}/parameters", "documents",
            "Параметры документа",
            response_schema={"parameters": list}),
        # Search
        EndpointDef("POST", f"{API_PREFIX}/documents/search", "search",
            "Поиск документов", body={"query": "тест"},
            response_schema={"items": list}),
        EndpointDef("GET", f"{API_PREFIX}/documents/search", "search",
            "Поиск (GET)", params={"query": "тест"}),
        # System health
        EndpointDef("GET", f"{API_PREFIX}/system/health", "health",
            "System health",
            response_schema={"status": str}),
    ]

    return ServiceDef(
        service_key=SERVICE_KEY,
        display_name=DISPLAY_NAME,
        port=PORT,
        needs_auth=True,
        endpoints=endpoints,
        prepare_endpoints=prepare_endpoints,
        depends_on=["auth", "registry", "query", "converter_validator", "parser", "rag_search"],
        base_data={},
    )
