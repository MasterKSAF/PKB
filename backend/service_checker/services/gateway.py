"""
PKB Neuroassistant — Gateway Service API Definitions.

Gateway — отдельный mock-сервис, тестируется независимо.
Определения основаны строго на openapi.json gateway (порт 8080).
"""

from __future__ import annotations

import time

from .base import (
    EndpointDef,
    ServiceDef,
    API_PREFIX,
)

SERVICE_KEY = "gateway"
PORT = 8080
DISPLAY_NAME = "Gateway Service"

# Gateway-specific credentials (пароль admin123 из SEED_USERS мока)
_CREDS = {"username": "admin@example.com", "password": "admin123"}
_PREP_SESSION = {"title": "Тестовая сессия Gateway", "project_id": 1}
_PREP_MESSAGE = {"text": "Тестовое сообщение", "content": "Тестовое сообщение"}
_PREP_DOC = {"title": "Тестовый документ Gateway", "doc_code": f"GW.{int(time.time())%100000}", "source_type": "GOST"}
_PREP_CLASSIF = {"classifier_system": "MKS", "code": f"CK.{int(time.time())%100000}", "full_name": "Тестовый классификатор Gateway", "status": "active"}
_PREP_TERM = {"raw_term": f"term.{int(time.time())%100000}", "standard_term": f"term.{int(time.time())%100000}", "normalized_value": f"term.{int(time.time())%100000}", "term_type": "abbreviation"}


def get_service_def() -> ServiceDef:
    """Определение Gateway Service на основе openapi.json mock'а."""

    prepare_endpoints = [
        EndpointDef("POST", f"{API_PREFIX}/auth/token", "auth",
            "Получение JWT токена через Gateway",
            body=_CREDS, extract_keys=["access_token", "refresh_token"],
            is_preparation=True, expected_status=200),
        EndpointDef("GET", f"{API_PREFIX}/auth/me", "auth",
            "Профиль пользователя через Gateway",
            is_preparation=True, expected_status=200),
        EndpointDef("POST", f"{API_PREFIX}/chat/sessions", "chat",
            "Создать сессию (prepare)",
            body=_PREP_SESSION, extract_keys=["session_id"],
            is_preparation=True, expected_status=201),
        EndpointDef("POST", f"{API_PREFIX}/chat/sessions/{{session_id}}/messages", "chat",
            "Отправить сообщение (prepare)",
            body=_PREP_MESSAGE, extract_keys=["message_id"],
            is_preparation=True, expected_status=200),

        # Registry prepare (создаём ID для registry endpoints)
        EndpointDef("POST", f"{API_PREFIX}/registry/classifiers", "classifiers",
            "Создать классификатор (prepare)",
            body=_PREP_CLASSIF, extract_keys=["code"],
            response_schema={"data": dict, "data.code": str},
            is_preparation=True, expected_status={201, 409}),
        EndpointDef("POST", f"{API_PREFIX}/registry/documents", "registry_documents",
            "Создать документ (prepare)",
            body=_PREP_DOC, extract_keys=["doc_id"],
            response_schema={"data": dict, "data.id": int},
            is_preparation=True, expected_status={201, 409}),
        EndpointDef("POST", f"{API_PREFIX}/registry/terminology", "terminology",
            "Создать термин (prepare)",
            body=_PREP_TERM, extract_keys=["term_id"],
            response_schema={"data": dict, "data.id": int},
            is_preparation=True, expected_status={201, 409}),

        # Create category (prepare category_id)
        EndpointDef("POST", f"{API_PREFIX}/registry/categories", "categories",
            "Создать категорию (prepare)",
            body={"name": f"Категория_{int(time.time())%100000}"},
            extract_keys=["category_id"],
            is_preparation=True, expected_status={201, 409}),

        # Chat project (prepare project_id)
        EndpointDef("POST", f"{API_PREFIX}/chat/projects", "chat",
            "Создать проект (prepare)",
            body={"code": "TEST-PRJ", "name": "Тестовый проект", "status": "active"}, extract_keys=["project_id"],
            is_preparation=True, expected_status={201, 409}),

        # Admin: create user (prepare user_id — через seed user_id=1)
        EndpointDef("POST", f"{API_PREFIX}/admin/users", "admin",
            "Создать пользователя (prepare)",
            body={"email": f"gw_{int(time.time()*100)%100000}@test.com",
                  "full_name": "Gateway User",
                  "password": "test123", "roles": ["engineer"]},
            extract_keys=["user_id"],
            is_preparation=True, expected_status={201, 409}),

        # Orchestrator-style draft (prepare draft_id from orchestrator)
        EndpointDef("POST", f"{API_PREFIX}/drafts", "drafts",
            "Создать черновик через orchestrator (prepare)",
            body={"document_key": "prepare-doc-key", "title": "prepare-draft", "source_type": "GOST"},
            extract_keys=["draft_id", "task_id"],
            is_preparation=True, expected_status={202}),

        # Registry-style draft (prepare reg_draft_id отдельно)
        EndpointDef("POST", f"{API_PREFIX}/registry/drafts", "registry_documents",
            "Создать черновик (prepare)",
            body={"file_key": f"prepare-file-{int(time.time()*100)%100000}.pdf",
                  "document_key": f"prepare-draft-key-{int(time.time()*100)%100000}"},
            extract_keys=["reg_draft_id"],
            is_preparation=True, expected_status={201, 409}),
    ]

    endpoints = [
        # ── Health ──
        EndpointDef("GET", f"{API_PREFIX}/system/health", "health", "System health",
            response_schema={"status": str, "version": str, "services": dict}),
        EndpointDef("GET", f"{API_PREFIX}/monitor/health", "health", "Monitor health"),
        EndpointDef("GET", f"{API_PREFIX}/monitor/metrics", "health", "Metrics"),

        # ── Auth (без DELETE) ──
        EndpointDef("POST", f"{API_PREFIX}/auth/token", "auth", "Получение JWT токена",
            body=_CREDS, response_schema={"access_token": str, "token_type": str}),
        EndpointDef("GET", f"{API_PREFIX}/auth/me", "auth", "Профиль пользователя",
            response_schema={"user_id": str, "full_name": str, "role": str}),
        EndpointDef("POST", f"{API_PREFIX}/auth/refresh", "auth", "Обновление токена",
            body={"refresh_token": "{refresh_token}"}),
        EndpointDef("POST", f"{API_PREFIX}/auth/revoke", "auth", "Отзыв токена",
            body={"refresh_token": "{refresh_token}"}),
        EndpointDef("GET", f"{API_PREFIX}/admin/users", "admin", "Список пользователей",
            params={"page": 1, "page_size": 10}),
        EndpointDef("POST", f"{API_PREFIX}/admin/users", "admin", "Создать пользователя",
            body={"email": "test@test.com", "full_name": "Test User", "password": "test123", "roles": ["engineer"]},
            expected_status={201, 409}),
        EndpointDef("GET", f"{API_PREFIX}/admin/users/{{user_id}}", "admin", "Получить пользователя",
            response_schema={"user_id": str}),
        EndpointDef("PUT", f"{API_PREFIX}/admin/users/{{user_id}}", "admin", "Обновить пользователя",
            body={"full_name": "Updated User", "roles": ["engineer"]}),
        EndpointDef("PATCH", f"{API_PREFIX}/admin/users/{{user_id}}", "admin", "Изменить роль",
            body={"role": "admin"}),
        EndpointDef("GET", f"{API_PREFIX}/admin/roles", "admin", "Список ролей"),
        EndpointDef("POST", f"{API_PREFIX}/admin/roles", "admin", "Создать роль",
            body={"name": "viewer", "permissions": ["documents:read"]}),
        EndpointDef("GET", f"{API_PREFIX}/admin/audit", "admin", "Журнал аудита"),
        EndpointDef("POST", f"{API_PREFIX}/internal/auth/validate", "auth", "Валидация токена",
            body={"access_token": "{access_token}"}, response_schema={"valid": bool}),

        # ── Chat (без DELETE) ──
        EndpointDef("POST", f"{API_PREFIX}/chat/sessions", "chat", "Создать сессию",
            body=_PREP_SESSION, response_schema={"session_id": int, "title": str}),
        EndpointDef("GET", f"{API_PREFIX}/chat/sessions", "chat", "Список сессий"),
        EndpointDef("GET", f"{API_PREFIX}/chat/sessions/{{session_id}}", "chat", "Детали сессии"),
        EndpointDef("PUT", f"{API_PREFIX}/chat/sessions/{{session_id}}", "chat", "Обновить сессию",
            body={"title": "Обновлённая сессия"}),
        EndpointDef("GET", f"{API_PREFIX}/chat/history", "chat", "История чатов"),
        EndpointDef("GET", f"{API_PREFIX}/chat/history/export", "chat", "Экспорт истории"),
        EndpointDef("POST", f"{API_PREFIX}/chat/projects", "chat", "Создать проект",
            body={"code": "TEST-PRJ", "name": "Тестовый проект", "status": "active"}),
        EndpointDef("GET", f"{API_PREFIX}/chat/projects", "chat", "Список проектов"),
        EndpointDef("GET", f"{API_PREFIX}/chat/projects/{{project_id}}", "chat", "Детали проекта"),
        EndpointDef("PUT", f"{API_PREFIX}/chat/projects/{{project_id}}", "chat", "Обновить проект",
            body={"title": "Обновлённый проект"}),
        EndpointDef("POST", f"{API_PREFIX}/chat/sessions/{{session_id}}/messages", "chat", "Отправить сообщение",
            body=_PREP_MESSAGE, extract_keys=["message_id"],
            response_schema={"message_id": str}),
        EndpointDef("GET", f"{API_PREFIX}/chat/sessions/{{session_id}}/messages", "chat", "История сообщений"),
        EndpointDef("GET", f"{API_PREFIX}/chat/sessions/{{session_id}}/messages/last", "chat", "Последние сообщения"),
        EndpointDef("GET", f"{API_PREFIX}/chat/sessions/{{session_id}}/messages/{{message_id}}", "chat", "Детали сообщения"),
        EndpointDef("POST", f"{API_PREFIX}/chat/sessions/{{session_id}}/context", "chat", "Управление контекстом",
            body={"action": "add_documents", "params": {"document_ids": []}}),
        EndpointDef("POST", f"{API_PREFIX}/chat/sessions/{{session_id}}/export", "chat", "Экспорт сессии",
            body={"format": "json"}),
        EndpointDef("POST", f"{API_PREFIX}/chat/feedback", "chat", "Отправить отзыв",
            body={"session_id": "{session_id}", "message_id": "{message_id}", "rating": 5},
            response_schema={"status": str}),

        # ── Documents (orchestrator-style, без DELETE) ──
        EndpointDef("GET", f"{API_PREFIX}/documents", "documents", "Список документов"),
        EndpointDef("GET", f"{API_PREFIX}/documents/queue", "documents", "Очередь документов"),
        EndpointDef("GET", f"{API_PREFIX}/documents/{{doc_id}}", "documents", "Детали документа",
            response_schema={"id": int, "title": str}),
        EndpointDef("GET", f"{API_PREFIX}/documents/{{doc_id}}/status", "documents", "Статус документа"),
        EndpointDef("GET", f"{API_PREFIX}/documents/{{doc_id}}/file", "documents", "Файл документа"),
        EndpointDef("GET", f"{API_PREFIX}/documents/{{doc_id}}/history", "documents", "История документа"),
        EndpointDef("GET", f"{API_PREFIX}/documents/{{doc_id}}/errors", "documents", "Ошибки документа"),
        EndpointDef("GET", f"{API_PREFIX}/documents/{{doc_id}}/versions", "documents", "Версии документа"),
        EndpointDef("POST", f"{API_PREFIX}/documents/{{doc_id}}/versions", "documents", "Создать версию",
            form_body={"comment": "Новая версия"}),
        EndpointDef("POST", f"{API_PREFIX}/documents/{{doc_id}}/approve", "documents", "Утвердить документ"),
        EndpointDef("POST", f"{API_PREFIX}/documents/{{doc_id}}/reprocess", "documents", "Переобработать документ"),
        EndpointDef("GET", f"{API_PREFIX}/documents/{{doc_id}}/pages", "documents", "Страницы документа"),
        EndpointDef("GET", f"{API_PREFIX}/documents/{{doc_id}}/pages/{{page_num}}", "documents", "Детали страницы"),
        EndpointDef("GET", f"{API_PREFIX}/documents/{{doc_id}}/pages/{{page_num}}/text", "documents", "Текст страницы"),
        EndpointDef("GET", f"{API_PREFIX}/documents/{{doc_id}}/pages/{{page_num}}/preview", "documents", "Превью страницы"),
        EndpointDef("GET", f"{API_PREFIX}/documents/{{doc_id}}/parameters", "documents", "Параметры документа"),

        # ── Tasks ──
        EndpointDef("GET", f"{API_PREFIX}/tasks/{{task_id}}/status", "tasks", "Статус задачи",
            response_schema={"status": str}),

        # ── Drafts (orchestrator-style, без DELETE) ──
        EndpointDef("POST", f"{API_PREFIX}/drafts", "drafts", "Создать черновик",
            body={"document_key": "test-doc-key", "title": "Тестовый черновик", "source_type": "GOST"},
            response_schema={"draft_id": int}),
        EndpointDef("GET", f"{API_PREFIX}/drafts", "drafts", "Список черновиков"),
        EndpointDef("GET", f"{API_PREFIX}/drafts/{{draft_id}}", "drafts", "Детали черновика"),
        EndpointDef("PATCH", f"{API_PREFIX}/drafts/{{draft_id}}/decide", "drafts", "Решение по черновику",
            body={"decision": "approved", "comment": "ОК"},
            expected_status={200, 409}),
        EndpointDef("GET", f"{API_PREFIX}/drafts/{{draft_id}}/preview", "drafts", "Превью черновика"),
        EndpointDef("POST", f"{API_PREFIX}/drafts/{{draft_id}}/preview", "drafts", "Запустить превью", body={}),
        EndpointDef("GET", f"{API_PREFIX}/drafts/{{draft_id}}/preview/status", "drafts", "Статус превью"),

        # ── Text ──
        EndpointDef("POST", f"{API_PREFIX}/text/search", "text", "Поиск текста", body={"text": "тест"}),
        EndpointDef("POST", f"{API_PREFIX}/text/ask", "text", "Задать вопрос", body={"text": "тест"}),

        # ── Registry: Classifiers (без DELETE) ──
        EndpointDef("GET", f"{API_PREFIX}/registry/classifiers", "classifiers", "Список классификаторов",
            response_schema={"data": list, "meta": dict}),
        EndpointDef("POST", f"{API_PREFIX}/registry/classifiers", "classifiers", "Создать классификатор",
            body=_PREP_CLASSIF, response_schema={"data": dict},
            expected_status={201, 409}),
        EndpointDef("GET", f"{API_PREFIX}/registry/classifiers/tree", "classifiers", "Дерево классификаторов"),
        EndpointDef("GET", f"{API_PREFIX}/registry/classifiers/{{code}}", "classifiers", "Получить классификатор",
            response_schema={"data": dict}),
        EndpointDef("PUT", f"{API_PREFIX}/registry/classifiers/{{code}}", "classifiers", "Обновить классификатор",
            body={"full_name": "Обновлённый"}),
        EndpointDef("PATCH", f"{API_PREFIX}/registry/classifiers/{{code}}", "classifiers", "Частичное обновление",
            body={"status": "inactive"}),
        EndpointDef("POST", f"{API_PREFIX}/registry/classifiers/import", "classifiers", "Импорт классификаторов",
            body=[{"code": "IMP.TEST", "full_name": "Тестовый импорт"}]),
        EndpointDef("GET", f"{API_PREFIX}/registry/classifiers/quarantine", "classifiers", "Карантин классификаторов"),
        EndpointDef("POST", f"{API_PREFIX}/registry/classifiers/quarantine/{{pending_id}}/accept", "classifiers", "Принять из карантина"),
        EndpointDef("POST", f"{API_PREFIX}/registry/classifiers/quarantine/{{pending_id}}/reject", "classifiers", "Отклонить из карантина"),
        EndpointDef("POST", f"{API_PREFIX}/registry/classifiers/validate", "classifiers", "Валидация",
            body={"classification": {"mks_oks_code": "47.020"}},
            response_schema={"data": dict, "data.udk_valid": bool}),

        # ── Registry: Terminology (без DELETE) ──
        EndpointDef("GET", f"{API_PREFIX}/registry/terminology", "terminology", "Список терминов"),
        EndpointDef("POST", f"{API_PREFIX}/registry/terminology", "terminology", "Создать термин",
            body=_PREP_TERM, response_schema={"data": dict}),
        EndpointDef("GET", f"{API_PREFIX}/registry/terminology/{{term_id}}", "terminology", "Получить термин"),
        EndpointDef("PUT", f"{API_PREFIX}/registry/terminology/{{term_id}}", "terminology", "Обновить термин",
            body={"standard_term": "обновлённый термин"}),
        EndpointDef("GET", f"{API_PREFIX}/registry/terminology/normalize", "terminology", "Нормализация",
            params={"term": "тест"}),
        EndpointDef("POST", f"{API_PREFIX}/registry/terminology/import", "terminology", "Импорт терминов",
            body=[{"raw_term": "test.import"}]),

        # ── Registry: Documents (без DELETE) ──
        EndpointDef("GET", f"{API_PREFIX}/registry/documents", "registry_documents", "Список документов"),
        EndpointDef("POST", f"{API_PREFIX}/registry/documents", "registry_documents", "Создать документ",
            body=_PREP_DOC, response_schema={"data": dict}),
        EndpointDef("GET", f"{API_PREFIX}/registry/documents/{{doc_id}}", "registry_documents", "Получить документ",
            response_schema={"data": dict}),
        EndpointDef("PUT", f"{API_PREFIX}/registry/documents/{{doc_id}}", "registry_documents", "Обновить документ",
            body={"title": "Обновлённый"}),
        EndpointDef("PATCH", f"{API_PREFIX}/registry/documents/{{doc_id}}/status", "registry_documents", "Изменить статус",
            body={"status": "archived"}),
        EndpointDef("GET", f"{API_PREFIX}/registry/documents/{{doc_id}}/history", "registry_documents", "История документа"),
        EndpointDef("GET", f"{API_PREFIX}/registry/documents/{{doc_id}}/succession", "registry_documents", "Преемственность"),
        EndpointDef("GET", f"{API_PREFIX}/registry/documents/{{doc_id}}/sections", "registry_documents", "Разделы документа"),
        EndpointDef("GET", f"{API_PREFIX}/registry/documents/export", "registry_documents", "Экспорт документов"),
        EndpointDef("POST", f"{API_PREFIX}/registry/documents/import", "registry_documents", "Импорт документов",
            body=[{"title": "Тестовый импорт", "doc_code": "IMP.DOC"}]),
        EndpointDef("POST", f"{API_PREFIX}/registry/documents/check-uniqueness", "registry_documents", "Проверка уникальности",
            body={"title": "Тест", "doc_code": "TEST"}),
        EndpointDef("POST", f"{API_PREFIX}/registry/drafts", "registry_documents", "Создать черновик (registry)",
            body={"file_key": "test-file.pdf", "document_key": f"test-draft-{int(time.time())%100000}"}),
        EndpointDef("GET", f"{API_PREFIX}/registry/drafts", "registry_documents", "Список черновиков (registry)"),
        EndpointDef("GET", f"{API_PREFIX}/registry/drafts/{{reg_draft_id}}", "registry_documents", "Детали черновика (registry)"),
        EndpointDef("GET", f"{API_PREFIX}/registry/drafts/{{reg_draft_id}}/preview", "registry_documents", "Превью черновика (registry)"),
        EndpointDef("PATCH", f"{API_PREFIX}/registry/drafts/{{reg_draft_id}}/status", "registry_documents", "Статус черновика (registry)",
            body={"status": "archived"}),

        # ── Registry: Categories (без DELETE) ──
        EndpointDef("GET", f"{API_PREFIX}/registry/categories", "categories", "Список категорий"),
        EndpointDef("POST", f"{API_PREFIX}/registry/categories", "categories", "Создать категорию",
            body={"name": f"Категория_{int(time.time())%100000}_main"}),
        EndpointDef("GET", f"{API_PREFIX}/registry/categories/{{category_id}}", "categories", "Детали категории"),
        EndpointDef("PUT", f"{API_PREFIX}/registry/categories/{{category_id}}", "categories", "Обновить категорию",
            body={"name": "Обновлённая категория"}),

        # ── Registry: Common ──
        EndpointDef("GET", f"{API_PREFIX}/registry/common/stats", "common", "Статистика"),
        EndpointDef("GET", f"{API_PREFIX}/registry/common/enums", "common", "Справочники"),

        # ────────────────────────────────────────────────────────────────────────────
        # DELETE — в самом конце, чтобы не убивать данные раньше времени
        # ────────────────────────────────────────────────────────────────────────────
        EndpointDef("DELETE", f"{API_PREFIX}/admin/users/{{user_id}}", "admin", "Деактивировать пользователя"),
        EndpointDef("DELETE", f"{API_PREFIX}/chat/sessions/{{session_id}}", "chat", "Удалить сессию"),
        EndpointDef("DELETE", f"{API_PREFIX}/chat/projects/{{project_id}}", "chat", "Удалить проект"),
        EndpointDef("DELETE", f"{API_PREFIX}/documents/{{doc_id}}", "documents", "Удалить документ"),
        EndpointDef("DELETE", f"{API_PREFIX}/drafts/{{draft_id}}", "drafts", "Удалить черновик"),
        EndpointDef("DELETE", f"{API_PREFIX}/registry/classifiers/{{code}}", "classifiers", "Удалить классификатор"),
        EndpointDef("DELETE", f"{API_PREFIX}/registry/terminology/{{term_id}}", "terminology", "Удалить термин"),
        EndpointDef("DELETE", f"{API_PREFIX}/registry/documents/{{doc_id}}", "registry_documents", "Удалить документ"),
        EndpointDef("DELETE", f"{API_PREFIX}/registry/drafts/{{reg_draft_id}}", "registry_documents", "Удалить черновик (registry)"),
        EndpointDef("DELETE", f"{API_PREFIX}/registry/categories/{{category_id}}", "categories", "Удалить категорию"),
    ]

    return ServiceDef(
        service_key=SERVICE_KEY,
        display_name=DISPLAY_NAME,
        port=PORT,
        needs_auth=False,
        endpoints=endpoints,
        prepare_endpoints=prepare_endpoints,
        depends_on=[],
        base_data={"page_num": 1, "pending_id": 1, "user_id": 1},
        warnings=[
            "Gateway — отдельный mock-сервис, тестируется независимо от других сервисов.",
            "Эндпоинты и prepare определены строго по openapi.json mock'а.",
        ],
    )
