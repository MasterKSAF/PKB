"""Unit-тесты для модуля reranking (TEI provider, factory, chunks helper)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.core.reranking.base import RerankResult, RerankingError
from app.core.reranking.tei_provider import TEIRerankerProvider
from app.core.search.chunks import fetch_chunk_contents


class TestRerankResult:
    """Тесты модели RerankResult."""

    def test_rerank_result_fields(self):
        r = RerankResult(index=0, score=0.95, text="hello")
        assert r.index == 0
        assert r.score == 0.95
        assert r.text == "hello"


class TestTEIRerankerProvider:
    """Тесты TEI reranking-провайдера."""

    @pytest.fixture
    def mock_settings(self):
        with patch("app.core.reranking.tei_provider.get_settings") as m:
            settings = MagicMock()
            settings.reranker_base_url = "http://localhost:8080"
            settings.reranker_model = "BAAI/bge-reranker-v2-m3"
            settings.reranker_timeout = 10
            m.return_value = settings
            yield m

    def _make_provider(self, mock_settings):
        return TEIRerankerProvider()

    @pytest.mark.asyncio
    async def test_rerank_success(self, mock_settings):
        provider = self._make_provider(mock_settings)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "results": [
                {"index": 1, "score": 0.95, "text": "doc2"},
                {"index": 0, "score": 0.80, "text": "doc1"},
            ]
        }
        with patch.object(provider._client, "post", new_callable=AsyncMock, return_value=mock_resp):
            results = await provider.rerank("query", ["doc1", "doc2"], top_n=2)

        assert len(results) == 2
        assert results[0].index == 1
        assert results[0].score == 0.95
        assert results[1].index == 0
        assert results[1].score == 0.80
        await provider.close()

    @pytest.mark.asyncio
    async def test_rerank_empty_documents(self, mock_settings):
        provider = self._make_provider(mock_settings)
        results = await provider.rerank("query", [], top_n=10)
        assert results == []
        await provider.close()

    @pytest.mark.asyncio
    async def test_rerank_connection_error(self, mock_settings):
        provider = self._make_provider(mock_settings)
        with patch.object(
            provider._client,
            "post",
            new_callable=AsyncMock,
            side_effect=httpx.ConnectError("connection refused"),
        ):
            with pytest.raises(RerankingError, match="connection refused"):
                await provider.rerank("query", ["doc1"], top_n=1)
        await provider.close()

    @pytest.mark.asyncio
    async def test_rerank_timeout(self, mock_settings):
        provider = self._make_provider(mock_settings)
        with patch.object(
            provider._client,
            "post",
            new_callable=AsyncMock,
            side_effect=httpx.TimeoutException("timeout"),
        ):
            with pytest.raises(RerankingError, match="timeout"):
                await provider.rerank("query", ["doc1"], top_n=1)
        await provider.close()

    @pytest.mark.asyncio
    async def test_rerank_http_error(self, mock_settings):
        provider = self._make_provider(mock_settings)
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500", request=MagicMock(), response=mock_resp
        )
        with patch.object(provider._client, "post", new_callable=AsyncMock, return_value=mock_resp):
            with pytest.raises(RerankingError, match="HTTP error"):
                await provider.rerank("query", ["doc1"], top_n=1)
        await provider.close()

    @pytest.mark.asyncio
    async def test_rerank_empty_results(self, mock_settings):
        provider = self._make_provider(mock_settings)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"results": []}
        with patch.object(provider._client, "post", new_callable=AsyncMock, return_value=mock_resp):
            results = await provider.rerank("query", ["doc1"], top_n=1)
        assert results == []
        await provider.close()

    def test_get_model_name(self, mock_settings):
        provider = self._make_provider(mock_settings)
        assert provider.get_model_name() == "BAAI/bge-reranker-v2-m3"


class TestRerankerFactory:
    """Тесты фабрики reranker."""

    def test_singleton(self):
        from app.core.reranking.factory import get_reranker

        with patch("app.core.reranking.factory.TEIRerankerProvider"):
            r1 = get_reranker()
            r2 = get_reranker()
            assert r1 is r2


class TestFetchChunkContents:
    """Тесты хелпера fetch_chunk_contents."""

    @pytest.mark.asyncio
    async def test_fetch_success(self):
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [
            {"id": 1, "content": "text1"},
            {"id": 2, "content": "text2"},
        ]
        result = await fetch_chunk_contents(mock_conn, [1, 2])
        assert result == {1: "text1", 2: "text2"}
        mock_conn.fetch.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_empty_ids(self):
        mock_conn = AsyncMock()
        result = await fetch_chunk_contents(mock_conn, [])
        assert result == {}
        mock_conn.fetch.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetch_no_results(self):
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = []
        result = await fetch_chunk_contents(mock_conn, [999])
        assert result == {}
