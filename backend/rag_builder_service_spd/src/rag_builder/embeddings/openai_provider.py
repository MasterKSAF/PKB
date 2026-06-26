# src/rag_builder/embeddings/openai_provider.py

from openai import OpenAI

from rag_builder.core.config import settings
from rag_builder.models.domain import EmbeddingResult


class BaseOpenAIEmbeddingProvider:
    """
    Базовый провайдер для OpenAI-compatible Embeddings API.
    """

    def __init__(self, client: OpenAI | None = None) -> None:
        self.client = client or self._build_client()

    def _build_client(self) -> OpenAI:
        raise NotImplementedError

    def create_embedding(self, text: str) -> list[float]:
        return self.create_embedding_with_usage(text).embedding

    def create_embedding_with_usage(self, text: str) -> EmbeddingResult:
        response = self.client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=text,
            dimensions=settings.EMBEDDING_DIM,
        )

        usage = getattr(response, "usage", None)
        token_count = usage.total_tokens if usage else 0

        cost_usd = (
            token_count / 1_000_000
        ) * settings.EMBEDDING_PRICE_PER_1M_TOKENS_USD

        embedding = self._validate_embedding(
            list(response.data[0].embedding)
        )

        return EmbeddingResult(
            embedding=embedding,
            token_count=token_count,
            cost_usd=cost_usd,
        )

    def create_embeddings_with_usage(
            self,
            texts: list[str],
    ) -> list[EmbeddingResult]:
        if not texts:
            return []

        response = self.client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=texts,
            dimensions=settings.EMBEDDING_DIM,
        )

        response_data = list(response.data)

        if len(response_data) != len(texts):
            raise ValueError(
                "Embedding count mismatch: "
                f"got {len(response_data)}, expected {len(texts)}"
            )

        usage = getattr(response, "usage", None)
        token_count = usage.total_tokens if usage else 0

        total_cost = (
            token_count / 1_000_000
        ) * settings.EMBEDDING_PRICE_PER_1M_TOKENS_USD

        cost_per_embedding = (
            total_cost / len(response_data)
            if response_data
            else 0.0
        )

        token_count_per_embedding = (
            token_count // len(response_data)
            if response_data
            else 0
        )

        return [
            EmbeddingResult(
                embedding=self._validate_embedding(list(item.embedding)),
                token_count=token_count_per_embedding,
                cost_usd=cost_per_embedding,
            )
            for item in response_data
        ]

    def _validate_embedding(self, embedding: list[float]) -> list[float]:
        if len(embedding) != settings.EMBEDDING_DIM:
            raise ValueError(
                "Embedding dimension mismatch: "
                f"got {len(embedding)}, expected {settings.EMBEDDING_DIM}"
            )

        return embedding


class OpenAIEmbeddingProvider(BaseOpenAIEmbeddingProvider):
    """
    Провайдер эмбеддингов через официальный OpenAI API.
    """

    def __init__(self, client: OpenAI | None = None) -> None:
        if client is None and not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required for OpenAI embeddings")

        super().__init__(client=client)

    def _build_client(self) -> OpenAI:
        return OpenAI(api_key=settings.OPENAI_API_KEY)


class OpenAICompatibleEmbeddingProvider(BaseOpenAIEmbeddingProvider):
    """
    Провайдер эмбеддингов через OpenAI-compatible API.

    Используется для:
    - Infinity local embeddings service;
    - external Qwen/OpenAI-compatible endpoint.
    """

    def __init__(
            self,
            client: OpenAI | None = None,
            base_url: str | None = None,
            api_key: str | None = None,
    ) -> None:
        self.base_url = base_url or settings.effective_embedding_api_base_url
        self.api_key = (
            api_key
            if api_key is not None
            else settings.EMBEDDING_API_KEY
        )

        if client is None and not self.base_url:
            raise ValueError(
                "EMBEDDING_API_BASE_URL or EMBEDDING_BASE_URL is required for "
                "OpenAI-compatible embeddings"
            )

        super().__init__(client=client)

    def _build_client(self) -> OpenAI:
        return OpenAI(
            api_key=self.api_key or "not-needed",
            base_url=self.base_url,
        )
