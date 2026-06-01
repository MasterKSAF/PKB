"""Unit-тесты для retry/fallback механизма гибридного поиска.

Проверяет:
  1. _run_with_retry — 2 retry, exponential backoff, успех после N попыток
  2. Fallback dense→sparse — при ошибке dense поиск продолжается на sparse
  3. Fallback sparse→dense — при ошибке sparse поиск продолжается на dense
  4. Оба упали — ошибка пробрасывается
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.core.search.hybrid import hybrid_search


# ──────────────────────────────────────────────────────────────────────
# Вспомогательные моки
# ──────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_conn():
    """Мок подключения к БД."""
    return AsyncMock()


@pytest.fixture
def mock_embedding():
    """Мок провайдера эмбеддингов."""
    with patch("app.core.search.hybrid.get_embedding_provider") as mock:
        provider = AsyncMock()
        provider.encode.return_value = [0.1] * 1024
        mock.return_value = provider
        yield mock


@pytest.fixture
def mock_settings():
    """Мок настроек с кастомными параметрами."""
    with patch("app.core.search.hybrid.get_settings") as mock:
        settings = AsyncMock()
        settings.search_fetch_multiplier = 2
        settings.search_rrf_k = 60
        mock.return_value = settings
        yield mock


# ──────────────────────────────────────────────────────────────────────
# Тесты _run_with_retry (через hybrid_search с моками dense/sparse)
# ──────────────────────────────────────────────────────────────────────

class TestRetryMechanism:
    """Проверка retry-логики: 2 попытки, exponential backoff."""

    @pytest.mark.asyncio
    async def test_retry_success_on_second_attempt(self, mock_conn, mock_embedding, mock_settings):
        """Dense падает 1 раз, потом succeeds — retry срабатывает."""
        with patch("app.core.search.hybrid.dense_search") as mock_dense:
            # Первый вызов — ошибка, второй — успех
            mock_dense.side_effect = [
                Exception("DB connection timeout"),
                [1],
            ]

            results, total_found = await hybrid_search(
                mock_conn, query="test", top_k=5, search_type="dense",
            )

            assert len(results) == 1
            assert total_found >= 1
            # Должен быть вызван 2 раза (первый упал, второй успех)
            assert mock_dense.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_exhausted_raises_error(self, mock_conn, mock_embedding, mock_settings):
        """Dense падает 3 раза подряд — ошибка пробрасывается."""
        with patch("app.core.search.hybrid.dense_search") as mock_dense:
            mock_dense.side_effect = Exception("Persistent DB error")

            with pytest.raises(Exception, match="Persistent DB error"):
                await hybrid_search(
                    mock_conn, query="test", top_k=5, search_type="dense",
                )

            # Должен быть вызван 3 раза (1 оригинал + 2 retry)
            assert mock_dense.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_success_on_third_attempt(self, mock_conn, mock_embedding, mock_settings):
        """Dense падает 2 раза, succeeds на 3-й — все retry исчерпаны, но успех."""
        with patch("app.core.search.hybrid.dense_search") as mock_dense:
            mock_dense.side_effect = [
                Exception("Timeout 1"),
                Exception("Timeout 2"),
                [1],
            ]

            results, total_found = await hybrid_search(
                mock_conn, query="test", top_k=5, search_type="dense",
            )

            assert len(results) == 1
            assert mock_dense.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_first_attempt_success(self, mock_conn, mock_embedding, mock_settings):
        """Dense succeeds с первой попытки — retry не вызываются."""
        with patch("app.core.search.hybrid.dense_search") as mock_dense:
            mock_dense.return_value = [1, 2]

            results, total_found = await hybrid_search(
                mock_conn, query="test", top_k=5, search_type="dense",
            )

            assert len(results) == 2
            assert mock_dense.call_count == 1


# ──────────────────────────────────────────────────────────────────────
# Тесты fallback
# ──────────────────────────────────────────────────────────────────────

class TestFallbackMechanism:
    """Проверка fallback: dense→sparse, sparse→dense, оба упали."""

    @pytest.mark.asyncio
    async def test_fallback_dense_to_sparse(self, mock_conn, mock_embedding, mock_settings):
        """Dense падает после retry — fallback на sparse, результаты есть."""
        with (
            patch("app.core.search.hybrid.dense_search") as mock_dense,
            patch("app.core.search.hybrid.sparse_search") as mock_sparse,
        ):
            mock_dense.side_effect = Exception("Dense crashed")
            mock_sparse.return_value = [1, 2]

            results, total_found = await hybrid_search(
                mock_conn, query="test", top_k=5, search_type="hybrid",
            )

            # Должны быть результаты от sparse
            assert len(results) > 0
            assert mock_dense.call_count == 3  # 1 + 2 retry
            assert mock_sparse.call_count == 1  # без retry (успех)

    @pytest.mark.asyncio
    async def test_fallback_sparse_to_dense(self, mock_conn, mock_embedding, mock_settings):
        """Sparse падает после retry — fallback на dense, результаты есть."""
        with (
            patch("app.core.search.hybrid.dense_search") as mock_dense,
            patch("app.core.search.hybrid.sparse_search") as mock_sparse,
        ):
            mock_dense.return_value = [1]
            mock_sparse.side_effect = Exception("Sparse crashed")

            results, total_found = await hybrid_search(
                mock_conn, query="test", top_k=5, search_type="hybrid",
            )

            # Должны быть результаты от dense
            assert len(results) > 0
            assert mock_dense.call_count == 1  # без retry (успех)
            assert mock_sparse.call_count == 3  # 1 + 2 retry

    @pytest.mark.asyncio
    async def test_fallback_both_fail_raises_error(self, mock_conn, mock_embedding, mock_settings):
        """И dense, и sparse падают после retry — ошибка пробрасывается."""
        with (
            patch("app.core.search.hybrid.dense_search") as mock_dense,
            patch("app.core.search.hybrid.sparse_search") as mock_sparse,
        ):
            mock_dense.side_effect = Exception("Dense error")
            mock_sparse.side_effect = Exception("Sparse error")

            with pytest.raises(Exception, match="Sparse error"):
                await hybrid_search(
                    mock_conn, query="test", top_k=5, search_type="hybrid",
                )

            # Оба должны быть вызваны по 3 раза
            assert mock_dense.call_count == 3
            assert mock_sparse.call_count == 3

    @pytest.mark.asyncio
    async def test_fallback_dense_fails_sparse_succeeds_rerank(self, mock_conn, mock_embedding, mock_settings):
        """Dense падает, sparse успешен — RRF работает с одним списком."""
        with (
            patch("app.core.search.hybrid.dense_search") as mock_dense,
            patch("app.core.search.hybrid.sparse_search") as mock_sparse,
        ):
            mock_dense.side_effect = Exception("Dense error")
            mock_sparse.return_value = [1, 2]

            results, total_found = await hybrid_search(
                mock_conn, query="test", top_k=5, search_type="hybrid", rerank=True,
            )

            # RRF с одним списком: скоры должны быть 1/(k+rank)
            assert len(results) == 2
            # Первый результат должен иметь больший скор
            scores = list(results.values())
            assert scores[0] > scores[1]

    @pytest.mark.asyncio
    async def test_fallback_sparse_fails_dense_succeeds_no_rerank(self, mock_conn, mock_embedding, mock_settings):
        """Sparse падает, dense успешен, rerank=False — результаты от dense."""
        with (
            patch("app.core.search.hybrid.dense_search") as mock_dense,
            patch("app.core.search.hybrid.sparse_search") as mock_sparse,
        ):
            mock_dense.return_value = [1]
            mock_sparse.side_effect = Exception("Sparse error")

            results, total_found = await hybrid_search(
                mock_conn, query="test", top_k=5, search_type="hybrid", rerank=False,
            )

            # Без RRF все скоры = 1.0
            assert len(results) == 1
            assert all(score == 1.0 for score in results.values())
