"""Unit-тесты для database.py: vector codec, pool management, health check."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from app.core.database import (
    _vector_decoder,
    _vector_encoder,
    check_db_health,
    get_pool,
    init_db_pool,
)


class TestVectorEncoder:
    """Тесты кодека: Python list → pgvector строка."""

    def test_list_to_string(self):
        result = _vector_encoder([1.0, 2.0, 3.0])
        assert result == "[1.0,2.0,3.0]"

    def test_numpy_array_to_string(self):
        arr = np.array([1.0, 2.0, 3.0])
        result = _vector_encoder(arr)
        assert result == "[1.0,2.0,3.0]"

    def test_empty_list(self):
        result = _vector_encoder([])
        assert result == "[]"

    def test_single_element(self):
        result = _vector_encoder([42.0])
        assert result == "[42.0]"

    def test_negative_values(self):
        result = _vector_encoder([-1.5, 0.0, 2.5])
        assert result == "[-1.5,0.0,2.5]"

    def test_large_vector(self):
        vec = [float(i) for i in range(1024)]
        result = _vector_encoder(vec)
        assert result.startswith("[")
        assert result.endswith("]")
        assert len(result) > 1000


class TestVectorDecoder:
    """Тесты кодека: pgvector строка → Python list."""

    def test_string_to_list(self):
        result = _vector_decoder("[1.0,2.0,3.0]")
        assert result == [1.0, 2.0, 3.0]

    def test_string_with_spaces(self):
        result = _vector_decoder("[ 1.0, 2.0, 3.0 ]")
        assert result == [1.0, 2.0, 3.0]

    def test_single_element(self):
        result = _vector_decoder("[42.0]")
        assert result == [42.0]

    def test_negative_values(self):
        result = _vector_decoder("[-1.5,0.0,2.5]")
        assert result == [-1.5, 0.0, 2.5]

    def test_roundtrip(self):
        original = [0.1, 0.2, 0.3, 0.4, 0.5]
        encoded = _vector_encoder(original)
        decoded = _vector_decoder(encoded)
        assert len(decoded) == len(original)
        for a, b in zip(decoded, original):
            assert abs(a - b) < 1e-10


class TestGetPool:
    """Тесты get_pool()."""

    def test_raises_when_pool_is_none(self):
        with patch("app.core.database._pool", None):
            with pytest.raises(RuntimeError, match="Database pool is not initialized"):
                get_pool()


class TestInitDbPool:
    """Тесты init_db_pool()."""

    @pytest.mark.asyncio
    async def test_creates_pool(self):
        mock_pool = AsyncMock()
        mock_pool.is_closing = MagicMock(return_value=False)
        with (
            patch("app.core.database._pool", None),
            patch("app.core.database.get_settings") as mock_settings,
            patch("app.core.database.asyncpg") as mock_asyncpg,
        ):
            mock_settings.return_value.database_url = "postgresql://test"
            mock_settings.return_value.postgres_pool_min = 2
            mock_settings.return_value.postgres_pool_max = 10
            mock_asyncpg.create_pool = AsyncMock(return_value=mock_pool)

            pool = await init_db_pool()

            assert pool == mock_pool
            mock_asyncpg.create_pool.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_existing_pool(self):
        """Если пул уже существует и не закрывается — возвращается существующий."""
        mock_pool = MagicMock()
        mock_pool.is_closing = MagicMock(return_value=False)

        with patch("app.core.database._pool", mock_pool):
            pool = await init_db_pool()
            assert pool == mock_pool

    @pytest.mark.asyncio
    async def test_error_handling(self):
        with (
            patch("app.core.database._pool", None),
            patch("app.core.database.get_settings") as mock_settings,
            patch("app.core.database.asyncpg") as mock_asyncpg,
        ):
            mock_settings.return_value.database_url = "postgresql://test"
            mock_settings.return_value.postgres_pool_min = 2
            mock_settings.return_value.postgres_pool_max = 10
            mock_asyncpg.create_pool = AsyncMock(side_effect=Exception("Connection refused"))

            with pytest.raises(Exception, match="Connection refused"):
                await init_db_pool()


class TestCheckDbHealth:
    """Тесты check_db_health()."""

    @pytest.mark.asyncio
    async def test_ok_status(self):
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=1)
        mock_conn.fetch = AsyncMock(
            return_value=[
                {"schema_name": "registry"},
                {"schema_name": "rag"},
            ]
        )

        mock_pool = MagicMock()
        # pool.acquire() используется как async context manager
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=mock_conn)
        cm.__aexit__ = AsyncMock(return_value=False)
        mock_pool.acquire = MagicMock(return_value=cm)

        with patch("app.core.database._pool", mock_pool):
            result = await check_db_health()

        assert result["status"] == "ok"
        assert "DB connection OK" in result["detail"]

    @pytest.mark.asyncio
    async def test_degraded_missing_schemas(self):
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=1)
        mock_conn.fetch = AsyncMock(return_value=[])

        mock_pool = MagicMock()
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=mock_conn)
        cm.__aexit__ = AsyncMock(return_value=False)
        mock_pool.acquire = MagicMock(return_value=cm)

        with patch("app.core.database._pool", mock_pool):
            result = await check_db_health()

        assert result["status"] == "degraded"
        assert "Missing schemas" in result["detail"]

    @pytest.mark.asyncio
    async def test_error_status(self):
        mock_pool = MagicMock()
        mock_pool.acquire = MagicMock(side_effect=Exception("Connection refused"))

        with patch("app.core.database._pool", mock_pool):
            result = await check_db_health()

        assert result["status"] == "error"
        assert "Connection refused" in result["detail"]
