"""
PKB Neuroassistant — Orchestrator Service API Definitions.

Основано на: openapi.json orchestrator'а.
Обновления (19.06.2026):
- OR-3c: approve — /validate/metadata + check-uniqueness
- OR-7: GET /drafts/{id} — document_id, version_id, is_new_document
- OR-11: POST /drafts — единая точка входа (draft-first)
- OR-12: PATCH /drafts/{id}/decide — approve/reject/proceed/stop_duplicate/force_new_version
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

_DOC = f"{API_PREFIX}/documents/{{doc_id}}"
_DRAFT = f"{API_PREFIX}/drafts/{{draft_id}}"
_TASK = f"{API_PREFIX}/tasks/{{task_id}}"

_AUTH_PORT = 8082


def get_service_def() -> ServiceDef:
    """Вернуть полное описание Orchestrator Service."""

    prepare_endpoints = [
        # 1. Получаем JWT токен от Auth Service
        EndpointDef("POST", f"{API_PREFIX}/auth/token", "auth",
            "Получение JWT токена (prepare)",
            body=TEST_CREDENTIALS,
            extract_keys=["access_token", "refresh_token"],
            is_preparation=True,
            expected_status=200,
            override_port=_AUTH_PORT),
        # 2. OR-11: POST /drafts — единая точка входа
        EndpointDef("POST", f"{API_PREFIX}/drafts/", "drafts",
            "Создать черновик (prepare)",
            form_body={"document_key": "coverage-doc-key", "title": "Coverage черновик"},
            extract_keys=["draft_id", "task_id"],
            is_preparation=True,
            expected_status=202),
    ]

    endpoints = [
        # Health
        EndpointDef("GET", f"{API_PREFIX}/system/health", "health",
            "Health Orchestrator",
            response_schema={"status": str}),
        EndpointDef("GET", f"{API_PREFIX}/monitor/metrics", "monitor",
            "Метрики",
            response_schema={"control_metrics": dict}),
        EndpointDef("GET", f"{API_PREFIX}/health", "health",
            "Health check Orchestrator",
            response_schema={"status": str}),

        # Tasks
        # OR-1: список задач (админка, read-only)
        EndpointDef("GET", f"{API_PREFIX}/tasks/", "tasks",
            "Список задач (админка read-only)",
            response_schema={"tasks": list, "meta": dict}),
        EndpointDef("GET", f"{_TASK}/status", "tasks",
            "Статус задачи",
            response_schema={"status": str}),

        # Documents (только GET — создание через Draft-first OR-11)
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

        # OR-11: Draft-first — единая точка входа
        # OR-14: MIME-ветвление — image/* → OCR, application/pdf → Parser
        EndpointDef("POST", f"{API_PREFIX}/drafts/", "drafts",
            "Создать черновик (единая точка входа, MIME-ветвление OCR/Parser)",
            form_body={"document_key": "test-doc-key", "title": "Тестовый черновик"},
            response_schema={"draft_id": int}),
        EndpointDef("GET", f"{API_PREFIX}/drafts/", "drafts",
            "Список черновиков",
            response_schema={"items": list}),
        # OR-7: document_id, version_id, is_new_document
        EndpointDef("GET", f"{_DRAFT}", "drafts",
            "Детали черновика",
            response_schema={"draft_id": int, "document_id": (int, type(None)),
                             "version_id": (int, type(None)), "is_new_document": bool}),
        EndpointDef("DELETE", f"{_DRAFT}", "drafts",
            "Удалить черновик",
            expected_status={200, 204}),
        # OR-12: action вместо decision
        EndpointDef("PATCH", f"{_DRAFT}/decide", "drafts",
            "Решение по черновику",
            body={"action": "approve", "comment": "OK"},
            expected_status={200, 409, 422}),
        # OR-3b: PATCH /drafts/{id}/metadata — обновление метаданных
        # Вместо локального пересчёта вызывает /validate/metadata
        EndpointDef("PATCH", f"{_DRAFT}/metadata", "drafts",
            "Обновление метаданных черновика",
            body={"title": "Обновлённый заголовок", "doc_code": "UPD-001"},
            response_schema={"draft_id": int, "title": str, "status": str}),
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
            expected_status={200, 404})
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
        warnings=[],
    )
