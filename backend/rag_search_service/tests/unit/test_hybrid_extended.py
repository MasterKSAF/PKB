"""Unit-тесты для hybrid_search: расширенные edge cases + все стратегии S1-S7."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.core.search.hybrid import VALID_STRATEGIES, hybrid_search


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


class TestStrategies:
    """Тесты всех стратегий S1-S7."""

    @pytest.mark.asyncio
    async def test_s1_dense(self, mock_conn, mock_embedding, mock_settings):
        """S1: dense — только dense_search, score=1.0."""
        with patch("app.core.search.hybrid.dense_search") as mock_dense:
            mock_dense.return_value = [1, 2, 3]

            results, total_found = await hybrid_search(
                mock_conn, query="test", top_k=5, search_type="dense"
            )

            assert len(results) == 3
            assert total_found == 3
            assert all(score == 1.0 for score in results.values())
            mock_dense.assert_called_once()

    @pytest.mark.asyncio
    async def test_s2_dense_rerank_with_tei(self, mock_conn, mock_embedding, mock_settings):
        """S2: dense_rerank — TEI rerank успешен."""
        with (
            patch("app.core.search.hybrid.dense_search", return_value=[1, 2, 3]),
            patch("app.core.search.hybrid.fetch_chunk_contents", return_value={1: "a", 2: "b", 3: "c"}),
            patch("app.core.search.hybrid.get_reranker") as mock_reranker,
        ):
            reranker = AsyncMock()
            reranker.rerank.return_value = [
                AsyncMock(index=0, score=0.9),
                AsyncMock(index=2, score=0.7),
            ]
            mock_reranker.return_value = reranker

            results, total_found = await hybrid_search(
                mock_conn, query="test", top_k=2, search_type="dense_rerank"
            )

            assert len(results) == 2
            assert results[1] == 0.9
            assert results[3] == 0.7

    @pytest.mark.asyncio
    async def test_s3_sparse(self, mock_conn, mock_embedding, mock_settings):
        """S3: sparse — только sparse_search."""
        with patch("app.core.search.hybrid.sparse_search") as mock_sparse:
            mock_sparse.return_value = [10, 20]

            results, total_found = await hybrid_search(
                mock_conn, query="test", top_k=5, search_type="sparse"
            )

            assert len(results) == 2
            assert total_found == 2
            mock_sparse.assert_called_once()

    @pytest.mark.asyncio
    async def test_s4_hybrid_simple_merge(self, mock_conn, mock_embedding, mock_settings):
        """S4: hybrid — простое слияние (среднее), dense и sparse пересекаются."""
        with (
            patch("app.core.search.hybrid.dense_search", return_value=[1, 2, 3]),
            patch("app.core.search.hybrid.sparse_search", return_value=[2, 3, 4]),
        ):
            results, total_found = await hybrid_search(
                mock_conn, query="test", top_k=5, search_type="hybrid"
            )

            # id=2, id=3 в обоих → score = 1.0 (среднее)
            # id=1 только в dense → score = 1.0
            # id=4 только в sparse → score = 1.0
            assert len(results) == 4
            assert total_found == 4
            assert results[2] == 1.0
            assert results[3] == 1.0

    @pytest.mark.asyncio
    async def test_s5_hybrid_rerank(self, mock_conn, mock_embedding, mock_settings):
        """S5: hybrid_rerank — простое слияние + TEI rerank."""
        with (
            patch("app.core.search.hybrid.dense_search", return_value=[1, 2, 3]),
            patch("app.core.search.hybrid.sparse_search", return_value=[2, 3, 4]),
            patch("app.core.search.hybrid.fetch_chunk_contents", return_value={1: "a", 2: "b", 3: "c", 4: "d"}),
            patch("app.core.search.hybrid.get_reranker") as mock_reranker,
        ):
            reranker = AsyncMock()
            reranker.rerank.return_value = [
                AsyncMock(index=0, score=0.95),
                AsyncMock(index=1, score=0.80),
            ]
            mock_reranker.return_value = reranker

            results, total_found = await hybrid_search(
                mock_conn, query="test", top_k=2, search_type="hybrid_rerank"
            )

            assert len(results) == 2
            assert results[1] == 0.95
            assert results[2] == 0.80

    @pytest.mark.asyncio
    async def test_s6_hybrid_rrf(self, mock_conn, mock_embedding, mock_settings):
        """S6: hybrid_rrf — RRF слияние без rerank."""
        with (
            patch("app.core.search.hybrid.dense_search", return_value=[1, 2, 3]),
            patch("app.core.search.hybrid.sparse_search", return_value=[2, 3, 4]),
        ):
            results, total_found = await hybrid_search(
                mock_conn, query="test", top_k=5, search_type="hybrid_rrf"
            )

            # RRF: id=2, id=3 в обоих →highest scores
            assert len(results) > 0
            sorted_ids = list(results.keys())
            assert sorted_ids[0] in (2, 3)

    @pytest.mark.asyncio
    async def test_s7_hybrid_rrf_rerank(self, mock_conn, mock_embedding, mock_settings):
        """S7: hybrid_rrf_rerank — RRF + TEI rerank."""
        with (
            patch("app.core.search.hybrid.dense_search", return_value=[1, 2, 3]),
            patch("app.core.search.hybrid.sparse_search", return_value=[2, 3, 4]),
            patch("app.core.search.hybrid.fetch_chunk_contents", return_value={1: "a", 2: "b", 3: "c", 4: "d"}),
            patch("app.core.search.hybrid.get_reranker") as mock_reranker,
        ):
            reranker = AsyncMock()
            reranker.rerank.return_value = [
                AsyncMock(index=0, score=0.90),
                AsyncMock(index=1, score=0.75),
            ]
            mock_reranker.return_value = reranker

            results, total_found = await hybrid_search(
                mock_conn, query="test", top_k=2, search_type="hybrid_rrf_rerank"
            )

            # id_list = [1, 2, 3, 4] (dense + sparse deduped)
            # index=0 → id=1, score=0.90; index=1 → id=2, score=0.75
            assert len(results) == 2
            assert results[1] == 0.90
            assert results[2] == 0.75


class TestEdgeCases:
    """Edge cases для всех стратегий."""

    @pytest.mark.asyncio
    async def test_whitespace_only_query_raises_error(
        self, mock_conn, mock_embedding, mock_settings
    ):
        """Запрос из пробелов → ValueError."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            await hybrid_search(mock_conn, query="   ", top_k=5)

    @pytest.mark.asyncio
    async def test_invalid_search_type_raises_error(self, mock_conn, mock_embedding, mock_settings):
        """Невалидный search_type → ValueError."""
        with pytest.raises(ValueError, match="Invalid search_type"):
            await hybrid_search(mock_conn, query="test", top_k=5, search_type="invalid")

    @pytest.mark.asyncio
    async def test_empty_results(self, mock_conn, mock_embedding, mock_settings):
        """Пустые результаты поиска → пустой dict."""
        with (
            patch("app.core.search.hybrid.dense_search", return_value=[]),
            patch("app.core.search.hybrid.sparse_search", return_value=[]),
        ):
            results, total_found = await hybrid_search(
                mock_conn, query="test", top_k=5, search_type="hybrid"
            )
            assert results == {}
            assert total_found == 0

    @pytest.mark.asyncio
    async def test_all_strategies_are_valid(self):
        """Все 7 стратегий в VALID_STRATEGIES."""
        assert len(VALID_STRATEGIES) == 7
        assert "dense" in VALID_STRATEGIES
        assert "dense_rerank" in VALID_STRATEGIES
        assert "sparse" in VALID_STRATEGIES
        assert "hybrid" in VALID_STRATEGIES
        assert "hybrid_rerank" in VALID_STRATEGIES
        assert "hybrid_rrf" in VALID_STRATEGIES
        assert "hybrid_rrf_rerank" in VALID_STRATEGIES

    @pytest.mark.asyncio
    async def test_large_top_k(self, mock_conn, mock_embedding, mock_settings):
        """Большой top_k — результаты ограничены."""
        with patch("app.core.search.hybrid.dense_search") as mock_dense:
            mock_dense.return_value = list(range(1, 201))

            results, total_found = await hybrid_search(
                mock_conn, query="test", top_k=100, search_type="dense_rerank"
            )
            assert len(results) <= 100
