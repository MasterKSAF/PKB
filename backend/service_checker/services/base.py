"""
PKB Neuroassistant — Service Definition Base.

Определяет структуры данных для описания сервисов и их эндпоинтов.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class EndpointDef:
    """Определение эндпоинта из документации.

    Поля:
        method: GET, POST, PUT, PATCH, DELETE
        path: /api/v1/... с плейсхолдерами {doc_id}, {draft_id}, {task_id} и т.д.
        group: группа эндпоинтов (classifiers, documents, ...)
        description: краткое описание
        body: тело запроса JSON (для POST/PUT/PATCH)
        form_body: multipart/form-data (вместо body)
        form_files: файлы для multipart/form-data (вместе с form_body)
        params: query-параметры
        extract_keys: какие ключи из ответа сохранять в контекст
        response_schema: схема ответа для валидации {поле: тип}
        is_preparation: True — эндпоинт создаёт данные для последующих вызовов
        expected_status: ожидаемый HTTP статус (если не указан — 2xx/3xx)
        override_port: альтернативный порт (prepare может обращаться к другому сервису)
        check: функция (body, ctx) -> Tuple[bool, str] для пост-обработки ответа
    """

    method: str  # GET, POST, PUT, PATCH, DELETE
    path: str  # /api/v1/...
    group: str  # группа эндпоинтов (classifiers, documents, ...)
    description: str  # краткое описание
    body: Optional[Dict[str, Any]] = None  # тело запроса JSON (для POST/PUT/PATCH)
    form_body: Optional[Dict[str, Any]] = None  # multipart/form-data (вместо body)
    form_files: Optional[Dict[str, tuple[str, bytes, str]]] = None  # файлы для multipart: {field: (filename, content, content_type)}
    params: Optional[Dict[str, Any]] = None  # query-параметры
    check: Optional[Any] = None  # пост-обработка ответа: (body, ctx) -> (ok, msg)
    # Если эндпоинт требует ID из предыдущего ответа — шаблон подстановки
    # {doc_id}, {session_id}, {user_id}, {version_id}, {task_id},
    # {term_id}, {classifier_code}, {comparison_id} и т.д.
    # После успешного вызова скрипт ищет эти ID в ответе и сохраняет в контекст.
    extract_keys: Optional[List[str]] = None  # какие ключи из ответа сохранять в контекст
    # Схема ответа для валидации: {поле: тип}. Проверяется при HTTP < 500
    # Вложенные поля через точку: "data.id" → str проверяет response["data"]["id"]
    response_schema: Optional[Dict[str, type]] = None
    # Если True — эндпоинт создаёт данные для последующих вызовов (prepare-шаг)
    is_preparation: bool = False
    # Ожидаемый HTTP статус (если не указан — 2xx/3xx)
    expected_status: Optional[int] = None
    # Если указан — эндпоинт выполняется на этом порту вместо порта сервиса
    # (нужно для prepare-шагов, обращающихся к другим сервисам, например auth)
    override_port: Optional[int] = None
    # Количество повторов при несовпадении expected_status (для prepare-шагов, ожидающих асинхронных данных)
    max_retries: int = 1
    # Задержка между повторами в секундах
    retry_delay: int = 1


@dataclass
class EndpointResult:
    """Результат вызова одного эндпоинта."""

    endpoint: EndpointDef
    status_code: int
    success: bool
    elapsed_ms: int = 0
    response_body: Optional[str] = None
    error: Optional[str] = None
    warnings: Optional[str] = None
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


@dataclass
class ServiceDef:
    """
    Полное описание сервиса: эндпоинты, prepare-шаги, базовые данные.

    Атрибуты:
        service_key: Ключ сервиса (registry, auth, ...)
        display_name: Отображаемое имя
        port: Порт сервиса
        needs_auth: Требуется ли JWT токен
        endpoints: Основные эндпоинты для тестирования
        prepare_endpoints: Эндпоинты подготовки данных (выполняются перед основными)
        depends_on: Список сервисов, от которых зависит
        base_data: Базовые данные для контекста (ключ → значение)
    """

    service_key: str
    display_name: str
    port: int
    needs_auth: bool = True
    endpoints: List[EndpointDef] = field(default_factory=list)
    prepare_endpoints: List[EndpointDef] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    base_data: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)  # ⚠️ workaround-предупреждения для отчёта


# ── API prefix ─────────────────────────────────────────────────────────

API_PREFIX = "/api/v1"

# ── Test credentials (единый источник) ─────────────────────────────────

# Используем admin credentials — т.к. auth-сервис создаёт admin при старте
# из DEFAULT_ADMIN_EMAIL / DEFAULT_ADMIN_PASSWORD (см. docker/.env)
TEST_CREDENTIALS: Dict[str, str] = {
    "username": "admin@example.com",
    "password": "Admin1234!",
}

TEST_ADMIN_CREDENTIALS: Dict[str, str] = {
    "username": "admin@example.com",
    "password": "Admin1234!",
}

# Креды для Gateway Mock — пароль из SEED_USERS (mocks/common.py),
# не из DEFAULT_ADMIN_PASSWORD (env), т.к. Gateway Mock не читает env.
GATEWAY_CREDENTIALS: Dict[str, str] = {
    "username": "admin@example.com",
    "password": "admin123",
}

HEADERS_JSON: Dict[str, str] = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}


# ── Mode helpers ────────────────────────────────────────────────────────

TEST_MODE_REAL = "real"
TEST_MODE_MOCK = "mock"


def get_test_mode() -> str:
    """Вернуть текущий режим тестирования.

    Приоритет:
    1. Переменная окружения TEST_MODE
    2. По умолчанию "real"
    """
    return os.environ.get("TEST_MODE", TEST_MODE_REAL).lower()


def is_real_mode(mode: Optional[str] = None) -> bool:
    """Проверить, включён ли real-режим."""
    if mode is not None:
        return mode.lower() == TEST_MODE_REAL
    return get_test_mode() == TEST_MODE_REAL


def get_credentials_for_mode(mode: Optional[str] = None) -> Dict[str, str]:
    """Вернуть credentials в зависимости от режима.

    - real: TEST_CREDENTIALS (Admin1234!) — против реального Auth
    - mock: GATEWAY_CREDENTIALS (admin123) — против Gateway Mock
    """
    if is_real_mode(mode):
        return dict(TEST_CREDENTIALS)
    return dict(GATEWAY_CREDENTIALS)
