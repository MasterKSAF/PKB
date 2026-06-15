"""
Общие фикстуры для всех тестов проекта.
Обеспечивают очистку хранилища задач, клиенты для синхронного и асинхронного тестирования.
"""
import os
import sys
from pathlib import Path
import asyncio
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock, MagicMock


# Очищаем переменные, которые могут переопределить таймауты из окружения
for env_var in ["PREVIEW_TIMEOUT", "PIPELINE_TIMEOUT", "PARSER_TIMEOUT", "VALIDATION_GLOBAL_TIMEOUT"]:
    os.environ.pop(env_var, None)

# Устанавливаем переменные окружения для тестов (до импорта app)
os.environ.setdefault("MINIO_ENDPOINT", "localhost:9000")
os.environ.setdefault("MINIO_ACCESS_KEY", "test_access")
os.environ.setdefault("MINIO_SECRET_KEY", "test_secret")
os.environ.setdefault("MINIO_BUCKET", "test-bucket")
os.environ.setdefault("MINIO_IMAGE_BUCKET", "test-images")
os.environ.setdefault("LOG_LEVEL", "INFO")

# Добавляем корень проекта в PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from app.main import app
from app.core.task_store import task_store


@pytest.fixture(scope="function")
def client():
    """Синхронный тестовый клиент FastAPI."""
    return TestClient(app)


@pytest.fixture(scope="function")
def clear_task_store():
    """Очищает in‑memory хранилище задач перед каждым тестом."""
    task_store._store.clear()
    task_store._locks.clear()
    task_store._notifier._conditions.clear()
    task_store._notifier._versions.clear()
    yield


@pytest.fixture(scope="session")
def event_loop():
    """Создаёт цикл событий asyncio для всех асинхронных тестов."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def async_client():
    """Асинхронный HTTP‑клиент для тестирования эндпоинтов."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture(scope="function")
async def async_client_v2():
    """Асинхронный HTTP‑клиент для тестирования эндпоинтов v2."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test/api/v2"
    ) as ac:
        yield ac


# Общие моки для MinIO и валидатора
@pytest.fixture
def mock_minio_download():
    with patch("app.services.file_loader.minio_client.download_file", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def mock_validator():
    with patch("app.services.file_loader.Validator.validate") as mock:
        mock.return_value = "application/pdf"
        yield mock


@pytest.fixture
def mock_pipeline_preview():
    with patch("app.api.v2.endpoints.process.Pipeline.create") as mock:
        mock_pipeline = AsyncMock()
        mock_ctx = MagicMock()
        mock_ctx.final_json = {
            "content": {
                "document": {"source": {"file_name": "test.pdf", "page_count": 2}}
            }
        }
        mock_pipeline.run = AsyncMock(return_value=mock_ctx)
        mock.return_value = mock_pipeline
        yield mock