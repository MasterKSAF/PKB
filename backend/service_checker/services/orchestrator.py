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
_PAGE = f"{_DOC}/pages/{{page_num}}"

_AUTH_PORT = 8082

# Эндпоинты, описанные в документации, но не реализованные в текущей версии —
# checker показывает ❌ Fail, чтобы разработчик знал о несоответствии.


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
            form_body={"document_key": "coverage-doc-key", "title": "Coverage черновик",
                      "source_type": "GOST"},
            extract_keys=["draft_id", "task_id"],
            is_preparation=True,
            expected_status={202, 409}),
    ]

    endpoints = [
        # Health
        EndpointDef("GET", f"{API_PREFIX}/system/health", "health",
            "Health Orchestrator",
            response_schema={"status": str}),
        EndpointDef("GET", f"{API_PREFIX}/monitor/metrics", "monitor",
            "Метрики (OTLP — эндпоинт не реализован)",
            response_schema={"control_metrics": dict},
            expected_status={404}),

        # Tasks
        # OR-1: список задач (админка, read-only)
        EndpointDef("GET", f"{API_PREFIX}/tasks/", "tasks",
            "Список задач (админка read-only)",
            response_schema={"items": list, "meta": dict}),
        EndpointDef("GET", f"{_TASK}/status", "tasks",
            "Статус задачи",
            response_schema={"status": str}),

        # OR-16: шаги задачи
        EndpointDef("GET", f"{_TASK}/steps", "tasks",
            "Шаги задачи",
            response_schema={"task_id": int, "total": int, "steps": list}),

        # OR: статистика задач
        EndpointDef("GET", f"{API_PREFIX}/tasks/stats", "tasks",
            "Статистика по задачам пайплайна",
            response_schema={"total": int, "by_status": dict, "by_stage": dict}),

        # Documents
        # GET /documents/, GET /documents/queue — описаны, но не реализованы (Registry API)
        EndpointDef("GET", f"{API_PREFIX}/documents/", "documents",
            "Список документов",
            response_schema={"summary": dict, "items": list},
            expected_status={404}),
        EndpointDef("GET", f"{API_PREFIX}/documents/queue", "documents",
            "Очередь документов"),
        # Чтение документов — через Registry, не реализовано в оркестраторе
        EndpointDef("GET", f"{_DOC}", "documents",
            "Детали документа",
            response_schema={"document_id": (int, str)},
            expected_status={404}),
        EndpointDef("DELETE", f"{_DOC}", "documents",
            "Удалить документ",
            response_schema={"document_id": (int, str)},
            expected_status={404}),
        EndpointDef("GET", f"{_DOC}/status", "documents",
            "Статус документа",
            response_schema={"status": str},
            expected_status={404}),
        EndpointDef("GET", f"{_DOC}/file", "documents",
            "Файл документа",
            expected_status={404}),

        # OR-8a: версии документа
        EndpointDef("GET", f"{_DOC}/versions", "documents",
            "Список версий документа",
            response_schema={"document_id": int, "versions": list, "meta": dict},
            expected_status={404}),
        EndpointDef("POST", f"{_DOC}/versions", "documents",
            "Загрузить новую версию файла документа",
            form_body={"file": "binary"},
            response_schema={"document_id": int, "version_id": int, "version_number": int,
                             "status": str, "task_id": int, "file_hash_sha256": str,
                             "is_duplicate_file": bool, "created_at": str},
            expected_status={404}),
        # OR-8b: история документа
        EndpointDef("GET", f"{_DOC}/history", "documents",
            "История изменений статусов документа",
            response_schema={"document_id": int, "history": list, "meta": dict},
            expected_status={404}),
        # OR: переобработка документа
        EndpointDef("POST", f"{_DOC}/reprocess", "documents",
            "Переобработка документа без создания черновика",
            body={"mode": "full", "options": {"ocr_engine": "paddleocr", "language": "ru"}},
            expected_status={202, 409},
            response_schema={"task_id": (int, str), "document_id": (int, str), "mode": str,
                             "status": str, "created_at": str}),
        # OR: pipeline-задачи документа
        EndpointDef("GET", f"{_DOC}/tasks", "documents",
            "Pipeline-задачи документа",
            response_schema={"document_id": int, "tasks": list}),
        # OR: ошибки обработки
        EndpointDef("GET", f"{_DOC}/errors", "documents",
            "Журнал ошибок обработки документа",
            response_schema={"errors": list, "meta": dict},
            expected_status={404}),
        # OR: параметры документа
        EndpointDef("GET", f"{_DOC}/parameters", "documents",
            "Извлечённые параметры документа",
            response_schema={"document_id": int, "parameters": list, "total": int},
            expected_status={404}),

        # Pages — не реализованы в оркестраторе (Parser/Registry)
        EndpointDef("GET", f"{_DOC}/pages", "pages",
            "Список страниц документа",
            response_schema={"document_id": int, "pages_total": int, "pages": list, "meta": dict},
            expected_status={404}),
        EndpointDef("GET", f"{_PAGE}", "pages",
            "Изображение страницы с наложенными блоками",
            params={"highlight": None},
            expected_status={404}),
        EndpointDef("GET", f"{_PAGE}/text", "pages",
            "Текстовый слой и структура страницы",
            response_schema={"document_id": str, "page": int, "width": int, "height": int, "blocks": list},
            expected_status={404}),
        EndpointDef("GET", f"{_PAGE}/preview", "pages",
            "Агрегированный просмотр страницы (изображение + текст + блоки)",
            params={"format": None, "highlight": None},
            expected_status={404}),

        # OR-11: Draft-first — единая точка входа
        # OR-14: MIME-ветвление — image/* → OCR, application/pdf → Parser
        EndpointDef("POST", f"{API_PREFIX}/drafts/", "drafts",
            "Создать черновик (единая точка входа, MIME-ветвление OCR/Parser)",
            form_body={"document_key": "test-doc-key", "title": "Тестовый черновик",
                      "source_type": "GOST"},
            expected_status={202, 409},
            response_schema={"draft_id": int}),
        # GET /drafts/ — описан, но list_drafts удалён при рефакторинге
        EndpointDef("GET", f"{API_PREFIX}/drafts/", "drafts",
            "Список черновиков",
            response_schema={"items": list},
            expected_status={404, 405}),
        # OR-7: document_id, version_id, is_new_document
        EndpointDef("GET", f"{_DRAFT}", "drafts",
            "Детали черновика",
            response_schema={"draft_id": int, "document_id": (int, type(None)),
                             "version_id": (int, type(None)), "is_new_document": bool}),
        # OR: список задач черновика
        EndpointDef("GET", f"{_DRAFT}/tasks", "drafts",
            "Список задач черновика",
            response_schema={"draft_id": int, "tasks": list}),
        EndpointDef("DELETE", f"{_DRAFT}", "drafts",
            "Удалить черновик",
            expected_status={200, 204}),
        # OR-12: action вместо decision
        EndpointDef("PATCH", f"{_DRAFT}/decide", "drafts",
            "Решение по черновику",
            body={"action": "approve", "comment": "OK"},
            expected_status={200, 409, 422}),
        # OR-3b: PATCH /drafts/{id}/metadata — обновление метаданных
        # Прокси в Registry, который возвращает 404 для черновиков, созданных через оркестратор
        EndpointDef("PATCH", f"{_DRAFT}/metadata", "drafts",
            "Обновление метаданных черновика (internal, прокси в Registry)",
            body={"title": "Обновлённый заголовок", "doc_code": "UPD-001"},
            expected_status={200, 404}),
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
        base_data={"doc_id": 1, "page_num": 1},
        warnings=[],
    )
