"""Фабрика для создания провайдера эмбеддингов."""

from __future__ import annotations

from functools import lru_cache

from app.config import get_settings
from app.core.embeddings.base import EmbeddingProvider
from app.core.embeddings.hf_provider import HuggingFaceLocalProvider
from app.core.embeddings.openai_provider import OpenAICompatibleProvider
from app.core.logging import get_logger

logger = get_logger("embeddings.factory")


@lru_cache(maxsize=1)
def get_embedding_provider() -> EmbeddingProvider:
    """
    Получить провайдер эмбеддингов (singleton).

    Логика выбора:
    - Если EMBEDDING_API_KEY задан → OpenAI-compatible provider
    - Если EMBEDDING_API_KEY пустой → HuggingFace local provider

    Returns:
        Экземпляр EmbeddingProvider
    """
    settings = get_settings()

    if settings.use_local_embedding:
        logger.info("Using HuggingFace local provider (no API key configured)")
        return HuggingFaceLocalProvider()
    else:
        logger.info("Using OpenAI-compatible provider (API key configured)")
        return OpenAICompatibleProvider()