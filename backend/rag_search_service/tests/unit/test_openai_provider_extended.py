"""Unit-тесты для OpenAI-compatible провайдера эмбеддингов: edge cases."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.embeddings.base import EmbeddingError
from app.core.embeddings.openai_provider import OpenAICompatibleProvider


def _make_provider(**overrides):
    """Создать провайдер с замоканными настройками."""
    defaults = dict(
        embedding_api_key="test-key",
        embedding_base_url="https://api.test.com",
        embedding_model="test-model",
        embedding_dim=768,
        embedding_timeout=30,
        embedding_instruction="",
    )
    defaults.update(overrides)

    with patch("app.core.embeddings.openai_provider.get_settings") as mock_settings:
        for k, v in defaults.items():
            setattr(mock_settings.return_value, k, v)
        return OpenAICompatibleProvider()


class TestOpenAIProviderEdgeCases:
    """Расширенные тесты edge cases провайдера эмбеддингов."""

    @pytest.mark.asyncio
    async def test_api_timeout_raises_embedding_error(self):
        """Таймаут API → EmbeddingError."""
        provider = _make_provider()
        provider._client.embeddings = AsyncMock()
        provider._client.embeddings.create = AsyncMock(side_effect=Exception("Request timeout"))

        with pytest.raises(EmbeddingError, match="Embedding API error"):
            await provider.encode("test query")

    @pytest.mark.asyncio
    async def test_empty_response_data_raises_error(self):
        """API вернул пустой data[] → IndexError → EmbeddingError."""
        provider = _make_provider()
        mock_response = MagicMock()
        mock_response.data = []  # Пустой список

        provider._client.embeddings = AsyncMock()
        provider._client.embeddings.create = AsyncMock(return_value=mock_response)

        with pytest.raises(EmbeddingError, match="Embedding API error"):
            await provider.encode("test query")

    @pytest.mark.asyncio
    async def test_whitespace_only_text_rejected(self):
        """Текст из пробелов → EmbeddingError."""
        provider = _make_provider()

        with pytest.raises(EmbeddingError, match="Empty text"):
            await provider.encode("   ")

    @pytest.mark.asyncio
    async def test_tab_only_text_rejected(self):
        """Текст из табов → EmbeddingError."""
        provider = _make_provider()

        with pytest.raises(EmbeddingError, match="Empty text"):
            await provider.encode("\t\t\t")

    @pytest.mark.asyncio
    async def test_very_long_text_succeeds(self):
        """Очень длинный текст — должен успешно обработаться."""
        provider = _make_provider(embedding_dim=768)

        mock_data = MagicMock()
        mock_data.embedding = [0.1] * 768
        mock_response = MagicMock()
        mock_response.data = [mock_data]

        provider._client.embeddings = AsyncMock()
        provider._client.embeddings.create = AsyncMock(return_value=mock_response)

        long_text = "слово " * 10000
        result = await provider.encode(long_text)

        assert len(result) == 768

    def test_get_dimension(self):
        """get_dimension возвращает правильную размерность."""
        provider = _make_provider(embedding_dim=1024)
        assert provider.get_dimension() == 1024

    def test_get_model_name_format(self):
        """get_model_name возвращает строку с префиксом."""
        provider = _make_provider(embedding_model="Qwen/Qwen3-Embedding-0.6B")
        name = provider.get_model_name()
        assert "openai-compatible:" in name
        assert "Qwen/Qwen3-Embedding-0.6B" in name

    @pytest.mark.asyncio
    async def test_close_calls_client_close(self):
        """close() вызывает закрытие клиента."""
        provider = _make_provider()
        provider._client.close = AsyncMock()

        await provider.close()

        provider._client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_generic_exception_wrapped_as_embedding_error(self):
        """Любая ошибка API оборачивается в EmbeddingError."""
        provider = _make_provider()

        provider._client.embeddings = AsyncMock()
        provider._client.embeddings.create = AsyncMock(
            side_effect=RuntimeError("Something unexpected")
        )

        with pytest.raises(EmbeddingError, match="Embedding API error"):
            await provider.encode("test")

    @pytest.mark.asyncio
    async def test_embedding_error_reraised(self):
        """EmbeddingError не оборачивается повторно."""
        provider = _make_provider()

        provider._client.embeddings = AsyncMock()
        provider._client.embeddings.create = AsyncMock(side_effect=EmbeddingError("Original error"))

        with pytest.raises(EmbeddingError, match="Original error"):
            await provider.encode("test")
