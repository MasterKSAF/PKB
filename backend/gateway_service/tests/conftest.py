"""
PKB Neuroassistant — Gateway Integration Tests: Fixtures.

Фикстуры:
  - docker_gateway_base: str — URL Gateway в Docker (http://127.0.0.1:18080)
  - http_client: async-клиент для HTTP-вызовов к Docker
  - admin_token / engineer_token: JWT для RBAC-тестов
  - gateway_app: экземпляр FastAPI (для unit-тестов внутренних функций)

Фикстуры с префиксом docker_ требуют запущенного Gateway в Docker.
Если Gateway недоступен — тест пропускается (pytest.skip).
"""

from __future__ import annotations

import os
import sys
from typing import AsyncGenerator, Dict, Optional

import httpx
import pytest
import pytest_asyncio

# Принудительно устанавливаем ALLOW_ANONYMOUS=true для unit-тестов
os.environ["ALLOW_ANONYMOUS"] = "true"

# Добавляем backend/gateway_service в sys.path для импорта модулей gateway
_GATEWAY_DIR = os.path.join(os.path.dirname(__file__), "..")
if _GATEWAY_DIR not in sys.path:
    sys.path.insert(0, _GATEWAY_DIR)

# ---------------------------------------------------------------------------
# Конфигурация
# ---------------------------------------------------------------------------

# URL Gateway в Docker (проброшен на хост)
GATEWAY_DOCKER_URL = os.getenv("GATEWAY_TEST_URL", "http://127.0.0.1:18080")
# Таймауты
HTTP_TIMEOUT = float(os.getenv("GATEWAY_TEST_TIMEOUT", "10.0"))

# Тестовые credentials (seed-данные из mocks/common.py)
ADMIN_CREDENTIALS = {"username": "admin@example.com", "password": "admin123"}
ENGINEER_CREDENTIALS = {"username": "ivanov@example.com", "password": "secret123"}
KNOWLEDGE_ADMIN_CREDENTIALS = {"username": "petrova@example.com", "password": "secret456"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def is_docker_gateway_alive(base_url: str = GATEWAY_DOCKER_URL) -> bool:
    """Проверяет, отвечает ли Gateway в Docker."""
    try:
        r = httpx.get(f"{base_url}/api/v1/health", timeout=3.0)
        return r.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException):
        return False


async def async_is_docker_gateway_alive(base_url: str = GATEWAY_DOCKER_URL) -> bool:
    """Async проверка Gateway в Docker."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{base_url}/api/v1/health")
            return r.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException):
        return False


# ---------------------------------------------------------------------------
# Unit-тест фикстуры (не требуют Docker)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def gateway_app():
    """Возвращает экземпляр FastAPI Gateway для unit-тестов.

    Импортирует реальный gateway.main.
    Для тестов, которые тестируют resolve_service, config, rate_limiter и т.д.
    """
    from gateway.main import app
    return app


@pytest.fixture(scope="module")
def gateway_config():
    """GatewayConfig для unit-тестов конфигурации."""
    from gateway.config import GatewayConfig
    return GatewayConfig


@pytest.fixture(scope="module")
def route_table():
    """ROUTE_TABLE для тестов resolve_service."""
    from gateway.client import ROUTE_TABLE
    return ROUTE_TABLE


# ---------------------------------------------------------------------------
# Docker-интеграционные фикстуры (требуют запущенного Gateway)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def docker_gateway_base() -> str:
    """Базовый URL Gateway в Docker."""
    return GATEWAY_DOCKER_URL


@pytest_asyncio.fixture(scope="session")
async def http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """HTTP-клиент для интеграционных тестов.

    Если Gateway в Docker не отвечает — тест пропускается.
    """
    alive = await async_is_docker_gateway_alive()
    if not alive:
        pytest.skip("Gateway в Docker недоступен. Запустите recheck.bat или docker compose up -d app")

    async with httpx.AsyncClient(timeout=httpx.Timeout(HTTP_TIMEOUT)) as client:
        yield client


@pytest_asyncio.fixture(scope="session")
async def admin_token(http_client: httpx.AsyncClient) -> str:
    """JWT токен администратора (system_admin)."""
    resp = await http_client.post(
        f"{GATEWAY_DOCKER_URL}/api/v1/auth/token",
        json=ADMIN_CREDENTIALS,
    )
    assert resp.status_code == 200, (
        f"Не удалось получить admin token: {resp.status_code} {resp.text[:200]}"
    )
    data = resp.json()
    return data["access_token"]


@pytest_asyncio.fixture(scope="session")
async def engineer_token(http_client: httpx.AsyncClient) -> str:
    """JWT токен инженера (engineer)."""
    resp = await http_client.post(
        f"{GATEWAY_DOCKER_URL}/api/v1/auth/token",
        json=ENGINEER_CREDENTIALS,
    )
    assert resp.status_code == 200, (
        f"Не удалось получить engineer token: {resp.status_code} {resp.text[:200]}"
    )
    data = resp.json()
    return data["access_token"]


@pytest_asyncio.fixture(scope="session")
async def knowledge_admin_token(http_client: httpx.AsyncClient) -> str:
    """JWT токен knowledge_admin."""
    resp = await http_client.post(
        f"{GATEWAY_DOCKER_URL}/api/v1/auth/token",
        json=KNOWLEDGE_ADMIN_CREDENTIALS,
    )
    assert resp.status_code == 200, (
        f"Не удалось получить knowledge_admin token: {resp.status_code} {resp.text[:200]}"
    )
    data = resp.json()
    return data["access_token"]


@pytest_asyncio.fixture(scope="session")
async def system_admin_token(http_client: httpx.AsyncClient) -> str:
    """JWT токен system_admin (тот же admin)."""
    resp = await http_client.post(
        f"{GATEWAY_DOCKER_URL}/api/v1/auth/token",
        json=ADMIN_CREDENTIALS,
    )
    assert resp.status_code == 200
    data = resp.json()
    return data["access_token"]


# ---------------------------------------------------------------------------
# Утилиты для тестов
# ---------------------------------------------------------------------------


@pytest.fixture
def anyio_backend():
    """Backend для pytest-asyncio."""
    return "asyncio"
