"""Unit-тесты для TEI reranking в hybrid_search."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.core.reranking.base import RerankResult, RerankingError
from app.core.search.hybrid import hybrid_search


@pytest.fixture
def mock_conn():
    return AsyncMock()


@pytest.fixture
def mock_embedding():
    with patch("app.core.search.hybrid.get_embedding_provider") as mock:
        provider = AsyncMock()
        provider.encode.return_value = [0.1] * 1024
        mock.return_value = provider
        yield mock


@pytest.fixture
def mock_settings():
    with patch("app.core.search.hybrid.get_settings") as mock:
        settings = AsyncMock()
        settings.search_fetch_multiplier = 2
        settings.search_rrf_k = 60
        settings.reranker_fetch_multiplier = 5
        settings.rerank_top_n = 50
        settings.search_top_k = 10
        mock.return_value = settings
        yield mock


def _tei_results(*indices_scores):
    """Хелпер: создаёт список RerankResult из (index, score) пар."""
    return [RerankResult(index=i, score=s, text=f"doc{i}") for i, s in indices_scores]


class TestHybridTEIRerank:
    """Тесты интеграции TEI reranker с hybrid_search."""

    @pytest.mark.asyncio
    async def test_hybrid_tei_success(self, mock_conn, mock_embedding, mock_settings):
        """S7 hybrid_rrf_rerank: TEI reranker возвращает скоры."""
        with (
            patch("app.core.search.hybrid.dense_search", return_value=[1, 2, 3]),
            patch("app.core.search.hybrid.sparse_search", return_value=[2, 3, 4]),
            patch(
                "app.core.search.hybrid.fetch_chunk_contents",
                return_value={1: "text1", 2: "text2", 3: "text3", 4: "text4"},
            ),
            patch("app.core.search.hybrid.get_reranker") as mock_get_reranker,
        ):
            reranker = AsyncMock()
            reranker.rerank.return_value = _tei_results((0, 0.95), (2, 0.80))
            mock_get_reranker.return_value = reranker

            results, total_found = await hybrid_search(
                mock_conn, query="test", top_k=2, search_type="hybrid_rrf_rerank", rerank=True
            )

            assert len(results) == 2
            assert results[1] == 0.95
            assert results[3] == 0.80
            assert total_found == 4

    @pytest.mark.asyncio
    async def test_hybrid_tei_fallback_to_rrf(self, mock_conn, mock_embedding, mock_settings):
        """S7: TEI падает → fallback на RRF."""
        with (
            patch("app.core.search.hybrid.dense_search", return_value=[1, 2, 3]),
            patch("app.core.search.hybrid.sparse_search", return_value=[2, 3, 4]),
            patch(
                "app.core.search.hybrid.fetch_chunk_contents", side_effect=RerankingError("down")
            ),
        ):
            results, total_found = await hybrid_search(
                mock_conn, query="test", top_k=5, search_type="hybrid_rrf_rerank", rerank=True
            )

            # RRF fallback: id=2 и id=3 в обоих →highest scores
            assert len(results) > 0
            sorted_ids = list(results.keys())
            assert sorted_ids[0] in (2, 3)

    @pytest.mark.asyncio
    async def test_dense_tei_success(self, mock_conn, mock_embedding, mock_settings):
        """Dense: TEI reranker успешен → результаты с TEI-скорами."""
        with (
            patch("app.core.search.hybrid.dense_search", return_value=[1, 2, 3]),
            patch(
                "app.core.search.hybrid.fetch_chunk_contents",
                return_value={1: "text1", 2: "text2", 3: "text3"},
            ),
            patch("app.core.search.hybrid.get_reranker") as mock_get_reranker,
        ):
            reranker = AsyncMock()
            reranker.rerank.return_value = _tei_results((2, 0.90), (0, 0.70))
            mock_get_reranker.return_value = reranker

            results, total_found = await hybrid_search(
                mock_conn, query="test", top_k=2, search_type="dense_rerank", rerank=True
            )

            assert len(results) == 2
            assert results[3] == 0.90
            assert results[1] == 0.70

    @pytest.mark.asyncio
    async def test_fetch_multiplier_rerank_true(self, mock_conn, mock_embedding, mock_settings):
        """rerank=True использует rerank_top_n (50) вместо search_fetch_multiplier (2)."""
        with (
            patch("app.core.search.hybrid.dense_search", return_value=[1, 2]),
            patch("app.core.search.hybrid.fetch_chunk_contents", return_value={}),
        ):
            await hybrid_search(mock_conn, query="test", top_k=5, search_type="dense_rerank", rerank=True)

            from app.core.search.hybrid import dense_search

            call_args = dense_search.call_args
            # dense_search(conn, embedding, top_k, fetch_k)
            assert call_args[0][2] == 5  # top_k
            assert call_args[0][3] == 50  # fetch_k = rerank_top_n

    @pytest.mark.asyncio
    async def test_fetch_multiplier_rerank_false(self, mock_conn, mock_embedding, mock_settings):
        """rerank=False использует search_fetch_multiplier (2)."""
        with patch("app.core.search.hybrid.dense_search", return_value=[1, 2]):
            await hybrid_search(mock_conn, query="test", top_k=5, search_type="dense_rerank", rerank=False)

            from app.core.search.hybrid import dense_search

            call_args = dense_search.call_args
            # dense_search(conn, embedding, top_k, fetch_k)
            assert call_args[0][2] == 5  # top_k
            assert call_args[0][3] == 2  # fetch_k = search_fetch_multiplier

    @pytest.mark.asyncio
    async def test_hybrid_tei_empty_fetch_contents(self, mock_conn, mock_embedding, mock_settings):
        """S7: fetch_chunk_contents вернул пустой dict → fallback на RRF."""
        with (
            patch("app.core.search.hybrid.dense_search", return_value=[1, 2]),
            patch("app.core.search.hybrid.sparse_search", return_value=[2, 3]),
            patch("app.core.search.hybrid.fetch_chunk_contents", return_value={}),
        ):
            results, total_found = await hybrid_search(
                mock_conn, query="test", top_k=5, search_type="hybrid_rrf_rerank", rerank=True
            )

            # Fallback to RRF
            assert len(results) > 0
