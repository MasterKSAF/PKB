"""OpenAI-compatible провайдер эмбеддингов через библиотеку openai."""

from __future__ import annotations

from openai import AsyncOpenAI

from app.config import get_settings
from app.core.embeddings.base import EmbeddingError, EmbeddingProvider


class OpenAICompatibleProvider(EmbeddingProvider):
    """
    Провайдер эмбеддингов через OpenAI-compatible API (Infinity, vLLM, etc.).

    Использует официальную библиотеку openai для совместимости и retry-логики.
    Поддерживает инструкции (instruction) для моделей Qwen3-Embedding.
    """

    def __init__(self, instruction: str | None = None):
        self.settings = get_settings()
        self._instruction = instruction if instruction is not None else self.settings.embedding_instruction
        self._client = AsyncOpenAI(
            base_url=self.settings.embedding_base_url,
            api_key=self.settings.embedding_api_key or "not-needed",
            timeout=self.settings.embedding_timeout,
            max_retries=2,
        )
        self._dimension = self.settings.embedding_dim
        self._model = self.settings.embedding_model

    async def encode(self, text: str) -> list[float]:
        """
        Получить эмбеддинг через OpenAI-compatible API.

        Если задана instruction, она добавляется перед текстом в формате
        Qwen3-Embedding: ``{instruction}\n\n{text}``.

        Raises:
            EmbeddingError: При ошибке API
        """
        if not text.strip():
            raise EmbeddingError("Empty text provided for embedding")

        input_text = f"{self._instruction}\n\n{text}" if self._instruction else text

        try:
            response = await self._client.embeddings.create(
                input=[input_text],
                model=self._model,
            )

            embedding = response.data[0].embedding

            if len(embedding) != self._dimension:
                raise EmbeddingError(
                    f"Dimension mismatch: expected {self._dimension}, got {len(embedding)}"
                )

            return list(embedding)

        except EmbeddingError:
            raise
        except Exception as e:
            raise EmbeddingError(f"Embedding API error: {e}") from e

    def get_dimension(self) -> int:
        return self._dimension

    def get_model_name(self) -> str:
        return f"openai-compatible:{self._model}"

    async def close(self) -> None:
        await self._client.close()
