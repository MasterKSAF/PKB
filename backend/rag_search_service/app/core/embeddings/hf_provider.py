"""HuggingFace локальный провайдер эмбеддингов."""

from __future__ import annotations

import asyncio

from app.config import get_settings
from app.core.embeddings.base import EmbeddingError, EmbeddingProvider
from app.core.logging import get_logger

logger = get_logger("embeddings.huggingface")


class HuggingFaceLocalProvider(EmbeddingProvider):
    """
    Локальный провайдер эмбеддингов через sentence-transformers.

    Используется как fallback, когда EMBEDDING_API_KEY не задан.
    Модель загружается в память при первом вызове (lazy loading).
    """

    def __init__(self):
        self.settings = get_settings()
        self._model = None
        self._dimension = self.settings.embedding_dim
        self._model_name = self.settings.embedding_model
        logger.info(
            "HuggingFace local provider initialized: model=%s (lazy loading)",
            self._model_name,
        )

    def _load_model(self):
        """Загрузить модель sentence-transformers (ленивая загрузка)."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                logger.info("Loading sentence-transformers model: %s", self._model_name)
                self._model = SentenceTransformer(self._model_name)
                logger.info("Model loaded successfully, dimension=%d", self._model.get_sentence_embedding_dimension())
            except Exception as e:
                logger.exception("Failed to load HuggingFace model: %s", e)
                raise EmbeddingError(f"Failed to load model: {e}") from e

    async def encode(self, text: str) -> list[float]:
        """
        Получить эмбеддинг через локальную HuggingFace модель.

        Args:
            text: Текст для кодирования

        Returns:
            Вектор размерности EMBEDDING_DIM

        Raises:
            EmbeddingError: При ошибке инференса
        """
        if not text.strip():
            raise EmbeddingError("Empty text provided for embedding")

        try:
            # Ленивая загрузка модели
            self._load_model()

            # sentence-transformers работает синхронно, запускаем в отдельном потоке
            embedding = await asyncio.to_thread(self._model.encode, text)

            # Преобразуем результат в list (поддержка numpy array и обычных списков)
            import numpy as np
            if isinstance(embedding, np.ndarray):
                embedding_list = embedding.tolist()
            elif isinstance(embedding, list):
                embedding_list = embedding
            else:
                embedding_list = list(embedding)

            # Проверяем размерность
            if len(embedding_list) != self._dimension:
                raise EmbeddingError(
                    f"Dimension mismatch: expected {self._dimension}, got {len(embedding_list)}"
                )

            logger.debug("Generated embedding via HuggingFace, dim=%d", len(embedding_list))
            return embedding_list

        except Exception as e:
            logger.exception("Error in HuggingFace provider: %s", e)
            raise EmbeddingError(f"Embedding generation failed: {e}") from e

    def get_dimension(self) -> int:
        return self._dimension

    def get_model_name(self) -> str:
        return f"huggingface:{self._model_name}"

    def close(self) -> None:
        """Очистить ресурсы (если нужно)."""
        if self._model is not None:
            del self._model
            self._model = None
            logger.info("HuggingFace model unloaded")