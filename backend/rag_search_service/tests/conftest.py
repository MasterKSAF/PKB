"""Общие фикстуры для тестов."""

from typing import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

import pytest
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


@pytest.fixture
def mock_settings():
    """Мок настроек сервиса с типичными значениями."""
    settings = MagicMock()
    settings.service_name = "rag-search"
    settings.service_version = "0.1.0"
    settings.service_port = 8091
    settings.log_level = "INFO"
    settings.log_pii_fields = "password,access_token,refresh_token"
    settings.postgres_user = "rag_user"
    settings.postgres_password = "rag_password"
    settings.postgres_db = "knowledge_base"
    settings.postgres_host = "127.0.0.1"
    settings.postgres_port = 5433
    settings.postgres_pool_min = 2
    settings.postgres_pool_max = 10
    settings.embedding_api_key = ""
    settings.embedding_base_url = "http://localhost:7997"
    settings.embedding_model = "Qwen/Qwen3-Embedding-0.6B"
    settings.embedding_dim = 1024
    settings.embedding_timeout = 60
    settings.embedding_instruction = ""
    settings.search_top_k = 10
    settings.search_max_top_k = 100
    settings.search_rrf_k = 60
    settings.search_fetch_multiplier = 2
    settings.reranker_base_url = "http://localhost:8080"
    settings.reranker_model = "BAAI/bge-reranker-v2-m3"
    settings.reranker_timeout = 10
    settings.reranker_fetch_multiplier = 5
    settings.health_check_timeout = 5
    settings.database_url = "postgresql://rag_user:rag_password@127.0.0.1:5433/knowledge_base"
    settings.pii_fields_list = ["password", "access_token", "refresh_token"]
    return settings


@pytest.fixture
def mock_db_pool():
    """Мок пула подключений к БД."""
    pool = AsyncMock()
    conn = AsyncMock()
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
    pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)
    pool.is_closing.return_value = False
    return pool


@pytest.fixture
def mock_embedding_provider():
    """Мок провайдера эмбеддингов."""
    provider = AsyncMock()
    provider.encode.return_value = [0.1] * 1024
    provider.get_dimension.return_value = 1024
    provider.get_model_name.return_value = "openai-compatible:Qwen/Qwen3-Embedding-0.6B"
    provider.close.return_value = None
    return provider
