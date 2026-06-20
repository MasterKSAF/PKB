"""Unit-тесты для цепочек распространения ошибок."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


def _make_mock_pool(conn=None):
    """Создать мок пула с properly mocked context manager для acquire()."""
    mock_pool = MagicMock()
    mock_pool.is_closing = MagicMock(return_value=False)
    if conn is None:
        conn = AsyncMock()
        conn.fetch = AsyncMock(return_value=[])
        conn.fetchval = AsyncMock(return_value=1)
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=conn)
    cm.__aexit__ = AsyncMock(return_value=False)
    mock_pool.acquire = MagicMock(return_value=cm)
    return mock_pool


@pytest.fixture
async def api_client():
    """HTTP-клиент для тестов ошибок."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestErrorPropagation:
    """Тесты цепочек ошибок: от нижнего уровня до API-ответа."""

    @pytest.mark.asyncio
    async def test_db_connection_failure_returns_search_failed(self, api_client):
        """DB недоступна → hybrid_search падает → endpoint возвращает 500 SEARCH_FAILED."""
        mock_pool = MagicMock()
        mock_pool.acquire = MagicMock(side_effect=Exception("Connection refused"))

        with patch("app.core.database._pool", mock_pool):
            response = await api_client.post(
                "/api/v1/rag/search",
                json={"query": "test", "top_k": 5},
            )

            assert response.status_code == 500
            data = response.json()
            assert data["error"]["code"] == "SEARCH_FAILED"
            assert "Connection refused" in data["error"]["message"]

    @pytest.mark.asyncio
    async def test_embedding_provider_down_returns_error(self, api_client):
        """Embedding provider недоступен → ошибка в search → 500 SEARCH_FAILED."""
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])
        pool = _make_mock_pool(mock_conn)

        with (
            patch("app.core.database._pool", pool),
            patch(
                "app.core.search.hybrid.get_embedding_provider",
                side_effect=Exception("Embedding service unavailable"),
            ),
        ):
            response = await api_client.post(
                "/api/v1/rag/search",
                json={"query": "test", "top_k": 5},
            )

            assert response.status_code == 500
            data = response.json()
            assert data["error"]["code"] == "SEARCH_FAILED"

    @pytest.mark.asyncio
    async def test_both_search_strategies_fail(self, api_client):
        """Dense и sparse оба падают → 500 SEARCH_FAILED."""
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])
        pool = _make_mock_pool(mock_conn)

        with (
            patch("app.core.database._pool", pool),
            patch(
                "app.core.search.hybrid.get_embedding_provider",
                return_value=AsyncMock(encode=AsyncMock(return_value=[0.1] * 1024)),
            ),
            patch("app.core.search.hybrid.dense_search", side_effect=Exception("Dense error")),
            patch("app.core.search.hybrid.sparse_search", side_effect=Exception("Sparse error")),
        ):
            response = await api_client.post(
                "/api/v1/rag/search",
                json={"query": "test", "top_k": 5},
            )

            assert response.status_code == 500
            data = response.json()
            assert data["error"]["code"] == "SEARCH_FAILED"

    @pytest.mark.asyncio
    async def test_health_check_when_pool_is_none(self, api_client):
        """Health check при pool=None → degraded (не 500)."""
        with (
            patch("app.core.database._pool", None),
            patch("app.core.database.check_db_health") as mock_health,
        ):
            mock_health.return_value = {"status": "error", "detail": "Pool not initialized"}

            response = await api_client.get("/api/v1/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"

    @pytest.mark.asyncio
    async def test_search_returns_empty_when_no_chunks(self, api_client):
        """Поиск без результатов → 200 с пустым results."""
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])
        pool = _make_mock_pool(mock_conn)

        with (
            patch("app.core.database._pool", pool),
            patch("app.core.search.hybrid.hybrid_search", return_value=({}, 0)),
            patch("app.core.search.hybrid.get_embedding_provider") as mock_emb,
        ):
            mock_emb.return_value.encode = AsyncMock(return_value=[0.1] * 1024)
            response = await api_client.post(
                "/api/v1/rag/search",
                json={"query": "nonexistent query", "top_k": 5},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["results"] == []
            assert data["total_found"] == 0

    @pytest.mark.asyncio
    async def test_error_response_does_not_leak_stack_trace(self, api_client):
        """Ответ ошибки не содержит traceback."""
        mock_pool = MagicMock()
        mock_pool.acquire = MagicMock(side_effect=RuntimeError("secret_detail"))

        with patch("app.core.database._pool", mock_pool):
            response = await api_client.post(
                "/api/v1/rag/search",
                json={"query": "test", "top_k": 5},
            )

            assert response.status_code == 500
            data = response.json()
            assert "error" in data
            assert "code" in data["error"]
            assert "Traceback" not in data["error"].get("message", "")
