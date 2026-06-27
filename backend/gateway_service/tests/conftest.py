"""
PKB Neuroassistant — Gateway Service Tests: Fixtures.

Фикстуры для unit-тестов (TestClient, моки, seed-данные)
и Docker-интеграционных тестов (http_client, токены).

Docker-фикстуры (http_client, *_token) требуют запущенного Gateway в Docker.
Если Gateway недоступен — тест пропускается (pytest.skip).
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Any, AsyncGenerator, Dict, Generator
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Принудительно — тесты должны работать независимо от Docker/окружения
os.environ["ALLOW_ANONYMOUS"] = "true"

# Добавляем backend/gateway_service в sys.path для импорта модулей gateway
_GATEWAY_DIR = os.path.join(os.path.dirname(__file__), "..")
if _GATEWAY_DIR not in sys.path:
    sys.path.insert(0, _GATEWAY_DIR)


# ---------------------------------------------------------------------------
# Unit-тест фикстуры (не требуют Docker)
# ---------------------------------------------------------------------------

# Подавляем лишние логи до импорта
logging.getLogger().setLevel(logging.CRITICAL)

from gateway.main import app as _real_app
from gateway.config import config as _real_config


@pytest.fixture
def app() -> FastAPI:
    """Возвращает экземпляр FastAPI Gateway."""
    return _real_app


@pytest.fixture
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    """HTTP-клиент для тестирования Gateway."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def config() -> Any:
    """Возвращает конфигурацию Gateway (текущее состояние)."""
    return _real_config


# ---------------------------------------------------------------------------
# Seed-данные для тестов
# ---------------------------------------------------------------------------


@pytest.fixture
def test_token() -> str:
    """Тестовый JWT-токен (замоканный, невалидный для production)."""
    return "test-access-token-for-mocked-auth"


@pytest.fixture
def system_admin_user() -> Dict[str, Any]:
    """Пользователь с ролью system_admin."""
    return {
        "user_id": 1,
        "full_name": "Admin User",
        "role": "system_admin",
        "roles": ["system_admin"],
        "permissions": {
            "can_upload_documents": True,
            "can_manage_classifiers": True,
            "can_manage_terminology": True,
            "can_manage_registry": True,
        },
        "is_authenticated": True,
        "is_anonymous": False,
    }


@pytest.fixture
def knowledge_admin_user() -> Dict[str, Any]:
    """Пользователь с ролью knowledge_admin."""
    return {
        "user_id": 2,
        "full_name": "Knowledge Admin",
        "role": "knowledge_admin",
        "roles": ["knowledge_admin"],
        "permissions": {
            "can_upload_documents": True,
            "can_manage_classifiers": True,
            "can_manage_terminology": True,
            "can_manage_registry": True,
        },
        "is_authenticated": True,
        "is_anonymous": False,
    }


@pytest.fixture
def engineer_user() -> Dict[str, Any]:
    """Пользователь с ролью engineer (ограниченные права)."""
    return {
        "user_id": 3,
        "full_name": "Engineer User",
        "role": "engineer",
        "roles": ["engineer"],
        "permissions": {
            "can_upload_documents": False,
            "can_manage_classifiers": False,
            "can_manage_terminology": False,
            "can_manage_registry": False,
        },
        "is_authenticated": True,
        "is_anonymous": False,
    }


@pytest.fixture
def anonymous_user() -> Dict[str, Any]:
    """Неаутентифицированный пользователь."""
    return {
        "user_id": None,
        "full_name": None,
        "roles": [],
        "role": None,
        "permissions": {},
        "is_authenticated": False,
        "is_anonymous": True,
    }


# ---------------------------------------------------------------------------
# Мок для _validate_token_remotely (RBAC-тесты)
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_auth_validate(monkeypatch):
    """Мокает _validate_token_remotely, заполняя user_context переданными данными.

    Использование:
        mock_auth_validate(user_context)  # подставить нужный контекст
    """

    def _mock(user_context_override: Dict[str, Any]):
        async def _validate(token: str, context: Dict[str, Any]) -> bool:
            context.update(user_context_override)
            return True

        monkeypatch.setattr(
            "gateway.main._validate_token_remotely",
            _validate,
        )

    return _mock


# ---------------------------------------------------------------------------
# Мок для httpx-клиента (proxy-тесты)
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_httpx_client(monkeypatch):
    """Мокает get_client() для изоляции proxy_request от реальных HTTP-вызовов.

    Использование:
        mock_client = mock_httpx_client(response_data)
    """

    def _mock_response(
        status_code: int = 200,
        content: bytes = b'{"status": "ok"}',
        headers: Dict[str, str] = None,
        json_data: Any = None,
    ):
        if headers is None:
            headers = {"content-type": "application/json"}

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.status_code = status_code
        mock_response.headers = headers
        mock_response.content = content

        if json_data is not None:
            import json
            mock_response.content = json.dumps(json_data).encode()

        async def mock_request(method, url, **kwargs):
            return mock_response

        mock_client.request = mock_request

        monkeypatch.setattr("gateway.client.get_client", lambda: mock_client)
        return mock_client

    return _mock_response


# ---------------------------------------------------------------------------
# Настройка логирования для тестов
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _silence_logging():
    """Отключает лишние логи во время тестов."""
    logging.getLogger().setLevel(logging.CRITICAL)
    logging.getLogger("gateway").setLevel(logging.CRITICAL)
    logging.getLogger("httpx").setLevel(logging.CRITICAL)
    logging.getLogger("httpcore").setLevel(logging.CRITICAL)
    yield


# ---------------------------------------------------------------------------
# Cleanup тестового rate limiter
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Сбрасывает rate limiter между тестами."""
    try:
        from gateway.rate_limiter import reset_limiter
        reset_limiter()
    except ImportError:
        pass
    yield


# ---------------------------------------------------------------------------
# Docker-интеграционные фикстуры (требуют запущенного Gateway)
# ---------------------------------------------------------------------------

# URL Gateway в Docker (проброшен на хост)
GATEWAY_DOCKER_URL = os.getenv("GATEWAY_TEST_URL", "http://127.0.0.1:18080")
HTTP_TIMEOUT = float(os.getenv("GATEWAY_TEST_TIMEOUT", "10.0"))

# Тестовые credentials (seed-данные из mocks/common.py)
ADMIN_CREDENTIALS = {"username": "admin@example.com", "password": "admin123"}
ENGINEER_CREDENTIALS = {"username": "ivanov@example.com", "password": "secret123"}
KNOWLEDGE_ADMIN_CREDENTIALS = {"username": "petrova@example.com", "password": "secret456"}


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
        pytest.skip("Gateway в Docker недоступен. Запустите recheck.bat или docker compose up -d")

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
    """JWT токен system_admin."""
    resp = await http_client.post(
        f"{GATEWAY_DOCKER_URL}/api/v1/auth/token",
        json=ADMIN_CREDENTIALS,
    )
    assert resp.status_code == 200
    data = resp.json()
    return data["access_token"]


@pytest.fixture
def anyio_backend():
    """Backend для pytest-asyncio."""
    return "asyncio"
