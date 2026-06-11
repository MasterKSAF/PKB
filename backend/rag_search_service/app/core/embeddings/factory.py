"""Фабрика для создания провайдера эмбеддингов."""

from __future__ import annotations

from functools import lru_cache

from app.core.embeddings.base import EmbeddingProvider
from app.core.embeddings.openai_provider import OpenAICompatibleProvider
from app.core.logging import get_logger

logger = get_logger("embeddings.factory")


@lru_cache(maxsize=1)
def get_embedding_provider() -> EmbeddingProvider:
    """
    Получить провайдер эмбеддингов (singleton).

    Всегда использует OpenAI-compatible провайдер (Infinity или другой
    совместимый сервис эмбеддингов). Локальная модель не поддерживается.

    Returns:
        Экземпляр EmbeddingProvider
    """
    logger.info("Creating OpenAI-compatible embedding provider")
    return OpenAICompatibleProvider()