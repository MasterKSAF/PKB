"""Integration-тесты для модуля гибридного поиска."""

import pytest
import pytest_asyncio
import asyncpg
from typing import AsyncIterator

from app.core.search.hybrid import hybrid_search
from app.core.database import get_pool


@pytest_asyncio.fixture
async def db_conn(setup_database) -> AsyncIterator[asyncpg.Connection]:
    """Фикстура для получения подключения к тестовой БД."""
    pool = get_pool()
    async with pool.acquire() as conn:
        yield conn


class TestHybridSearch:
    """Integration-тесты для гибридного поиска."""

    @pytest.mark.asyncio
    async def test_dense_search_returns_results(self, db_conn: asyncpg.Connection):
        """Dense search возвращает результаты из тестовой БД."""
        query = "ледовый класс"
        results, total_found = await hybrid_search(
            db_conn,
            query=query,
            top_k=5,
            search_type="dense",
            rerank=False,
        )

        assert isinstance(results, dict)
        assert len(results) > 0
        assert total_found >= len(results)
        assert all(isinstance(k, int) for k in results.keys())
        assert all(isinstance(v, float) for v in results.values())

    @pytest.mark.asyncio
    async def test_sparse_search_returns_results(self, db_conn: asyncpg.Connection):
        """Sparse search возвращает результаты из тестовой БД."""
        query = "толщина обшивки"
        results, total_found = await hybrid_search(
            db_conn,
            query=query,
            top_k=5,
            search_type="sparse",
            rerank=False,
        )

        assert isinstance(results, dict)
        assert total_found >= len(results)

    @pytest.mark.asyncio
    async def test_hybrid_search_with_rerank(self, db_conn: asyncpg.Connection):
        """Hybrid search с RRF возвращает результаты с корректными скорами."""
        query = "ледовый класс Arc4"
        results, total_found = await hybrid_search(
            db_conn,
            query=query,
            top_k=5,
            search_type="hybrid",
            rerank=True,
        )

        assert isinstance(results, dict)
        assert len(results) > 0
        assert total_found >= len(results)

        # Проверяем, что скоры убывают
        score_values = list(results.values())
        for i in range(len(score_values) - 1):
            assert score_values[i] >= score_values[i + 1]

    @pytest.mark.asyncio
    async def test_hybrid_search_without_rerank(self, db_conn: asyncpg.Connection):
        """Hybrid search без RRF возвращает результаты с score=1.0."""
        query = "методика испытаний"
        results, total_found = await hybrid_search(
            db_conn,
            query=query,
            top_k=3,
            search_type="hybrid",
            rerank=False,
        )

        assert isinstance(results, dict)
        assert total_found >= len(results)
        # Без RRF все скоры должны быть 1.0
        assert all(score == 1.0 for score in results.values())

    @pytest.mark.asyncio
    async def test_empty_query_raises_error(self, db_conn: asyncpg.Connection):
        """Пустой запрос вызывает ValueError."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            await hybrid_search(
                db_conn,
                query="",
                top_k=5,
                search_type="hybrid",
                rerank=True,
            )

    @pytest.mark.asyncio
    async def test_invalid_search_type_raises_error(self, db_conn: asyncpg.Connection):
        """Невалидный search_type вызывает ValueError."""
        with pytest.raises(ValueError, match="Invalid search_type"):
            await hybrid_search(
                db_conn,
                query="test",
                top_k=5,
                search_type="invalid",  # type: ignore
                rerank=True,
            )

    @pytest.mark.asyncio
    async def test_top_k_limits_results(self, db_conn: asyncpg.Connection):
        """Параметр top_k ограничивает количество результатов."""
        query = "обшивка"
        top_k = 2
        results, total_found = await hybrid_search(
            db_conn,
            query=query,
            top_k=top_k,
            search_type="hybrid",
            rerank=True,
        )

        assert len(results) <= top_k
        assert total_found >= len(results)