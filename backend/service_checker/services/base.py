"""
PKB Neuroassistant — Service Definition Base.

Определяет структуры данных для описания сервисов и их эндпоинтов.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


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
    # Если True — эндпоинт создаёт данные для последующих вызовов (prepare-шаг)
    is_preparation: bool = False
    # Ожидаемый HTTP статус (для prepare-шагов)
    expected_status: int = 200


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

HEADERS_JSON: Dict[str, str] = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}
