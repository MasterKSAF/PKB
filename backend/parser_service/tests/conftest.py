"""
Общие фикстуры для всех тестов проекта.
Обеспечивают очистку хранилища задач, клиенты для синхронного и асинхронного тестирования.
"""

import sys
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH (чтобы тесты видели модули app)
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.task_store import task_store


@pytest.fixture(scope="function")
def client():
    """
    Синхронный тестовый клиент FastAPI.
    Используется для обычных (не асинхронных) эндпоинтов.
    """
    return TestClient(app)


@pytest.fixture(scope="function")
def clear_task_store():
    """
    Очищает in‑memory хранилище задач перед каждым тестом.
    Используется для изоляции тестов друг от друга.
    """
    task_store._storage._store.clear()
    yield


@pytest.fixture(scope="session")
def event_loop():
    """
    Создаёт цикл событий asyncio для всех асинхронных тестов (одна сессия).
    Необходим для работы pytest‑asyncio.
    """
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def async_client():
    """
    Асинхронный HTTP‑клиент для тестирования эндпоинтов.
    Использует ASGITransport для подключения к FastAPI приложению.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac