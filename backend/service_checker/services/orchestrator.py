"""
PKB Neuroassistant — Orchestrator Service API Definitions.

Основано на: openapi.json orchestrator'а (порт 8000).
ВНИМАНИЕ: create document — через Registry, не через Orchestrator.
POST /api/v1/documents/ — не существует (только GET /documents/ — список).
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

# Вспомогательные константы для путей с path-параметрами
# ({{var}} = подстановка из контекста через _resolve_path)
_DOC = f"{API_PREFIX}/documents/{{{{doc_id}}}}"
_DRAFT = f"{API_PREFIX}/drafts/{{{{draft_id}}}}"
_TASK = f"{API_PREFIX}/tasks/{{{{task_id}}}}"
_PAGE = f"{_DOC}/pages/{{{{page_num}}}}"


def get_service_def() -> ServiceDef:
    """Вернуть полное описание Orchestrator Service."""

    endpoints = [
        # ── Health / Monitor ──
        EndpointDef("GET", f"{API_PREFIX}/system/health", "health",
            "Health Orchestrator",
            response_schema={"status": str}),
        EndpointDef("GET", f"{API_PREFIX}/monitor/metrics", "monitor",
            "Метрики",
            response_schema={"control_metrics": dict}),

        # ── Tasks ──
        EndpointDef("GET", f"{_TASK}/status", "tasks",
            "Статус задачи",
            response_schema={"status": str}),

        # ── Documents (только GET — список и операции с существующими) ──
        EndpointDef("GET", f"{API_PREFIX}/documents/", "documents",
            "Список документов",
            response_schema={"summary": dict, "items": list}),
        EndpointDef("GET", f"{API_PREFIX}/documents/queue", "documents",
            "Очередь документов",
            response_schema={"queue": list, "meta": dict}),
        EndpointDef("GET", f"{_DOC}", "documents",
            "Детали документа",
            response_schema={"document_id": (int, str)}),
        EndpointDef("DELETE", f"{_DOC}", "documents",
            "Удалить документ",
            response_schema={"document_id": (int, str)}),
        EndpointDef("GET", f"{_DOC}/status", "documents",
            "Статус документа",
            response_schema={"status": str}),
        EndpointDef("GET", f"{_DOC}/file", "documents",
            "Файл документа"),
        EndpointDef("GET", f"{_DOC}/history", "documents",
            "История изменений",
            response_schema={"history": list}),
        EndpointDef("GET", f"{_DOC}/errors", "documents",
            "Ошибки документа",
            response_schema={"errors": list}),
        EndpointDef("GET", f"{_DOC}/versions", "documents",
            "Список версий",
            response_schema={"versions": list}),
        EndpointDef("POST", f"{_DOC}/versions", "documents",
            "Загрузить версию",
            body={}),  # file upload, JSON body не требуется
        EndpointDef("POST", f"{_DOC}/approve", "documents",
            "Аппрув документа",
            body={"comment": "Утверждено тестом"},
            response_schema={"status": str}),
        EndpointDef("POST", f"{_DOC}/reprocess", "documents",
            "Переобработка", body={"mode": "full"},
            response_schema={"status": str, "task_id": (int, str)}),
        EndpointDef("GET", f"{_DOC}/pages", "documents",
            "Список страниц",
            response_schema={"pages": list}),
        EndpointDef("GET", f"{_PAGE}", "documents",
            "Получить страницу",
            response_schema={"page": dict}),
        EndpointDef("GET", f"{_PAGE}/text", "documents",
            "Текст страницы",
            response_schema={"blocks": list}),
        EndpointDef("GET", f"{_PAGE}/preview", "documents",
            "Превью страницы",
            response_schema={"page": dict}),
        EndpointDef("GET", f"{_DOC}/parameters", "documents",
            "Параметры документа",
            response_schema={"parameters": list}),

        # ── Search ──
        EndpointDef("POST", f"{API_PREFIX}/documents/search", "search",
            "Поиск документов", body={"query": "тест"},
            response_schema={"items": list}),
        EndpointDef("GET", f"{API_PREFIX}/documents/search", "search",
            "Поиск (GET)", params={"query": "тест"}),

        # ── Drafts (create draft → decide → document) ──
        EndpointDef("POST", f"{API_PREFIX}/drafts/", "drafts",
            "Создать черновик",
            body={"title": "Тестовый черновик", "content": "тест"},
            response_schema={"draft_id": (int, str)}),
        EndpointDef("GET", f"{API_PREFIX}/drafts/", "drafts",
            "Список черновиков",
            response_schema={"items": list}),
        EndpointDef("GET", f"{_DRAFT}", "drafts",
            "Детали черновика",
            response_schema={"draft_id": (int, str)}),
        EndpointDef("DELETE", f"{_DRAFT}", "drafts",
            "Удалить черновик",
            response_schema={"draft_id": (int, str)}),
        EndpointDef("PATCH", f"{_DRAFT}/decide", "drafts",
            "Решение по черновику",
            body={"decision": "approved", "comment": "ОК"},
            response_schema={"status": str}),
        EndpointDef("GET", f"{_DRAFT}/preview", "drafts",
            "Превью черновика"),
        EndpointDef("POST", f"{_DRAFT}/preview", "drafts",
            "Запустить превью",
            body={},
            response_schema={"status": str}),
        EndpointDef("GET", f"{_DRAFT}/preview/status", "drafts",
            "Статус превью",
            response_schema={"status": str}),
    ]

    return ServiceDef(
        service_key=SERVICE_KEY,
        display_name=DISPLAY_NAME,
        port=PORT,
        needs_auth=True,
        endpoints=endpoints,
        prepare_endpoints=[],
        depends_on=["auth", "registry", "query", "converter_validator", "parser", "rag_search"],
        base_data={},
    )
