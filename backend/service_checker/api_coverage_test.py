#!/usr/bin/env python3
"""
PKB Neuroassistant — API Coverage Test (based on docs/api/*.md)

Скрипт проверяет вызов каждого эндпоинта из документации API.
Для каждого сервиса определяется полный список эндпоинтов (метод + путь + тело запроса),
после чего выполняется HTTP-вызов, и результат записывается в отчёт.

Запуск:
  # Все сервисы (моки должны быть запущены)
  python backend/service_checker/api_coverage_test.py

  # Только конкретные сервисы
  python backend/service_checker/api_coverage_test.py --services auth,registry

  # С сохранением отчёта
  python backend/service_checker/api_coverage_test.py -o coverage_report.md

  # Только здоровье — проверить какие сервисы отвечают
  python backend/service_checker/api_coverage_test.py --ping-only
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import httpx

# ──────────────────────────────────────────────────────────────────────
#  Data Classes
# ──────────────────────────────────────────────────────────────────────


@dataclass
class EndpointDef:
    """Определение эндпоинта из документации."""

    method: str  # GET, POST, PUT, PATCH, DELETE
    path: str  # /api/v1/...
    group: str  # группа эндпоинтов (classifiers, documents, ...)
    description: str  # краткое описание
    body: Optional[Dict[str, Any]] = None  # тело запроса (для POST/PUT/PATCH)
    params: Optional[Dict[str, Any]] = None  # query-параметры
    # Если эндпоинт требует ID из предыдущего ответа — шаблон подстановки
    # {doc_id}, {session_id}, {user_id}, {version_id}, {task_id},
    # {term_id}, {classifier_code}, {comparison_id} и т.д.
    # После успешного вызова скрипт ищет эти ID в ответе и сохраняет в контекст.
    extract_keys: Optional[List[str]] = None  # какие ключи из ответа сохранять в контекст
    # Схема ответа для валидации: {поле: тип}. Проверяется при HTTP < 500
    # Вложенные поля через точку: "data.id" → str проверяет response["data"]["id"]
    response_schema: Optional[Dict[str, type]] = None


@dataclass
class EndpointResult:
    """Результат вызова одного эндпоинта."""

    endpoint: EndpointDef
    status_code: int
    success: bool
    elapsed_ms: int = 0
    response_body: Optional[str] = None
    error: Optional[str] = None
    skipped: bool = False
    skip_reason: Optional[str] = None


@dataclass
class ServiceResult:
    """Результаты тестирования одного сервиса."""

    name: str
    port: int
    endpoints_total: int = 0
    endpoints_passed: int = 0
    endpoints_failed: int = 0
    endpoints_skipped: int = 0
    results: List[EndpointResult] = field(default_factory=list)
    ping_ok: bool = False


# ──────────────────────────────────────────────────────────────────────
#  API Specification from docs/api/*.md
# ──────────────────────────────────────────────────────────────────────

# Порты для каждого режима
MODE_PORTS = {
    "mock": {
        "orchestrator": 8081,
        "auth": 8082,
        "query": 8083,
        "registry": 8084,
    },
    "real": {
        "orchestrator": 8000,  # реальный orchestrator на порту 8000
        "auth": 8082,          # нет реальной реализации (будет пропущен)
        "query": 8083,         # нет реальной реализации (будет пропущен)
        "registry": 8084,
        "integration": 8085,
        "converter_validator": 8086,  # нет реализации (будет пропущен)
        "parser": 8087,
        "ocr": 8088,                  # нет реализации (будет пропущен)
        "analyse": 8089,               # нет реализации (будет пропущен)
        "rag_builder": 8090,
        "rag_search": 8091,
    },
}

# Какие сервисы имеют реальную реализацию (для real-режима)
SERVICES_WITH_REAL = {
    "orchestrator", "registry", "integration", "parser", "rag_builder", "rag_search",
}

# Какие сервисы имеют мок-реализацию (для mock-режима)
SERVICES_WITH_MOCK = {
    "orchestrator", "auth", "query", "registry",
}

API_PREFIX = "/api/v1"

# Тестовые данные
TEST_CREDENTIALS = {
    "username": "petrova@example.com",
    "password": "secret456",
}

TEST_ADMIN_CREDENTIALS = {
    "username": "admin@example.com",
    "password": "admin123",
}

# ──────────────────────────────────────────────────────────────────────
#  Endpoint definitions — based strictly on docs/api/*.md
# ──────────────────────────────────────────────────────────────────────


def build_endpoints() -> Dict[str, List[EndpointDef]]:
    """Построить полный список эндпоинтов из документации по каждому сервису.

    Порядок внутри цепочек: CREATE → GET → PUT → PATCH → DELETE
    чтобы эндпоинты, зависящие от ID из контекста, выполнялись после создания.
    """

    endpoints: Dict[str, List[EndpointDef]] = {}

    # ── Auth Service (auth-service:8082) ──────────────────────────────
    endpoints["auth"] = [
        # Health
        EndpointDef("GET", f"{API_PREFIX}/health", "health", "Health check сервиса",
            response_schema={"status": str, "service": str}),
        EndpointDef("GET", f"{API_PREFIX}/system/health", "health", "System health",
            response_schema={"status": str}),
        # Auth group (цепочка: token → refresh → revoke → me)
        EndpointDef("POST", f"{API_PREFIX}/auth/token", "auth", "Получение JWT токена",
            body=TEST_CREDENTIALS,
            extract_keys=["access_token", "refresh_token"],
            response_schema={"access_token": str, "refresh_token": str, "token_type": str, "expires_in": int}),
        EndpointDef("GET", f"{API_PREFIX}/auth/me", "auth", "Профиль пользователя",
            response_schema={"email": str, "role": str, "permissions": dict}),
        EndpointDef("POST", f"{API_PREFIX}/auth/refresh", "auth", "Обновление токена",
            body={"refresh_token": "{refresh_token}"},
            response_schema={"access_token": str, "refresh_token": str}),
        EndpointDef("POST", f"{API_PREFIX}/auth/revoke", "auth", "Отзыв токена",
            body={"refresh_token": "{refresh_token}"},
            response_schema={"message": str}),
        # Admin group (под admin правами — будет 403 для petrova)
        EndpointDef("GET", f"{API_PREFIX}/admin/users", "admin", "Список пользователей",
            params={"page": 1, "page_size": 10}),
        EndpointDef("POST", f"{API_PREFIX}/admin/users", "admin", "Создать пользователя",
            body={"email": "test@test.com", "full_name": "Test User", "password": "test123", "roles": ["engineer"]},
            extract_keys=["user_id"]),
        EndpointDef("GET", f"{API_PREFIX}/admin/users/{{user_id}}", "admin", "Получить пользователя"),
        EndpointDef("PUT", f"{API_PREFIX}/admin/users/{{user_id}}", "admin", "Обновить пользователя",
            body={"email": "updated@test.com", "full_name": "Updated User", "position": "Engineer", "roles": ["engineer"], "is_active": True}),
        EndpointDef("PATCH", f"{API_PREFIX}/admin/users/{{user_id}}", "admin", "Изменить роль",
            body={"role": "admin"}),
        EndpointDef("DELETE", f"{API_PREFIX}/admin/users/{{user_id}}", "admin", "Деактивировать пользователя"),
        EndpointDef("GET", f"{API_PREFIX}/admin/roles", "admin", "Список ролей"),
        EndpointDef("POST", f"{API_PREFIX}/admin/roles", "admin", "Создать роль",
            body={"name": "viewer", "permissions": {"can_view_documents": True}}),
        EndpointDef("GET", f"{API_PREFIX}/admin/audit", "admin", "Журнал аудита",
            params={"page": 1, "page_size": 10}),
        # Internal
        EndpointDef("POST", f"{API_PREFIX}/internal/auth/validate", "internal", "Валидация токена",
            body={"access_token": "{access_token}"},
            response_schema={"valid": bool}),
    ]

    # ── Registry Service (registry-service:8084) ─────────────────────
    # Цепочка 1: classifiers CRUD
    # Цепочка 2: terminology CRUD
    # Цепочка 3: documents CRUD
    endpoints["registry"] = [
        # Health
        EndpointDef("GET", f"{API_PREFIX}/health", "health", "Health check",
            response_schema={"status": str}),
        # ── Classifiers (create → get tree → get one → update → patch → delete) ──
        EndpointDef("POST", f"{API_PREFIX}/classifiers", "classifiers", "Создать классификатор",
            body={"classifier_system": "MKS", "code": "99.999", "full_name": "Тестовый классификатор", "status": "active"},
            extract_keys=["classifier_code"],
            response_schema={"data": dict}),
        EndpointDef("GET", f"{API_PREFIX}/classifiers", "classifiers", "Список классификаторов",
            params={"page": 1, "page_size": 10},
            response_schema={"data": list, "meta": dict}),
        EndpointDef("GET", f"{API_PREFIX}/classifiers/tree", "classifiers", "Дерево классификаторов",
            response_schema={"data": list}),
        EndpointDef("GET", f"{API_PREFIX}/classifiers/{{classifier_code}}", "classifiers", "Получить классификатор",
            response_schema={"data": dict}),
        EndpointDef("PUT", f"{API_PREFIX}/classifiers/{{classifier_code}}", "classifiers", "Обновить классификатор",
            body={"full_name": "Обновлённый тестовый классификатор"},
            response_schema={"data": dict}),
        EndpointDef("PATCH", f"{API_PREFIX}/classifiers/{{classifier_code}}", "classifiers", "Частичное обновление",
            body={"status": "inactive"},
            response_schema={"data": dict}),
        EndpointDef("DELETE", f"{API_PREFIX}/classifiers/{{classifier_code}}", "classifiers", "Удалить классификатор"),
        EndpointDef("POST", f"{API_PREFIX}/classifiers/import", "classifiers", "Импорт классификаторов",
            body={"classifiers": [{"classifier_system": "MKS", "code": "99.998", "full_name": "Импортированный"}]}),
        EndpointDef("GET", f"{API_PREFIX}/classifiers/quarantine", "classifiers", "Карантин",
            response_schema={"data": list}),
        EndpointDef("POST", f"{API_PREFIX}/classifiers/quarantine/{{pending_id}}/accept", "classifiers", "Принять из карантина",
            body={"parent_code": "01.040", "full_name": "Принятый термин"}),
        EndpointDef("POST", f"{API_PREFIX}/classifiers/quarantine/{{pending_id}}/reject", "classifiers", "Отклонить из карантина",
            body={"admin_comment": "Отклонено тестом"}),
        EndpointDef("POST", f"{API_PREFIX}/classifiers/validate", "classifiers", "Валидация классификации",
            body={"classification": {"mks_oks_code": "01.040.01", "okstu_code": "1234", "udk_code": "001.4"}}),
        # ── Terminology (create → list → get → normalize → update → delete) ──
        EndpointDef("POST", f"{API_PREFIX}/terminology", "terminology", "Создать термин",
            body={"raw_term": "Тест", "standard_term": "Тест", "normalized_value": "тест", "term_type": "abbreviation", "definition": "Тестовый термин"},
            extract_keys=["term_id"],
            response_schema={"data": dict}),
        EndpointDef("GET", f"{API_PREFIX}/terminology", "terminology", "Список терминов",
            params={"page": 1, "page_size": 10},
            response_schema={"data": list, "meta": dict}),
        EndpointDef("GET", f"{API_PREFIX}/terminology/{{term_id}}", "terminology", "Получить термин",
            response_schema={"data": dict}),
        EndpointDef("GET", f"{API_PREFIX}/terminology/normalize", "terminology", "Нормализовать термин",
            params={"term": "Тест"}),
        EndpointDef("PUT", f"{API_PREFIX}/terminology/{{term_id}}", "terminology", "Обновить термин",
            body={"definition": "Обновлённое определение"},
            response_schema={"data": dict}),
        EndpointDef("DELETE", f"{API_PREFIX}/terminology/{{term_id}}", "terminology", "Удалить термин"),
        EndpointDef("POST", f"{API_PREFIX}/terminology/import", "terminology", "Импорт терминов",
            body={"terms": [{"raw_term": "Импорт", "standard_term": "Импорт", "normalized_value": "импорт", "term_type": "abbreviation"}]}),
        # ── Documents (create → list → get → update → patch → history → succession → delete) ──
        EndpointDef("POST", f"{API_PREFIX}/documents", "documents", "Создать документ",
            body={"title": "Тестовый документ", "doc_code": "ТЕСТ-001", "source_type": "GOST", "era": "RF", "validity_status": "active"},
            extract_keys=["doc_id"],
            response_schema={"data": dict}),
        EndpointDef("GET", f"{API_PREFIX}/documents", "documents", "Список документов",
            params={"page": 1, "page_size": 10},
            response_schema={"data": list, "meta": dict}),
        EndpointDef("GET", f"{API_PREFIX}/documents/{{doc_id}}", "documents", "Получить документ",
            response_schema={"data": dict}),
        EndpointDef("PUT", f"{API_PREFIX}/documents/{{doc_id}}", "documents", "Обновить документ",
            body={"title": "Обновлённый документ"},
            response_schema={"data": dict}),
        EndpointDef("PATCH", f"{API_PREFIX}/documents/{{doc_id}}/status", "documents", "Обновить статус",
            body={"status": "uploaded"},
            response_schema={"data": dict}),
        EndpointDef("GET", f"{API_PREFIX}/documents/{{doc_id}}/history", "documents", "История статусов",
            response_schema={"data": list, "meta": dict}),
        EndpointDef("GET", f"{API_PREFIX}/documents/{{doc_id}}/succession", "documents", "Цепочка преемственности",
            response_schema={"data": dict}),
        EndpointDef("DELETE", f"{API_PREFIX}/documents/{{doc_id}}", "documents", "Удалить документ"),
        EndpointDef("GET", f"{API_PREFIX}/documents/export", "documents", "Экспорт документов"),
        EndpointDef("POST", f"{API_PREFIX}/documents/import", "documents", "Массовый импорт",
            body={"documents": [{"title": "Импорт тест", "doc_code": "ИМП-001", "source_type": "GOST", "era": "RF"}]}),
        # Common
        EndpointDef("GET", f"{API_PREFIX}/stats", "common", "Статистика",
            response_schema={"data": dict}),
        EndpointDef("GET", f"{API_PREFIX}/enums", "common", "Допустимые значения",
            response_schema={"data": dict}),
    ]

    # ── Orchestrator Service (orchestrator-service:8081) ────────────
    endpoints["orchestrator"] = [
        # Health / Monitor
        EndpointDef("GET", f"{API_PREFIX}/monitor/health", "monitor", "Health Orchestrator",
            response_schema={"status": str}),
        EndpointDef("GET", f"{API_PREFIX}/monitor/metrics", "monitor", "Метрики",
            response_schema={"control_metrics": dict}),
        # Documents (create → list → get → status → file → history → errors → versions → approve → delete → queue → pages → search)
        EndpointDef("POST", f"{API_PREFIX}/documents", "documents", "Загрузить документ",
            body={"title": "Тестовый документ", "source_type": "OTHER", "content_hash": "abc123"},
            extract_keys=["task_id"],
            response_schema={"task_id": str, "status": str}),
        EndpointDef("GET", f"{API_PREFIX}/documents", "documents", "Список документов",
            response_schema={"summary": dict, "items": list}),
        EndpointDef("GET", f"{API_PREFIX}/documents/{{doc_id}}", "documents", "Детали документа",
            response_schema={"document_id": str}),
        EndpointDef("GET", f"{API_PREFIX}/documents/{{doc_id}}/status", "documents", "Статус документа"),
        EndpointDef("GET", f"{API_PREFIX}/documents/{{doc_id}}/file", "documents", "Файл документа"),
        EndpointDef("GET", f"{API_PREFIX}/documents/{{doc_id}}/history", "documents", "История изменений"),
        EndpointDef("GET", f"{API_PREFIX}/documents/{{doc_id}}/errors", "documents", "Ошибки документа",
            response_schema={"errors": list}),
        EndpointDef("GET", f"{API_PREFIX}/documents/{{doc_id}}/versions", "documents", "Список версий",
            response_schema={"versions": list}),
        EndpointDef("POST", f"{API_PREFIX}/documents/{{doc_id}}/versions", "documents", "Добавить версию",
            body={}),
        EndpointDef("POST", f"{API_PREFIX}/documents/{{doc_id}}/approve", "documents", "Аппрув документа",
            body={"comment": "Утверждено тестом"},
            response_schema={"status": str}),
        EndpointDef("POST", f"{API_PREFIX}/documents/{{doc_id}}/reprocess", "documents", "Переобработка",
            body={"mode": "full"}),
        EndpointDef("DELETE", f"{API_PREFIX}/documents/{{doc_id}}", "documents", "Удалить документ",
            response_schema={"document_id": str}),
        EndpointDef("GET", f"{API_PREFIX}/documents/queue", "documents", "Очередь документов",
            response_schema={"queue": list, "meta": dict}),
        EndpointDef("GET", f"{API_PREFIX}/documents/{{doc_id}}/pages", "documents", "Список страниц",
            response_schema={"pages": list}),
        EndpointDef("GET", f"{API_PREFIX}/documents/{{doc_id}}/pages/{{page_num}}", "documents", "Получить страницу"),
        EndpointDef("GET", f"{API_PREFIX}/documents/{{doc_id}}/pages/{{page_num}}/text", "documents", "Текст страницы",
            response_schema={"blocks": list}),
        EndpointDef("GET", f"{API_PREFIX}/documents/{{doc_id}}/pages/{{page_num}}/preview", "documents", "Превью страницы"),
        EndpointDef("GET", f"{API_PREFIX}/documents/{{doc_id}}/parameters", "documents", "Параметры документа",
            response_schema={"parameters": list}),
        # Search
        EndpointDef("POST", f"{API_PREFIX}/documents/search", "search", "Поиск документов",
            body={"query": "тест"}),
        EndpointDef("GET", f"{API_PREFIX}/documents/search", "search", "Поиск (GET)",
            params={"query": "тест"}),
        # System health
        EndpointDef("GET", f"{API_PREFIX}/system/health", "health", "System health",
            response_schema={"status": str}),
    ]

    # ── Query Service (query-service:8083) ──────────────────────────
    # Цепочка: create session → list → get → update → messages → context → export → feedback → delete
    endpoints["query"] = [
        # Health
        EndpointDef("GET", f"{API_PREFIX}/health", "health", "Health check",
            response_schema={"status": str}),
        EndpointDef("GET", f"{API_PREFIX}/system/health", "health", "System health",
            response_schema={"status": str}),
        # Chat sessions (create → list → get → update → messages → delete)
        EndpointDef("POST", f"{API_PREFIX}/chat/sessions", "chat", "Создать сессию",
            body={"title": "Тестовая сессия API"},
            extract_keys=["session_id"],
            response_schema={"session_id": str, "title": str}),
        EndpointDef("GET", f"{API_PREFIX}/chat/sessions", "chat", "Список сессий",
            response_schema={"sessions": list}),
        EndpointDef("GET", f"{API_PREFIX}/chat/sessions/{{session_id}}", "chat", "Детали сессии",
            response_schema={"session_id": str, "messages": list}),
        EndpointDef("PUT", f"{API_PREFIX}/chat/sessions/{{session_id}}", "chat", "Обновить сессию",
            body={"title": "Обновлённая сессия"},
            response_schema={"session_id": str}),
        EndpointDef("POST", f"{API_PREFIX}/chat/sessions/{{session_id}}/messages", "chat", "Отправить сообщение",
            body={"text": "Тестовое сообщение", "content": "Тестовое сообщение"},
            extract_keys=["message_id"],
            response_schema={"message_id": str}),
        EndpointDef("GET", f"{API_PREFIX}/chat/sessions/{{session_id}}/messages/last", "chat", "Последние сообщения"),
        EndpointDef("GET", f"{API_PREFIX}/chat/sessions/{{session_id}}/messages", "chat", "История сообщений",
            response_schema={"messages": list}),
        EndpointDef("GET", f"{API_PREFIX}/chat/sessions/{{session_id}}/messages/{{message_id}}", "chat", "Детали сообщения",
            response_schema={"message": dict}),
        EndpointDef("POST", f"{API_PREFIX}/chat/sessions/{{session_id}}/context", "chat", "Управление контекстом",
            body={"action": "add_documents", "params": {"document_ids": []}}),
        EndpointDef("POST", f"{API_PREFIX}/chat/sessions/{{session_id}}/export", "chat", "Экспорт сессии",
            body={"format": "json"}),
        EndpointDef("POST", f"{API_PREFIX}/chat/feedback", "chat", "Отправить отзыв",
            body={"session_id": "{session_id}", "message_id": "{message_id}", "rating": 5}),
        EndpointDef("DELETE", f"{API_PREFIX}/chat/sessions/{{session_id}}", "chat", "Удалить сессию",
            response_schema={"session_id": str}),
        # History (не зависит от сессии)
        EndpointDef("GET", f"{API_PREFIX}/chat/history", "chat", "История чатов",
            response_schema={"items": list, "meta": dict}),
        EndpointDef("GET", f"{API_PREFIX}/chat/history/export", "chat", "Экспорт истории"),
        # Text search / ask (не зависит от сессии)
        EndpointDef("POST", f"{API_PREFIX}/text/search", "text", "Поиск по тексту",
            body={"text": "толщина обшивки ледового пояса", "top_k": 5},
            response_schema={"results": list}),
        EndpointDef("POST", f"{API_PREFIX}/text/ask", "text", "Задать вопрос",
            body={"text": "Какая толщина обшивки?", "document_ids": []}),
    ]

    # ── Integration Service (integration-service:8085) ──────────────
    endpoints["integration"] = [
        EndpointDef("GET", f"{API_PREFIX}/health", "health", "Health check сервиса"),
        EndpointDef("GET", f"{API_PREFIX}/external/status", "external", "Статус внешних систем"),
        # Files — multipart, сложно тестировать без реального файла, но проверим метаданные
        EndpointDef("POST", f"{API_PREFIX}/files/upload", "files", "Загрузка файла (проверка без файла — ожидается 422)"),
        EndpointDef("GET", f"{API_PREFIX}/files/{{file_key}}", "files", "Получить файл"),
        EndpointDef("GET", f"{API_PREFIX}/files/{{file_key}}/info", "files", "Метаданные файла"),
        EndpointDef("DELETE", f"{API_PREFIX}/files/{{file_key}}", "files", "Удалить файл"),
        EndpointDef("POST", f"{API_PREFIX}/meridian/export", "meridian", "Экспорт в Меридиан", body={"document_id": "test-doc-id", "data": {"designation": "ТЕСТ.001", "title": "Тестовый экспорт"}}),
    ]

    # ── Parser Service (parser-service:8087) ────────────────────────
    endpoints["parser"] = [
        EndpointDef("GET", f"{API_PREFIX}/health", "health", "Health check сервиса"),
        EndpointDef("POST", f"{API_PREFIX}/parser/process", "parser", "Запуск обработки", body={"task_id": "test-task", "version_id": "test-version", "file_key": "test-file-key"}),
        EndpointDef("POST", f"{API_PREFIX}/parser/preview", "parser", "Быстрый предпросмотр", body={"task_id": "test-task", "version_id": "test-version", "file_key": "test-file-key", "max_pages": 1}),
        EndpointDef("GET", f"{API_PREFIX}/parser/process/{{task_id}}/status", "parser", "Статус обработки (longpoll)"),
        EndpointDef("GET", f"{API_PREFIX}/parser/process/{{task_id}}/result", "parser", "Итоговый JSON обработки"),
    ]

    # ── OCR Service (ocr-service:8088) ────────────────────────────
    endpoints["ocr"] = [
        EndpointDef("GET", f"{API_PREFIX}/health", "health", "Health check сервиса"),
        EndpointDef("POST", f"{API_PREFIX}/ocr/process", "ocr", "Запуск OCR обработки", body={"task_id": "test-task", "version_id": "test-version", "file_key": "test-file-key"}),
        EndpointDef("POST", f"{API_PREFIX}/ocr/preview", "ocr", "Быстрый OCR предпросмотр", body={"task_id": "test-task", "version_id": "test-version", "file_key": "test-file-key", "max_pages": 1}),
        EndpointDef("GET", f"{API_PREFIX}/ocr/process/{{task_id}}/status", "ocr", "Статус OCR обработки"),
        EndpointDef("GET", f"{API_PREFIX}/ocr/process/{{task_id}}/result", "ocr", "Итоговый JSON OCR"),
    ]

    # ── Analyse Service (analyse-service:8089) ──────────────────────
    endpoints["analyse"] = [
        EndpointDef("GET", f"{API_PREFIX}/health", "health", "Health check сервиса"),
        EndpointDef("POST", f"{API_PREFIX}/analyse/compare", "analyse", "Сопоставление норм и проектов", body={"comparison_id": "cmp-test-001", "normative_query": "Толщина обшивки ≥ 12 мм", "project_document_id": "doc-proj-001"}),
        EndpointDef("GET", f"{API_PREFIX}/analyse/compare/{{comparison_id}}", "analyse", "Результат сопоставления"),
        EndpointDef("POST", f"{API_PREFIX}/analyse/compare/batch", "analyse", "Массовое сопоставление", body={"pairs": [{"normative_chunk_id": 1, "project_chunk_id": 2}]}),
        EndpointDef("POST", f"{API_PREFIX}/analyse/calculate", "analyse", "Вычисления", body={"expression": "(1200 + 2*10) / 2"}),
        EndpointDef("POST", f"{API_PREFIX}/analyse/recommend", "analyse", "Рекомендации", body={"failures": [{"rule": "min_thickness_12mm", "status": "fail"}], "document_type": "drawing"}),
    ]

    # ── Converter-Validator Service (converter-validator:8086) ──────
    endpoints["converter_validator"] = [
        EndpointDef("GET", f"{API_PREFIX}/health", "health", "Health check сервиса"),
        EndpointDef("POST", f"{API_PREFIX}/converter/preview/metadata", "converter", "Предпросмотр метаданных", body={"task_id": "test-task", "version_id": "test-version", "raw_json": {"test": True}}),
        EndpointDef("POST", f"{API_PREFIX}/converter/convert", "converter", "Конвертация документа", body={"task_id": "test-task", "version_id": "test-version", "raw_json": {"test": True}}),
        EndpointDef("POST", f"{API_PREFIX}/validate/document", "validate", "Валидация документа", body={"task_id": "test-task", "version_id": "test-version", "raw_json": {"test": True}}),
    ]

    # ── RAG Builder Service (rag-builder:8090) ─────────────────────
    endpoints["rag_builder"] = [
        EndpointDef("GET", f"{API_PREFIX}/health", "health", "Health check сервиса"),
        EndpointDef("POST", f"{API_PREFIX}/rag/build", "rag", "Построение чанков и индексация", body={"document_id": "test-doc-001", "sections": [{"section_id": 1, "document_id": "test-doc-001", "clause": "1", "level": 1, "path": "1", "page": 1, "type": "text", "content": {"text": "Тестовое содержимое"}}]}),
        EndpointDef("DELETE", f"{API_PREFIX}/rag/build/{{doc_id}}", "rag", "Удаление чанков из индекса"),
        EndpointDef("GET", f"{API_PREFIX}/rag/build/{{doc_id}}/status", "rag", "Статус индексации (longpoll)"),
    ]

    # ── RAG Search Service (rag-search:8091) ────────────────────────
    endpoints["rag_search"] = [
        EndpointDef("GET", f"{API_PREFIX}/health", "health", "Health check сервиса"),
        EndpointDef("POST", f"{API_PREFIX}/rag/search", "rag", "Гибридный поиск чанков", body={"query": "ледовый класс Arc4", "top_k": 5}),
    ]

    return endpoints


# ──────────────────────────────────────────────────────────────────────
#  Тестовый движок
# ──────────────────────────────────────────────────────────────────────

HEADERS_JSON = {"Content-Type": "application/json", "Accept": "application/json"}


class ApiCoverageTester:
    """
    Тестер покрытия API.
    Для каждого сервиса вызывает все эндпоинты из документации,
    собирает результаты и формирует отчёт.

    Режимы:
      - mock: только мок-сервисы (auth, registry mock, orchestrator mock, query mock)
      - real: только реальные сервисы с БД (registry, integration, rag_builder, ...)
    """

    def __init__(
        self,
        mode: str = "mock",
        services: Optional[List[str]] = None,
        base_host: str = "127.0.0.1",
    ):
        self.mode = mode
        self.base_host = base_host
        self.endpoints = build_endpoints()

        # Определяем какие сервисы доступны в этом режиме
        available_ports = MODE_PORTS.get(mode, MODE_PORTS["mock"])
        available_services = set(available_ports.keys())

        if mode == "mock":
            self.services_with_impl = SERVICES_WITH_MOCK
        else:
            self.services_with_impl = SERVICES_WITH_REAL

        if services:
            self.services_to_test = [s for s in services if s in available_services]
        else:
            self.services_to_test = sorted(available_services)

        self.context: Dict[str, Any] = {}  # shared context между вызовами
        self.results: Dict[str, ServiceResult] = {}
        self.client = httpx.AsyncClient(timeout=15)

    async def close(self) -> None:
        await self.client.aclose()

    async def ping_service(self, port: int, fast: bool = False) -> bool:
        """Проверить, отвечает ли сервис.

        Если fast=True — пробуем только первый health-эндпоинт с таймаутом 1.5с.
        """
        health_paths = [
            f"{API_PREFIX}/health",
            f"{API_PREFIX}/system/health",
            f"{API_PREFIX}/monitor/health",
        ]
        if fast:
            health_paths = health_paths[:1]
        timeout = 1.5 if fast else 2
        for path in health_paths:
            try:
                resp = await self.client.get(
                    f"http://{self.base_host}:{port}{path}",
                    timeout=timeout,
                )
                if resp.status_code < 500:
                    return True
            except Exception:
                continue
        return False

    def _resolve_path(self, path: str) -> str:
        """Подставить контекстные переменные в путь."""
        resolved = path
        for key, value in self.context.items():
            placeholder = "{{" + key + "}}"
            resolved = resolved.replace(placeholder, str(value))
        return resolved

    def _resolve_body(self, body: Optional[Dict]) -> Optional[Dict]:
        """Подставить контекстные переменные в тело."""
        if body is None:
            return None
        resolved = json.dumps(body)
        for key, value in self.context.items():
            placeholder = "{" + key + "}"
            resolved = resolved.replace(placeholder, str(value))
        return json.loads(resolved)

    def _validate_response(
        self,
        response_body: Optional[str],
        schema: Dict[str, type],
    ) -> Tuple[bool, List[str]]:
        """
        Проверить что ответ содержит все ожидаемые поля с правильными типами.

        schema = {
            "status": str,              # проверяет response["status"] — str
            "data": dict,               # response["data"] — dict
            "data.items": list,         # response["data"]["items"] — list (точечная нотация)
        }

        Возвращает (ok, список_ошибок).
        """
        if not response_body:
            return False, ["Пустой ответ"]

        try:
            data = json.loads(response_body)
        except json.JSONDecodeError as e:
            return False, [f"Невалидный JSON: {e}"]

        errors = []

        for path, expected_type in schema.items():
            # Идём по точечному пути
            parts = path.split(".")
            current = data
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    errors.append(
                        f"Поле '{path}' обязательно, но не найдено в ответе"
                    )
                    break
            else:
                # Проверяем тип
                if not isinstance(current, expected_type):
                    actual = type(current).__name__
                    expected = expected_type.__name__
                    errors.append(
                        f"Поле '{path}' ожидалось {expected}, получен {actual} = {str(current)[:80]}"
                    )

        return len(errors) == 0, errors

    def _extract_context(self, response_body: Optional[str], extract_keys: Optional[List[str]]) -> None:
        """Извлечь ID из ответа и сохранить в контекст.

        Поддержка обёрток: если ответ = {"data": {"id": "xxx"}},
        а ключ "id" — сначала ищем "data.id", потом рекурсивно "id".
        """
        if not response_body or not extract_keys:
            return
        try:
            raw = json.loads(response_body)
        except json.JSONDecodeError:
            return

        def _get_by_path(obj: Any, path: str) -> Optional[Any]:
            """Достать значение по точечному пути ("data.id")."""
            parts = path.split(".")
            current = obj
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return None
            return current

        def _search(obj: Any, key: str) -> Optional[Any]:
            """Рекурсивный поиск ключа в любом месте объекта."""
            if isinstance(obj, dict):
                if key in obj:
                    return obj[key]
                for v in obj.values():
                    result = _search(v, key)
                    if result is not None:
                        return result
                # Альтернативные имена
                alt_map = {
                    "session_id": ["id", "sessionId", "session_id"],
                    "doc_id": ["id", "document_id", "docId"],
                    "user_id": ["id", "userId", "user_id"],
                    "classifier_code": ["code", "classifier_code"],
                    "term_id": ["id", "term_id", "termId"],
                    "message_id": ["id", "messageId", "message_id"],
                    "task_id": ["task_id", "taskId"],
                }
                for alt in alt_map.get(key, []):
                    if alt in obj:
                        return obj[alt]
            elif isinstance(obj, list):
                for item in obj:
                    result = _search(item, key)
                    if result is not None:
                        return result
            return None

        for key in extract_keys:
            if key not in self.context:
                # Сначала ищем как data.key (для обёрнутых ответов)
                value = _get_by_path(raw, f"data.{key}")
                # Потом рекурсивно
                if value is None:
                    value = _search(raw, key)
                if value is not None:
                    self.context[key] = value

    async def test_service(self, service_key: str) -> ServiceResult:
        """Протестировать все эндпоинты сервиса."""
        svc_endpoints = self.endpoints.get(service_key, [])
        ports = MODE_PORTS.get(self.mode, MODE_PORTS["mock"])
        port = ports.get(service_key, 0)

        # Определяем имя сервиса
        svc_name = {
            "auth": "Auth Service",
            "registry": "Registry Service",
            "orchestrator": "Orchestrator Service",
            "query": "Query Service",
            "integration": "Integration Service",
            "parser": "Parser Service",
            "ocr": "OCR Service",
            "analyse": "Analyse Service",
            "converter_validator": "Converter-Validator Service",
            "rag_builder": "RAG Builder Service",
            "rag_search": "RAG Search Service",
        }.get(service_key, service_key)

        result = ServiceResult(name=svc_name, port=port)
        result.endpoints_total = len(svc_endpoints)

        if port == 0:
            result.ping_ok = False
            for ep in svc_endpoints:
                result.results.append(
                    EndpointResult(endpoint=ep, status_code=0, success=False, skipped=True, skip_reason="Неизвестный порт")
                )
            result.endpoints_skipped = len(svc_endpoints)
            return result

        # Проверяем жив ли сервис
        alive = await self.ping_service(port, fast=True)
        result.ping_ok = alive

        # Определяем нужен ли токен для этого сервиса
        needs_auth = service_key in ("auth", "registry", "orchestrator", "query")

        for ep in svc_endpoints:
            # Если сервис не отвечает — пропускаем все эндпоинты
            if not alive:
                result.results.append(
                    EndpointResult(endpoint=ep, status_code=0, success=False, skipped=True, skip_reason="Сервис не отвечает")
                )
                result.endpoints_skipped += 1
                continue

            # Для эндпоинтов, требующих ID из контекста, проверяем наличие
            path_placeholders = [p.strip("{}") for p in ep.path.split("/") if "{" in p and "}" in p]
            missing_vars = [v for v in path_placeholders if v not in self.context]
            if missing_vars and "{{" in ep.path:
                result.results.append(
                    EndpointResult(
                        endpoint=ep, status_code=0, success=False, skipped=True,
                        skip_reason=f"Нет в контексте: {', '.join(missing_vars)}. "
                                    f"Требуется предварительный вызов создающего эндпоинта."
                    )
                )
                result.endpoints_skipped += 1
                continue

            # Если тело содержит неподставленные переменные — пропускаем
            body = self._resolve_body(ep.body)
            if body and isinstance(body, str):
                # Если после подстановки остались плейсхолдеры
                if "{" in body and "}" in body:
                    result.results.append(
                        EndpointResult(endpoint=ep, status_code=0, success=False, skipped=True, skip_reason="Не все переменные контекста доступны для тела запроса")
                    )
                    result.endpoints_skipped += 1
                    continue

            # Формируем URL
            resolved_path = self._resolve_path(ep.path)
            url = f"http://{self.base_host}:{port}{resolved_path}"

            # Формируем заголовки
            headers = {**HEADERS_JSON}
            if needs_auth and "access_token" in self.context:
                headers["Authorization"] = f"Bearer {self.context['access_token']}"

            # Выполняем запрос
            start = time.time()
            try:
                kwargs: Dict[str, Any] = {"headers": headers}
                if body is not None:
                    kwargs["json"] = body
                if ep.params:
                    kwargs["params"] = ep.params

                resp = await getattr(self.client, ep.method.lower())(url, **kwargs)
                elapsed = int((time.time() - start) * 1000)

                resp_body = resp.text if resp.content else None
                success = resp.status_code < 500  # 5xx считаем ошибкой сервиса

                # Извлекаем контекст из ответа
                if success and ep.extract_keys:
                    self._extract_context(resp_body, ep.extract_keys)

                # Валидация схемы ответа (только для 2xx)
                schema_valid = True
                schema_errors = []
                if resp.status_code < 300 and ep.response_schema:
                    schema_valid, schema_errors = self._validate_response(
                        resp_body, ep.response_schema
                    )
                    if not schema_valid:
                        success = False  # помечаем как failed если схема не совпала

                ep_result = EndpointResult(
                    endpoint=ep,
                    status_code=resp.status_code,
                    success=success,
                    elapsed_ms=elapsed,
                    response_body=resp_body[:500] if resp_body else None,
                    error="; ".join(schema_errors) if schema_errors else None,
                )

                if success:
                    result.endpoints_passed += 1
                else:
                    result.endpoints_failed += 1

            except httpx.ConnectError as e:
                elapsed = int((time.time() - start) * 1000)
                ep_result = EndpointResult(
                    endpoint=ep, status_code=0, success=False, elapsed_ms=elapsed,
                    error=f"ConnectError: {e}", skipped=True, skip_reason="Сервис не отвечает"
                )
                result.endpoints_skipped += 1
            except httpx.TimeoutException as e:
                elapsed = int((time.time() - start) * 1000)
                ep_result = EndpointResult(
                    endpoint=ep, status_code=0, success=False, elapsed_ms=elapsed,
                    error=f"Timeout: {e}", skipped=True, skip_reason="Таймаут"
                )
                result.endpoints_skipped += 1
            except Exception as e:
                elapsed = int((time.time() - start) * 1000)
                ep_result = EndpointResult(
                    endpoint=ep, status_code=0, success=False, elapsed_ms=elapsed,
                    error=str(e)
                )
                result.endpoints_failed += 1

            result.results.append(ep_result)

        return result

    async def run_all(self) -> Dict[str, ServiceResult]:
        """Запустить тестирование всех сервисов."""
        mode_label = {"mock": "🧪 Mock mode (быстрый)", "real": "🔬 Real mode (полный)"}
        print("=" * 70)
        print(f"  PKB Neuroassistant — API Coverage Test")
        print(f"  {mode_label.get(self.mode, self.mode)}")
        print(f"  Основано на docs/api/*.md")
        print("=" * 70)

        for svc_key in self.services_to_test:
            if svc_key not in self.endpoints:
                print(f"\n  ✗  Сервис '{svc_key}' не найден в спецификации. Пропускаем.")
                continue

            svc_name = svc_key.upper()
            ep_count = len(self.endpoints[svc_key])
            print(f"\n  ── [{svc_name}] ({ep_count} эндпоинтов) ──")

            result = await self.test_service(svc_key)
            self.results[svc_key] = result

            status = "✓" if result.ping_ok else "✗"
            print(f"     Ping: {status}  |  Passed: {result.endpoints_passed}/{result.endpoints_total}  "
                  f"|  Failed: {result.endpoints_failed}  |  Skipped: {result.endpoints_skipped}")

        return self.results

    def generate_report(self) -> str:
        """Сформировать markdown-отчёт."""
        lines = []
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        mode_label = {"mock": "🧪 Mock (быстрый)", "real": "🔬 Real (полный)"}
        lines.append(f"# API Coverage Report\n")
        lines.append(f"**Generated:** {now}\n")
        lines.append(f"**Mode:** {mode_label.get(self.mode, self.mode)}\n")
        lines.append(f"**Based on:** `docs/api/*.md`\n")
        lines.append("---\n")

        # Сводка
        lines.append("## 📊 Summary\n")
        lines.append("| Service | Port | Endpoints | ✅ Passed | ❌ Failed | ⏭️ Skipped | Ping |")
        lines.append("|---------|:----:|:---------:|:---------:|:---------:|:----------:|:----:|")

        total_ep = 0
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        services_alive = 0

        for svc_key, result in self.results.items():
            total_ep += result.endpoints_total
            total_passed += result.endpoints_passed
            total_failed += result.endpoints_failed
            total_skipped += result.endpoints_skipped
            if result.ping_ok:
                services_alive += 1
            ping_icon = "✅" if result.ping_ok else "❌"
            lines.append(f"| {result.name} | {result.port} | {result.endpoints_total} | "
                        f"{result.endpoints_passed} | {result.endpoints_failed} | "
                        f"{result.endpoints_skipped} | {ping_icon} |")

        lines.append(f"| **Total** | | **{total_ep}** | **{total_passed}** | "
                    f"**{total_failed}** | **{total_skipped}** | **{services_alive}/{len(self.results)}** |\n")

        # Детали по каждому сервису
        lines.append("## 🔍 Details by Service\n")

        for svc_key, result in self.results.items():
            lines.append(f"### {result.name} (port {result.port})\n")
            lines.append(f"**Ping:** {'✅ Alive' if result.ping_ok else '❌ Unreachable'}\n")
            lines.append(f"**Total:** {result.endpoints_total} | **Passed:** {result.endpoints_passed} | "
                        f"**Failed:** {result.endpoints_failed} | **Skipped:** {result.endpoints_skipped}\n")

            # Группируем по группам
            groups: Dict[str, List[EndpointResult]] = {}
            for r in result.results:
                groups.setdefault(r.endpoint.group, []).append(r)

            for group_name, group_results in groups.items():
                lines.append(f"<details>")
                lines.append(f"<summary><b>{group_name.upper()}</b> ({len(group_results)} эндпоинтов)</summary>\n")
                lines.append("| # | Method | Path | Status | Code | Time |")
                lines.append("|---|--------|------|--------|:----:|:----:|")

                for i, r in enumerate(group_results, 1):
                    if r.skipped:
                        icon = "⏭️"
                        status_text = f"Skipped: {r.skip_reason or ''}"
                    elif r.success:
                        icon = "✅"
                        status_text = "OK"
                    else:
                        icon = "❌"
                        status_text = f"Error: {r.error or f'HTTP {r.status_code}'}"

                    # Сокращаем path для читаемости
                    path_short = r.endpoint.path.replace(API_PREFIX, "")
                    lines.append(f"| {i} | {r.endpoint.method} | `{path_short}` | {icon} {status_text} | {r.status_code} | {r.elapsed_ms}ms |")

                lines.append("</details>\n")

            lines.append("---\n")

        # Контекст
        lines.append("## 🔗 Context Variables\n")
        if self.context:
            lines.append("| Variable | Value |")
            lines.append("|----------|-------|")
            for k, v in self.context.items():
                lines.append(f"| `{k}` | `{v}` |")
        else:
            lines.append("_No context variables extracted._\n")

        # Легенда
        lines.append("## 📖 Legend\n")
        lines.append("- **✅ Passed** — запрос выполнен, сервер вернул HTTP < 500\n")
        lines.append("- **❌ Failed** — сервер вернул HTTP ≥ 500 или ошибка подключения\n")
        lines.append("- **⏭️ Skipped** — эндпоинт пропущен (сервис не отвечает, нет ID в контексте)\n")
        lines.append("- **Ping** — проверка health-эндпоинта на порту сервиса\n")
        lines.append(f"- **Mode** — `{self.mode}`: проверяются только сервисы этого режима\n")
        lines.append("\n---\n")
        lines.append(f"_Report generated by `api_coverage_test.py` at {now}_\n")

        return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────
#  CLI
# ──────────────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PKB Neuroassistant — API Coverage Test (based on docs)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Примеры:\n"
            "  python backend/service_checker/api_coverage_test.py\n"
            "  python backend/service_checker/api_coverage_test.py --services auth,registry\n"
            "  python backend/service_checker/api_coverage_test.py --ping-only\n"
            "  python backend/service_checker/api_coverage_test.py -o coverage_report.md\n"
        ),
    )
    parser.add_argument(
        "--services",
        default=None,
        help="Список сервисов через запятую (по умолч. все)",
    )
    parser.add_argument(
        "--mode",
        choices=["mock", "real"],
        default="mock",
        help="Режим: mock (быстрый, только моки) или real (полный, реальные сервисы)",
    )
    parser.add_argument(
        "--ping-only",
        action="store_true",
        help="Только проверить какие сервисы отвечают",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Сохранить отчёт в файл (.md)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Хост для подключения (по умолч. 127.0.0.1)",
    )
    return parser.parse_args()


async def ping_all(tester: ApiCoverageTester) -> None:
    """Проверить какие сервисы отвечают (конкурентно)."""
    ports = MODE_PORTS.get(tester.mode, MODE_PORTS["mock"])
    print(f"\n  Mode: {tester.mode.upper()}")
    print(f"  {'Service':30s} Port  Status")
    print(f"  {'─'*50}")

    async def _ping_one(svc_key: str, port: int) -> Tuple[str, int, bool]:
        alive = await tester.ping_service(port, fast=True)
        return svc_key, port, alive

    results = await asyncio.gather(*[
        _ping_one(svc_key, port) for svc_key, port in sorted(ports.items())
    ])

    for svc_key, port, alive in sorted(results, key=lambda x: x[0]):
        icon = "✅" if alive else "❌"
        name = svc_key.replace("_", " ").title()
        has_impl = svc_key in tester.services_with_impl
        impl = "*" if has_impl else " "
        print(f"  {icon} {name:28s} {port}   {'Alive' if alive else 'Unreachable'} {impl}")
    print(f"\n  * — сервис имеет реализацию в этом режиме")


async def main():
    args = parse_args()

    services_list = None
    if args.services:
        services_list = [s.strip() for s in args.services.split(",")]

    tester = ApiCoverageTester(
        mode=args.mode,
        services=services_list,
        base_host=args.host,
    )

    try:
        if args.ping_only:
            await ping_all(tester)
            return

        await tester.run_all()

        # Вывод сводки
        print("\n" + "=" * 70)
        print("  ITEMS COVERAGE SUMMARY")
        print("=" * 70)
        total_ep = 0
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        for svc_key, result in tester.results.items():
            total_ep += result.endpoints_total
            total_passed += result.endpoints_passed
            total_failed += result.endpoints_failed
            total_skipped += result.endpoints_skipped
            status = "✅" if result.ping_ok else "❌"
            print(f"  {status} {result.name:35s} [{result.endpoints_passed:2d}/{result.endpoints_total:2d}]  "
                  f"failed={result.endpoints_failed}  skipped={result.endpoints_skipped}")
        print(f"\n  {'─'*60}")
        print(f"  TOTAL: {total_passed}/{total_ep} passed, "
              f"{total_failed} failed, {total_skipped} skipped\n")

        # Сохраняем отчёт
        report = tester.generate_report()
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report, encoding="utf-8")
            print(f"  📄 Report saved: {output_path.resolve()}")
        else:
            # Сохраняем с автоименем (с префиксом режима)
            prefix = "mock_" if args.mode == "mock" else "real_"
            report_path = Path(f"api_coverage_{prefix}{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
            report_path.write_text(report, encoding="utf-8")
            print(f"  📄 Report saved: {report_path.resolve()}")

    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(main())
