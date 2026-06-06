"""Модуль генерации эмбеддингов для поисковых запросов."""

from app.core.embeddings.base import EmbeddingProvider
from app.core.embeddings.factory import get_embedding_provider

__all__ = ["EmbeddingProvider", "get_embedding_provider"]