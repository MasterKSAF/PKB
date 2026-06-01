"""Общие фикстуры для тестов."""

from typing import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.core.database import init_db_pool, close_db_pool


@pytest_asyncio.fixture(scope="function")
async def setup_database():
    """Инициализируем пул БД перед каждым тестом и закрываем после."""
    await init_db_pool()
    yield
    await close_db_pool()


@pytest_asyncio.fixture
async def client(setup_database) -> AsyncIterator[AsyncClient]:
    """HTTP-клиент для интеграционных тестов."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac