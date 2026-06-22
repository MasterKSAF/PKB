"""
PKB Neuroassistant — Gateway Service API Definitions.

Основано на: GW-12 актуализация маршрутизации (19.06.2026).
Убраны: /pages/*, /monitor/*
Добавлены: /analyse/*, /health, /meridian/*, /files/*, /external/*, /registry/categories/*
Префиксы переименованы → /api/v1/registry/*
"""

from __future__ import annotations

from .base import (
    EndpointDef,
    ServiceDef,
    API_PREFIX,
    TEST_CREDENTIALS,
    GATEWAY_CREDENTIALS,
)

SERVICE_KEY = "gateway"
PORT = 8080
DISPLAY_NAME = "Gateway Service"


def get_service_def() -> ServiceDef:
    """Вернуть полное описание Gateway Service (агрегирующий прокси)."""

    prepare_endpoints = [
        # 1. Получаем JWT токен через Gateway (не напрямую Auth),
        #    чтобы Gateway Mock сохранил токен в своём _access_token_map.
        #    Пароль из SEED_USERS (admin123), а не из env (Admin1234!),
        #    т.к. Gateway Mock не читает DEFAULT_ADMIN_PASSWORD.
        EndpointDef("POST", f"{API_PREFIX}/auth/token", "auth",
            "Получение JWT токена (prepare)",
            body=GATEWAY_CREDENTIALS,
            extract_keys=["access_token", "refresh_token"],
            is_preparation=True,
            expected_status=200),
    ]

    endpoints = [
        # ── System Health ──
        EndpointDef("GET", f"{API_PREFIX}/health", "health",
            "Health check Gateway",
            response_schema={"status": str}),
        EndpointDef("GET", f"{API_PREFIX}/system/health", "health",
            "System health",
            response_schema={"status": str}),

        # ── Auth (прокси) ──
        EndpointDef("POST", f"{API_PREFIX}/auth/token", "auth",
            "Получение JWT токена",
            body=GATEWAY_CREDENTIALS,
            extract_keys=["access_token", "refresh_token"],
            response_schema={"access_token": str}),
        EndpointDef("GET", f"{API_PREFIX}/auth/me", "auth",
            "Профиль пользователя",
            response_schema={"user_id": str}),
        EndpointDef("POST", f"{API_PREFIX}/auth/refresh", "auth",
            "Обновление токена",
            body={"refresh_token": "{refresh_token}"},
            response_schema={"access_token": str}),
        EndpointDef("POST", f"{API_PREFIX}/auth/revoke", "auth",
            "Отзыв токена",
            body={"refresh_token": "{refresh_token}"},
            response_schema={"message": str}),

        # ── Admin (прокси на Auth) ──
        EndpointDef("GET", f"{API_PREFIX}/admin/users", "admin",
            "Список пользователей",
            params={"page": 1, "page_size": 10},
            response_schema={"users": list}),
        EndpointDef("POST", f"{API_PREFIX}/admin/users", "admin",
            "Создать пользователя",
            body={"email": "test@test.com", "full_name": "Test", "password": "Test1234!", "roles": ["engineer"]},
            expected_status={201, 409}),
        EndpointDef("GET", f"{API_PREFIX}/admin/users/{{user_id}}", "admin",
            "Получить пользователя"),
        EndpointDef("PATCH", f"{API_PREFIX}/admin/users/{{user_id}}", "admin",
            "Обновить пользователя (roles[])",
            body={"roles": ["engineer"], "is_active": True},
            response_schema={"user_id": str}),
        EndpointDef("DELETE", f"{API_PREFIX}/admin/users/{{user_id}}", "admin",
            "Деактивировать пользователя"),
        EndpointDef("GET", f"{API_PREFIX}/admin/roles", "admin",
            "Список ролей",
            response_schema={"roles": list}),
        EndpointDef("POST", f"{API_PREFIX}/admin/roles", "admin",
            "Создать роль",
            body={"name": "viewer", "permissions": ["documents:read"]},
            expected_status={201, 409}),
        EndpointDef("GET", f"{API_PREFIX}/admin/audit", "admin",
            "Журнал аудита",
            params={"page": 1, "page_size": 10},
            response_schema={"events": list}),

        # ── Registry: Classifiers ──
        EndpointDef("GET", f"{API_PREFIX}/registry/classifiers/", "classifiers",
            "Список классификаторов",
            params={"page": 1, "page_size": 10},
            response_schema={"data": list}),
        EndpointDef("POST", f"{API_PREFIX}/registry/classifiers/", "classifiers",
            "Создать классификатор",
            body={"classifier_system": "MKS", "code": "99.001", "full_name": "Тест"},
            extract_keys=["classifier_code"],
            expected_status={201, 409}),
        EndpointDef("GET", f"{API_PREFIX}/registry/classifiers/tree/", "classifiers",
            "Дерево классификаторов",
            params={"classifier_system": "MKS"},
            response_schema={"data": list}),
        EndpointDef("GET", f"{API_PREFIX}/registry/classifiers/{{classifier_code}}",
            "classifiers", "Получить классификатор",
            params={"classifier_system": "MKS"}),
        EndpointDef("PUT", f"{API_PREFIX}/registry/classifiers/{{classifier_code}}",
            "classifiers", "Обновить классификатор",
            params={"classifier_system": "MKS"},
            body={"full_name": "Обновлённый"}),
        EndpointDef("PATCH", f"{API_PREFIX}/registry/classifiers/{{classifier_code}}",
            "classifiers", "Частичное обновление",
            params={"classifier_system": "MKS"},
            body={"status": "inactive"}),
        EndpointDef("DELETE", f"{API_PREFIX}/registry/classifiers/{{classifier_code}}",
            "classifiers", "Удалить классификатор",
            params={"classifier_system": "MKS"}),
        EndpointDef("POST", f"{API_PREFIX}/registry/classifiers/import",
            "classifiers", "Импорт (file upload)",
            expected_status={400, 422}),
        EndpointDef("GET", f"{API_PREFIX}/registry/classifiers/pending",
            "classifiers", "Карантин",
            response_schema={"data": list}),
        EndpointDef("POST", f"{API_PREFIX}/registry/classifiers/pending/{{pending_id}}/accept",
            "classifiers", "Принять из карантина",
            body={"parent_code": "01.040", "full_name": "Принятый"}),
        EndpointDef("POST", f"{API_PREFIX}/registry/classifiers/pending/{{pending_id}}/reject",
            "classifiers", "Отклонить из карантина",
            body={"admin_comment": "Отклонено"}),
        EndpointDef("POST", f"{API_PREFIX}/registry/classifiers/validate",
            "classifiers", "Валидация классификации",
            body={"classification": {"mks_oks_code": "47.020", "okstu_code": None, "udk_code": "629.5.021"}},
            response_schema={"data": dict}),

        # ── Registry: Categories (GW-12: добавлено) ──
        EndpointDef("GET", f"{API_PREFIX}/registry/categories/", "categories",
            "Список категорий",
            response_schema={"data": list}),
        EndpointDef("POST", f"{API_PREFIX}/registry/categories/", "categories",
            "Создать категорию",
            body={"name": "Тестовая категория", "slug": "test-category"},
            expected_status={201, 409},
            extract_keys=["category_id"]),
        EndpointDef("GET", f"{API_PREFIX}/registry/categories/{{category_id}}",
            "categories", "Получить категорию"),
        EndpointDef("PUT", f"{API_PREFIX}/registry/categories/{{category_id}}",
            "categories", "Обновить категорию",
            body={"name": "Обновлённая категория"}),
        EndpointDef("DELETE", f"{API_PREFIX}/registry/categories/{{category_id}}",
            "categories", "Удалить категорию"),

        # ── Registry: Terminology ──
        EndpointDef("GET", f"{API_PREFIX}/registry/terminology/", "terminology",
            "Список терминов",
            params={"page": 1, "page_size": 10},
            response_schema={"data": list}),
        EndpointDef("POST", f"{API_PREFIX}/registry/terminology/", "terminology",
            "Создать термин",
            body={"raw_term": "Тест", "standard_term": "Тест", "normalized_value": "тест"},
            extract_keys=["term_id"],
            expected_status={201, 409}),
        EndpointDef("GET", f"{API_PREFIX}/registry/terminology/{{term_id}}",
            "terminology", "Получить термин"),
        EndpointDef("PUT", f"{API_PREFIX}/registry/terminology/{{term_id}}",
            "terminology", "Обновить термин",
            body={"definition": "Обновлённое определение"}),
        EndpointDef("DELETE", f"{API_PREFIX}/registry/terminology/{{term_id}}",
            "terminology", "Удалить термин"),
        EndpointDef("GET", f"{API_PREFIX}/registry/terminology/normalize/",
            "terminology", "Нормализовать термин",
            params={"term": "Тест"}),
        EndpointDef("POST", f"{API_PREFIX}/registry/terminology/import",
            "terminology", "Импорт (file upload)",
            expected_status={400, 422}),

        # ── Registry: Documents ──
        EndpointDef("GET", f"{API_PREFIX}/registry/documents/", "documents",
            "Список документов",
            params={"page": 1, "page_size": 10},
            response_schema={"data": list}),
        EndpointDef("POST", f"{API_PREFIX}/registry/documents/", "documents",
            "Создать документ",
            body={"title": "Тестовый документ", "doc_code": "TEST-001",
                  "source_type": "GOST", "era": "RF", "validity_status": "active"},
            extract_keys=["doc_id"],
            expected_status={201, 409}),
        EndpointDef("GET", f"{API_PREFIX}/registry/documents/{{doc_id}}",
            "documents", "Получить документ",
            response_schema={"data": dict}),
        EndpointDef("PUT", f"{API_PREFIX}/registry/documents/{{doc_id}}",
            "documents", "Обновить документ",
            body={"title": "Обновлённый"}),
        EndpointDef("PATCH", f"{API_PREFIX}/registry/documents/{{doc_id}}/status",
            "documents", "Обновить статус (internal)",
            body={"status": "uploaded"}),
        EndpointDef("GET", f"{API_PREFIX}/registry/documents/{{doc_id}}/history",
            "documents", "История статусов"),
        EndpointDef("GET", f"{API_PREFIX}/registry/documents/{{doc_id}}/succession/",
            "documents", "Цепочка преемственности"),
        EndpointDef("DELETE", f"{API_PREFIX}/registry/documents/{{doc_id}}",
            "documents", "Удалить документ"),
        EndpointDef("GET", f"{API_PREFIX}/registry/documents/export",
            "documents", "Экспорт (CSV)"),
        EndpointDef("POST", f"{API_PREFIX}/registry/documents/import",
            "documents", "Импорт (file upload)",
            expected_status={400, 422}),

        # ── Registry: Search (RG-8: BM25) ──
        EndpointDef("GET", f"{API_PREFIX}/registry/search", "search",
            "Поиск по реестру (BM25)",
            params={"q": "тест"},
            response_schema={"data": list}),

        # ── Registry: Stats / Enums ──
        EndpointDef("GET", f"{API_PREFIX}/registry/stats", "common",
            "Статистика",
            response_schema={"data": dict}),
        EndpointDef("GET", f"{API_PREFIX}/registry/enums", "common",
            "Допустимые значения",
            response_schema={"data": dict}),

        # ── Orchestrator: Drafts ──
        EndpointDef("POST", f"{API_PREFIX}/drafts/", "drafts",
            "Создать черновик",
            body={"document_key": "test-key", "title": "Тестовый черновик"},
            extract_keys=["draft_id", "task_id"],
            expected_status=202),
        EndpointDef("GET", f"{API_PREFIX}/drafts/", "drafts",
            "Список черновиков"),
        EndpointDef("GET", f"{API_PREFIX}/drafts/{{draft_id}}", "drafts",
            "Детали черновика",
            response_schema={"draft_id": int}),
        EndpointDef("DELETE", f"{API_PREFIX}/drafts/{{draft_id}}", "drafts",
            "Удалить черновик"),
        EndpointDef("PATCH", f"{API_PREFIX}/drafts/{{draft_id}}/decide", "drafts",
            "Решение по черновику",
            body={"action": "approve", "comment": "OK"},
            expected_status={200, 409}),
        EndpointDef("POST", f"{API_PREFIX}/drafts/{{draft_id}}/preview", "drafts",
            "Запустить превью",
            body={},
            expected_status={200, 202, 404, 409}),
        EndpointDef("GET", f"{API_PREFIX}/drafts/{{draft_id}}/preview", "drafts",
            "Превью черновика"),

        # ── Orchestrator: Documents ──
        EndpointDef("GET", f"{API_PREFIX}/documents/", "documents",
            "Список документов",
            response_schema={"items": list}),

        # ── Analyse (GW-12: добавлено) ──
        EndpointDef("POST", f"{API_PREFIX}/analyse/start", "analyse",
            "Запуск анализа",
            body={"document_id": 1},
            expected_status={200, 202}),
        EndpointDef("GET", f"{API_PREFIX}/analyse/{{task_id}}/status", "analyse",
            "Статус анализа"),

        # ── Meridian (GW-12: добавлено) ──
        EndpointDef("GET", f"{API_PREFIX}/meridian/status", "meridian",
            "Статус Meridian",
            response_schema={"status": str}),

        # ── Files (GW-12: добавлено) ──
        EndpointDef("GET", f"{API_PREFIX}/files/{{file_id}}", "files",
            "Получить файл"),

        # ── External (GW-12: добавлено) ──
        EndpointDef("GET", f"{API_PREFIX}/external/integrations", "external",
            "Список интеграций"),

        # ── Gateway собственный health ──
        EndpointDef("GET", f"{API_PREFIX}/gateway/health", "health",
            "Health check Gateway (собственный)",
            response_schema={"status": str}),

        # ── Query: Chat ──
        EndpointDef("POST", f"{API_PREFIX}/chat/sessions", "chat",
            "Создать сессию",
            body={"title": "Тест", "document_ids": [], "project_id": "{project_id}"},
            extract_keys=["session_id"],
            expected_status=201),
        EndpointDef("GET", f"{API_PREFIX}/chat/sessions", "chat",
            "Список сессий"),
        EndpointDef("GET", f"{API_PREFIX}/chat/sessions/{{session_id}}", "chat",
            "Детали сессии"),
        EndpointDef("POST", f"{API_PREFIX}/chat/sessions/{{session_id}}/messages", "chat",
            "Отправить сообщение",
            body={"text": "Тестовое сообщение", "content": "Тестовое сообщение"},
            extract_keys=["message_id"],
            expected_status={200, 202}),
        EndpointDef("GET", f"{API_PREFIX}/chat/sessions/{{session_id}}/messages", "chat",
            "История сообщений"),
        EndpointDef("POST", f"{API_PREFIX}/chat/sessions/{{session_id}}/messages/search", "chat",
            "Поиск по сессии",
            body={"query": "тест"},
            response_schema={"results": list}),
        EndpointDef("GET", f"{API_PREFIX}/chat/history", "chat",
            "История чатов"),
        EndpointDef("GET", f"{API_PREFIX}/chat/history/export", "chat",
            "Экспорт истории"),

        # ── Query: Text Search ──
        EndpointDef("POST", f"{API_PREFIX}/text/search", "text",
            "Поиск по тексту",
            body={"text": "тест", "valid_at": "2026-06-19", "top_k": 5,
                  "filters": {"category_ids": []}},
            response_schema={"results": list}),

        # ── RAG Search ──
        EndpointDef("POST", f"{API_PREFIX}/rag/search", "rag",
            "Поиск по RAG",
            body={"query": "тест", "valid_at": "2026-06-19",
                  "filters": {"document_type": [], "category_ids": [], "document_ids": []}},
            response_schema={"results": list}),
    ]

    return ServiceDef(
        service_key=SERVICE_KEY,
        display_name=DISPLAY_NAME,
        port=PORT,
        needs_auth=True,
        endpoints=endpoints,
        prepare_endpoints=prepare_endpoints,
        depends_on=["auth", "orchestrator", "query", "registry"],
        base_data={"doc_id": 1, "user_id": "1", "page_num": 1, "category_id": 1, "file_id": 1, "project_id": 1},
    )
