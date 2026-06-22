"""Unit-тесты для FastAPI endpoints: validation, root, health, exception handlers."""

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
    """HTTP-клиент для тестов."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestRootEndpoint:
    """Тесты GET /."""

    @pytest.mark.asyncio
    async def test_root_returns_service_info(self, api_client):
        response = await api_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "rag-search"
        assert data["version"] == "0.1.0"
        assert data["status"] == "running"
        assert data["docs"] == "/docs"


class TestHealthEndpoint:
    """Тесты GET /health."""

    @pytest.mark.asyncio
    async def test_health_ok(self, api_client):
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=1)
        mock_conn.fetch = AsyncMock(
            return_value=[
                {"schema_name": "registry"},
                {"schema_name": "rag"},
            ]
        )
        pool = _make_mock_pool(mock_conn)

        with patch("app.core.database._pool", pool):
            response = await api_client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "rag-search"
        assert "uptime_seconds" in data
        assert data["details"]["database"]["status"] == "ok"

    @pytest.mark.asyncio
    async def test_health_degraded_when_db_down(self, api_client):
        mock_pool = MagicMock()
        mock_pool.acquire = MagicMock(side_effect=Exception("Connection refused"))

        with patch("app.core.database._pool", mock_pool):
            response = await api_client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"


class TestSearchEndpointValidation:
    """Тесты валидации входных данных на endpoint."""

    @pytest.mark.asyncio
    async def test_missing_query_returns_422(self, api_client):
        response = await api_client.post(
            "/api/v1/rag/search",
            json={"valid_at": "2026-06-18"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_valid_at_returns_422(self, api_client):
        response = await api_client.post(
            "/api/v1/rag/search",
            json={"query": "test"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_empty_body_returns_422(self, api_client):
        response = await api_client.post(
            "/api/v1/rag/search",
            json={},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_empty_query_returns_400(self, api_client):
        """Пустой query → 400 EMPTY_QUERY."""
        response = await api_client.post(
            "/api/v1/rag/search",
            json={"query": "", "valid_at": "2026-06-18"},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "EMPTY_QUERY"

    @pytest.mark.asyncio
    async def test_valid_request_accepted(self, api_client):
        """Валидный запрос — endpoint не падает с 422."""
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])
        pool = _make_mock_pool(mock_conn)

        with (
            patch("app.core.database._pool", pool),
            patch("app.core.search.hybrid.hybrid_search", return_value=({1: 1.0}, 1)),
            patch("app.core.search.hybrid.get_embedding_provider") as mock_emb,
            patch("app.api.v1.search.expand_context_batch", return_value={}),
        ):
            mock_emb.return_value.encode = AsyncMock(return_value=[0.1] * 1024)
            response = await api_client.post(
                "/api/v1/rag/search",
                json={"query": "test", "valid_at": "2026-06-18"},
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_valid_request_with_filters(self, api_client):
        """Валидный запрос с фильтрами."""
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])
        pool = _make_mock_pool(mock_conn)

        with (
            patch("app.core.database._pool", pool),
            patch("app.core.search.hybrid.hybrid_search", return_value=({1: 1.0}, 1)),
            patch("app.core.search.hybrid.get_embedding_provider") as mock_emb,
            patch("app.api.v1.search.expand_context_batch", return_value={}),
        ):
            mock_emb.return_value.encode = AsyncMock(return_value=[0.1] * 1024)
            response = await api_client.post(
                "/api/v1/rag/search",
                json={
                    "query": "test",
                    "valid_at": "2026-06-18",
                    "filters": {
                        "document_type": ["normative"],
                        "category_ids": [1, 2],
                        "document_ids": [10],
                    },
                },
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_response_has_new_format(self, api_client):
        """Ответ содержит source/retrieval/context структуру."""
        mock_conn = AsyncMock()
        # Возвращаем строку с данными чанка
        mock_conn.fetch = AsyncMock(return_value=[
            {
                "chunk_id": 1,
                "document_id": 42,
                "section_id": 8,
                "chunk_index": 0,
                "clause": "6.1",
                "section_path": "6/6.1",
                "section_bbox": None,
                "section_title": "Допуск соосности",
                "page": 2,
                "content": "Для ледового класса Arc4...",
            }
        ])
        pool = _make_mock_pool(mock_conn)

        with (
            patch("app.core.database._pool", pool),
            patch("app.api.v1.search.hybrid_search", return_value=({1: 0.87}, 1)),
            patch("app.api.v1.search.expand_context_batch", return_value={1: []}),
        ):
            response = await api_client.post(
                "/api/v1/rag/search",
                json={"query": "test", "valid_at": "2026-06-18"},
            )
            assert response.status_code == 200
            data = response.json()
            assert "results" in data
            assert len(data["results"]) == 1
            result = data["results"][0]
            assert "source" in result
            assert "retrieval" in result
            assert "context" in result
            assert result["source"]["document_id"] == 42
            assert result["source"]["clause"] == "6.1"
            assert result["source"]["path"] == "6/6.1"
            assert result["retrieval"]["chunk_id"] == 1
            assert result["retrieval"]["score"] == 0.87
            assert result["retrieval"]["mode"] == "dense_rerank"
