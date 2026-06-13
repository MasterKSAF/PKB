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
    TEST_CREDENTIALS,
)

SERVICE_KEY = "orchestrator"
PORT = 8081
DISPLAY_NAME = "Orchestrator Service"

# Вспомогательные константы для путей с path-параметрами
# ({{var}} = подстановка из контекста через _resolve_path)
_DOC = f"{API_PREFIX}/documents/{{doc_id}}"
_DRAFT = f"{API_PREFIX}/drafts/{{draft_id}}"
_TASK = f"{API_PREFIX}/tasks/{{task_id}}"
_PAGE = f"{_DOC}/pages/{{page_num}}"

# Порт Auth Service для prepare-шага получения JWT
_AUTH_PORT = 8082


def get_service_def() -> ServiceDef:
    """Вернуть полное описание Orchestrator Service."""

    # ── Prepare-эндпоинты (выполняются перед основными) ──────────────
    prepare_endpoints = [
        # 1. Получаем JWT токен от Auth Service (через override_port=8082)
        EndpointDef("POST", f"{API_PREFIX}/auth/token", "auth",
            "Получение JWT токена (prepare)",
            body=TEST_CREDENTIALS,
            extract_keys=["access_token", "refresh_token"],
            is_preparation=True,
            expected_status=200,
            override_port=_AUTH_PORT),
        # 2. Создаём черновик — получаем draft_id и task_id
        EndpointDef("POST", f"{API_PREFIX}/drafts/", "drafts",
            "Создать черновик (prepare)",
            form_body={"document_key": "coverage-doc-key", "title": "Coverage черновик"},
            extract_keys=["draft_id", "task_id"],
            is_preparation=True,
            expected_status=202),
    ]

    # ── Основные эндпоинты ──────────────────────────────────────────
    endpoints = [
        # ── Health / Monitor ──
        EndpointDef("GET", f"{API_PREFIX}/system/health", "health",
            "Health Orchestrator",
            response_schema={"status": str}),
        EndpointDef("GET", f"{API_PREFIX}/monitor/metrics", "monitor",
            "Метрики",
            response_schema={"control_metrics": dict}),

        # ── Tasks ──
        # task_id подставляется из prepare (POST /drafts/)
        EndpointDef("GET", f"{_TASK}/status", "tasks",
            "Статус задачи",
            response_schema={"status": str}),

        # ── Documents (только GET — список и операции с существующими) ──
        # doc_id=1 из base_data, сервис возвращает mock-данные для любого doc_id
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
            body={},  # file upload, JSON body не требуется
            expected_status={200, 202, 422}),
        EndpointDef("POST", f"{_DOC}/approve", "documents",
            "Аппрув документа",
            body={"comment": "Утверждено тестом"},
            response_schema={"status": str}),
        EndpointDef("POST", f"{_DOC}/reprocess", "documents",
            "Переобработка", body={"mode": "full"},
            response_schema={"status": str, "task_id": int}),
        EndpointDef("GET", f"{_DOC}/pages", "documents",
            "Список страниц",
            response_schema={"pages": list}),
        EndpointDef("GET", f"{_PAGE}", "documents",
            "Получить страницу",
            response_schema={"page": int, "document_id": str, "blocks": list}),
        EndpointDef("GET", f"{_PAGE}/text", "documents",
            "Текст страницы",
            response_schema={"blocks": list}),
        EndpointDef("GET", f"{_PAGE}/preview", "documents",
            "Превью страницы",
            response_schema={"page": int, "document_id": str, "blocks": list}),
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
        # Спецификация: multipart/form-data с file, document_key, опционально title
        EndpointDef("POST", f"{API_PREFIX}/drafts/", "drafts",
            "Создать черновик",
            form_body={"document_key": "test-doc-key", "title": "Тестовый черновик"},
            response_schema={"draft_id": int}),
        EndpointDef("GET", f"{API_PREFIX}/drafts/", "drafts",
            "Список черновиков",
            response_schema={"items": list}),
        # draft_id подставляется из prepare
        EndpointDef("GET", f"{_DRAFT}", "drafts",
            "Детали черновика",
            response_schema={"draft_id": int}),
        EndpointDef("DELETE", f"{_DRAFT}", "drafts",
            "Удалить черновик",
            expected_status={200, 204}),
        EndpointDef("PATCH", f"{_DRAFT}/decide", "drafts",
            "Решение по черновику",
            body={"decision": "approved", "comment": "ОК"},
            expected_status={200, 409, 422}),
        EndpointDef("GET", f"{_DRAFT}/preview", "drafts",
            "Превью черновика",
            expected_status={200, 404}),
        EndpointDef("POST", f"{_DRAFT}/preview", "drafts",
            "Запустить превью",
            body={},
            expected_status={200, 202, 404}),
        EndpointDef("GET", f"{_DRAFT}/preview/status", "drafts",
            "Статус превью",
            params={"longpoll": 0},
            response_schema={"status": str},
            expected_status={200, 404}),
    ]

    return ServiceDef(
        service_key=SERVICE_KEY,
        display_name=DISPLAY_NAME,
        port=PORT,
        needs_auth=True,
        endpoints=endpoints,
        prepare_endpoints=prepare_endpoints,
        depends_on=["auth", "registry", "query", "converter_validator", "parser", "rag_search"],
        base_data={"doc_id": "1", "page_num": 1},
    )
