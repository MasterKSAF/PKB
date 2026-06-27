"""
Fixtures for Gateway Service tests.

Предоставляет:
  - TestClient(app) с настроенным экземпляром FastAPI
  - Мок-сервисы через mocks/gateway (для интеграционных тестов)
  - Сид-данные: тестовый токен, пользователи, документы, черновики
  - Конфигурация: ALLOW_ANONYMOUS=True по умолчанию
  - Логирование на CRITICAL для тестов
"""

import logging
import os
import sys
from typing import Any, Dict, Generator
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Путь к корню gateway_service
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


# ---------------------------------------------------------------------------
# Force test configuration before importing gateway modules
# ---------------------------------------------------------------------------

# Принудительно — тесты должны работать независимо от Docker/окружения
os.environ["ALLOW_ANONYMOUS"] = "true"
os.environ["GATEWAY_MODE"] = "real"
os.environ["ENV"] = "development"
os.environ["RATE_LIMIT_ENABLED"] = "0"  # отключаем rate limiting
os.environ["GATEWAY_LOG_LEVEL"] = "CRITICAL"


# ---------------------------------------------------------------------------
# Импортируем после настройки переменных окружения
# ---------------------------------------------------------------------------

# Подавляем лишние логи до импорта
logging.getLogger().setLevel(logging.CRITICAL)

from gateway.main import app as _real_app
from gateway.config import config as _real_config


# ---------------------------------------------------------------------------
# Redis-зависимости не нужны — rate limiter in-memory
# ---------------------------------------------------------------------------


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
