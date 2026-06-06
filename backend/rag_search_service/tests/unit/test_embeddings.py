"""Unit-тесты для модуля эмбеддингов."""

import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.embeddings.base import EmbeddingError
from app.core.embeddings.factory import get_embedding_provider
from app.core.embeddings.hf_provider import HuggingFaceLocalProvider
from app.core.embeddings.openai_provider import OpenAICompatibleProvider


class TestEmbeddingFactory:
    """Тесты фабрики провайдеров эмбеддингов."""

    def setup_method(self):
        """Очищаем кэш фабрики перед каждым тестом."""
        from app.core.embeddings.factory import get_embedding_provider
        get_embedding_provider.cache_clear()

    def teardown_method(self):
        """Очищаем кэш фабрики после каждого теста."""
        from app.core.embeddings.factory import get_embedding_provider
        get_embedding_provider.cache_clear()

    def test_factory_returns_hf_provider_when_no_api_key(self):
        """Если API-ключ пустой — возвращается HuggingFace провайдер."""
        with patch("app.core.embeddings.factory.get_settings") as mock_settings:
            mock_settings.return_value.use_local_embedding = True
            mock_settings.return_value.embedding_model = "intfloat/multilingual-e5-large"
            mock_settings.return_value.embedding_dim = 768

            provider = get_embedding_provider()
            assert isinstance(provider, HuggingFaceLocalProvider)

    def test_factory_returns_openai_provider_when_api_key_set(self):
        """Если API-ключ задан — возвращается OpenAI провайдер."""
        with patch("app.core.embeddings.factory.get_settings") as mock_settings:
            mock_settings.return_value.use_local_embedding = False
            mock_settings.return_value.embedding_api_key = "test-key"
            mock_settings.return_value.embedding_base_url = "https://api.openai.com/v1"
            mock_settings.return_value.embedding_model = "text-embedding-3-small"
            mock_settings.return_value.embedding_dim = 768
            mock_settings.return_value.embedding_timeout = 30

            provider = get_embedding_provider()
            assert isinstance(provider, OpenAICompatibleProvider)


class TestOpenAIProvider:
    """Тесты OpenAI-compatible провайдера."""

    @pytest.mark.asyncio
    async def test_encode_success(self):
        """Успешная генерация эмбеддинга через API."""
        with patch("app.core.embeddings.openai_provider.get_settings") as mock_settings:
            mock_settings.return_value.embedding_api_key = "test-key"
            mock_settings.return_value.embedding_base_url = "https://api.test.com"
            mock_settings.return_value.embedding_model = "test-model"
            mock_settings.return_value.embedding_dim = 768
            mock_settings.return_value.embedding_timeout = 30

            provider = OpenAICompatibleProvider()

            # Мокаем HTTP-клиент
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "data": [{"embedding": [0.1] * 768}]
            }
            mock_response.raise_for_status = MagicMock()

            with patch.object(provider._client, "post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = mock_response

                result = await provider.encode("test query")

                assert isinstance(result, list)
                assert len(result) == 768
                assert all(isinstance(v, float) for v in result)

    @pytest.mark.asyncio
    async def test_encode_empty_text_raises_error(self):
        """Пустой текст вызывает EmbeddingError."""
        with patch("app.core.embeddings.openai_provider.get_settings") as mock_settings:
            mock_settings.return_value.embedding_api_key = "test-key"
            mock_settings.return_value.embedding_base_url = "https://api.test.com"
            mock_settings.return_value.embedding_model = "test-model"
            mock_settings.return_value.embedding_dim = 768
            mock_settings.return_value.embedding_timeout = 30

            provider = OpenAICompatibleProvider()

            with pytest.raises(EmbeddingError, match="Empty text"):
                await provider.encode("")

    @pytest.mark.asyncio
    async def test_encode_dimension_mismatch_raises_error(self):
        """Несоответствие размерности вызывает EmbeddingError."""
        with patch("app.core.embeddings.openai_provider.get_settings") as mock_settings:
            mock_settings.return_value.embedding_api_key = "test-key"
            mock_settings.return_value.embedding_base_url = "https://api.test.com"
            mock_settings.return_value.embedding_model = "test-model"
            mock_settings.return_value.embedding_dim = 768
            mock_settings.return_value.embedding_timeout = 30

            provider = OpenAICompatibleProvider()

            # Возвращаем вектор неправильной размерности
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "data": [{"embedding": [0.1] * 384}]  # 384 вместо 768
            }
            mock_response.raise_for_status = MagicMock()

            with patch.object(provider._client, "post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = mock_response

                with pytest.raises(EmbeddingError, match="Dimension mismatch"):
                    await provider.encode("test query")


class TestHuggingFaceProvider:
    """Тесты HuggingFace локального провайдера."""

    @pytest.mark.asyncio
    async def test_encode_empty_text_raises_error(self):
        """Пустой текст вызывает EmbeddingError."""
        with patch("app.core.embeddings.hf_provider.get_settings") as mock_settings:
            mock_settings.return_value.embedding_model = "intfloat/multilingual-e5-large"
            mock_settings.return_value.embedding_dim = 1024

            provider = HuggingFaceLocalProvider()

            with pytest.raises(EmbeddingError, match="Empty text"):
                await provider.encode("")

    @pytest.mark.asyncio
    async def test_encode_success_with_mock_model(self):
        """Успешная генерация эмбеддинга через мокированную модель."""
        with patch("app.core.embeddings.hf_provider.get_settings") as mock_settings:
            mock_settings.return_value.embedding_model = "test-model"
            mock_settings.return_value.embedding_dim = 1024

            provider = HuggingFaceLocalProvider()

            # Мокаем модель
            mock_model = MagicMock()
            mock_model.encode.return_value = np.array([0.1] * 1024)
            provider._model = mock_model

            result = await provider.encode("test query")

            assert isinstance(result, list)
            assert len(result) == 1024
            mock_model.encode.assert_called_once_with("test query")

    def test_get_dimension(self):
        """Метод get_dimension возвращает правильную размерность."""
        with patch("app.core.embeddings.hf_provider.get_settings") as mock_settings:
            mock_settings.return_value.embedding_model = "test-model"
            mock_settings.return_value.embedding_dim = 1024

            provider = HuggingFaceLocalProvider()
            assert provider.get_dimension() == 1024

    def test_get_model_name(self):
        """Метод get_model_name возвращает правильное имя."""
        with patch("app.core.embeddings.hf_provider.get_settings") as mock_settings:
            mock_settings.return_value.embedding_model = "intfloat/multilingual-e5-large"
            mock_settings.return_value.embedding_dim = 1024

            provider = HuggingFaceLocalProvider()
            assert provider.get_model_name() == "huggingface:intfloat/multilingual-e5-large"