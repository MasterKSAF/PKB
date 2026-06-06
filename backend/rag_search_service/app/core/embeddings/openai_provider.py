"""OpenAI-compatible провайдер эмбеддингов."""

from __future__ import annotations

import httpx

from app.config import get_settings
from app.core.embeddings.base import EmbeddingError, EmbeddingProvider
from app.core.logging import get_logger

logger = get_logger("embeddings.openai")


class OpenAICompatibleProvider(EmbeddingProvider):
    """
    Провайдер эмбеддингов через OpenAI-compatible API.

    Поддерживает:
    - OpenAI API (api.openai.com)
    - Локальные LLM-серверы (Ollama, vLLM, LocalAI)
    - Облачные провайдеры (Anthropic, Cohere через прокси)
    """

    def __init__(self):
        self.settings = get_settings()
        self._client = httpx.AsyncClient(
            base_url=self.settings.embedding_base_url,
            headers={
                "Authorization": f"Bearer {self.settings.embedding_api_key}",
                "Content-Type": "application/json",
            },
            timeout=self.settings.embedding_timeout,
        )
        self._dimension = self.settings.embedding_dim
        self._model = self.settings.embedding_model
        logger.info(
            "OpenAI-compatible provider initialized: base_url=%s, model=%s",
            self.settings.embedding_base_url,
            self._model,
        )

    async def encode(self, text: str) -> list[float]:
        """
        Получить эмбеддинг через OpenAI-compatible API.

        Args:
            text: Текст для кодирования

        Returns:
            Вектор размерности EMBEDDING_DIM

        Raises:
            EmbeddingError: При ошибке API
        """
        if not text.strip():
            raise EmbeddingError("Empty text provided for embedding")

        try:
            # Формируем запрос в формате OpenAI Embeddings API
            payload = {
                "input": text,
                "model": self._model,
            }

            response = await self._client.post("/embeddings", json=payload)
            response.raise_for_status()

            data = response.json()

            # Проверяем структуру ответа
            if "data" not in data or not data["data"]:
                raise EmbeddingError("Invalid response structure: missing 'data' field")

            embedding = data["data"][0].get("embedding")
            if embedding is None:
                raise EmbeddingError("Invalid response structure: missing 'embedding' field")

            # Проверяем размерность
            if len(embedding) != self._dimension:
                raise EmbeddingError(
                    f"Dimension mismatch: expected {self._dimension}, got {len(embedding)}"
                )

            logger.debug("Generated embedding via OpenAI API, dim=%d", len(embedding))
            return embedding

        except httpx.TimeoutException as e:
            logger.error("OpenAI API timeout: %s", e)
            raise EmbeddingError(f"API timeout: {e}") from e
        except httpx.HTTPStatusError as e:
            logger.error("OpenAI API error: %s (status=%d)", e, e.response.status_code)
            raise EmbeddingError(
                f"API error (status={e.response.status_code}): {e.response.text}"
            ) from e
        except Exception as e:
            logger.exception("Unexpected error in OpenAI provider: %s", e)
            raise EmbeddingError(f"Unexpected error: {e}") from e

    def get_dimension(self) -> int:
        return self._dimension

    def get_model_name(self) -> str:
        return f"openai-compatible:{self._model}"

    async def close(self) -> None:
        """Закрыть HTTP-клиент."""
        await self._client.aclose()
        logger.info("OpenAI provider closed")