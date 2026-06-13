"""Unit-тесты для модуля эмбеддингов."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.embeddings.base import EmbeddingError
from app.core.embeddings.factory import get_embedding_provider
from app.core.embeddings.openai_provider import OpenAICompatibleProvider


class TestEmbeddingFactory:
    """Тесты фабрики провайдеров эмбеддингов."""

    def setup_method(self):
        get_embedding_provider.cache_clear()

    def teardown_method(self):
        get_embedding_provider.cache_clear()

    def test_factory_always_returns_openai_provider(self):
        provider = get_embedding_provider()
        assert isinstance(provider, OpenAICompatibleProvider)


class TestOpenAIProvider:
    """Тесты OpenAI-compatible провайдера."""

    @pytest.mark.asyncio
    async def test_encode_success(self):
        with patch("app.core.embeddings.openai_provider.get_settings") as mock_settings:
            mock_settings.return_value.embedding_api_key = "test-key"
            mock_settings.return_value.embedding_base_url = "https://api.test.com"
            mock_settings.return_value.embedding_model = "test-model"
            mock_settings.return_value.embedding_dim = 768
            mock_settings.return_value.embedding_timeout = 30
            mock_settings.return_value.embedding_instruction = ""

            provider = OpenAICompatibleProvider()

            mock_data = MagicMock()
            mock_data.embedding = [0.1] * 768
            mock_response = MagicMock()
            mock_response.data = [mock_data]

            provider._client.embeddings = AsyncMock()
            provider._client.embeddings.create = AsyncMock(return_value=mock_response)

            result = await provider.encode("test query")

            assert isinstance(result, list)
            assert len(result) == 768
            assert all(isinstance(v, float) for v in result)

    @pytest.mark.asyncio
    async def test_encode_empty_text_raises_error(self):
        with patch("app.core.embeddings.openai_provider.get_settings") as mock_settings:
            mock_settings.return_value.embedding_api_key = "test-key"
            mock_settings.return_value.embedding_base_url = "https://api.test.com"
            mock_settings.return_value.embedding_model = "test-model"
            mock_settings.return_value.embedding_dim = 768
            mock_settings.return_value.embedding_timeout = 30
            mock_settings.return_value.embedding_instruction = ""

            provider = OpenAICompatibleProvider()

            with pytest.raises(EmbeddingError, match="Empty text"):
                await provider.encode("")

    @pytest.mark.asyncio
    async def test_encode_dimension_mismatch_raises_error(self):
        with patch("app.core.embeddings.openai_provider.get_settings") as mock_settings:
            mock_settings.return_value.embedding_api_key = "test-key"
            mock_settings.return_value.embedding_base_url = "https://api.test.com"
            mock_settings.return_value.embedding_model = "test-model"
            mock_settings.return_value.embedding_dim = 768
            mock_settings.return_value.embedding_timeout = 30
            mock_settings.return_value.embedding_instruction = ""

            provider = OpenAICompatibleProvider()

            mock_data = MagicMock()
            mock_data.embedding = [0.1] * 384
            mock_response = MagicMock()
            mock_response.data = [mock_data]

            provider._client.embeddings = AsyncMock()
            provider._client.embeddings.create = AsyncMock(return_value=mock_response)

            with pytest.raises(EmbeddingError, match="Dimension mismatch"):
                await provider.encode("test query")

    @pytest.mark.asyncio
    async def test_encode_with_instruction(self):
        with patch("app.core.embeddings.openai_provider.get_settings") as mock_settings:
            mock_settings.return_value.embedding_api_key = ""
            mock_settings.return_value.embedding_base_url = "http://localhost:7997"
            mock_settings.return_value.embedding_model = "Qwen/Qwen3-Embedding-0.6B"
            mock_settings.return_value.embedding_dim = 1024
            mock_settings.return_value.embedding_timeout = 30
            mock_settings.return_value.embedding_instruction = "Instruct: Test instruction"

            provider = OpenAICompatibleProvider()

            mock_data = MagicMock()
            mock_data.embedding = [0.1] * 1024
            mock_response = MagicMock()
            mock_response.data = [mock_data]

            provider._client.embeddings = AsyncMock()
            provider._client.embeddings.create = AsyncMock(return_value=mock_response)

            await provider.encode("test query")

            call_args = provider._client.embeddings.create.call_args
            input_text = call_args[1]["input"][0]
            assert input_text.startswith("Instruct: Test instruction\n\n")

    @pytest.mark.asyncio
    async def test_encode_without_instruction(self):
        with patch("app.core.embeddings.openai_provider.get_settings") as mock_settings:
            mock_settings.return_value.embedding_api_key = ""
            mock_settings.return_value.embedding_base_url = "http://localhost:7997"
            mock_settings.return_value.embedding_model = "Qwen/Qwen3-Embedding-0.6B"
            mock_settings.return_value.embedding_dim = 1024
            mock_settings.return_value.embedding_timeout = 30
            mock_settings.return_value.embedding_instruction = ""

            provider = OpenAICompatibleProvider()

            mock_data = MagicMock()
            mock_data.embedding = [0.1] * 1024
            mock_response = MagicMock()
            mock_response.data = [mock_data]

            provider._client.embeddings = AsyncMock()
            provider._client.embeddings.create = AsyncMock(return_value=mock_response)

            await provider.encode("test query")

            call_args = provider._client.embeddings.create.call_args
            input_text = call_args[1]["input"][0]
            assert input_text == "test query"
