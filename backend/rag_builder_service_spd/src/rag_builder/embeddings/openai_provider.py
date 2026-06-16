# src/rag_builder/embeddings/openai_provider.py

from openai import OpenAI

from rag_builder.core.config import settings
from rag_builder.models.domain import EmbeddingResult


class OpenAIEmbeddingProvider:
    """
    Провайдер эмбеддингов через OpenAI API.
    """

    def __init__(self) -> None:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required for OpenAI embeddings")

        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def create_embedding(self, text: str) -> list[float]:
        return self.create_embedding_with_usage(text).embedding

    def create_embedding_with_usage(self, text: str) -> EmbeddingResult:
        response = self.client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=text,
        )

        usage = response.usage
        token_count = usage.total_tokens if usage else 0

        cost_usd = (
            token_count / 1_000_000
        ) * settings.EMBEDDING_PRICE_PER_1M_TOKENS_USD

        return EmbeddingResult(
            embedding=response.data[0].embedding,
            token_count=token_count,
            cost_usd=cost_usd,
        )

    def create_embeddings_with_usage(
            self,
            texts: list[str],
    ) -> list[EmbeddingResult]:
        response = self.client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=texts,
        )

        usage = response.usage
        token_count = usage.total_tokens if usage else 0

        total_cost = (
                             token_count / 1_000_000
                     ) * settings.EMBEDDING_PRICE_PER_1M_TOKENS_USD

        cost_per_embedding = (
            total_cost / len(response.data)
            if response.data
            else 0.0
        )

        return [
            EmbeddingResult(
                embedding=item.embedding,
                token_count=0,
                cost_usd=cost_per_embedding,
            )
            for item in response.data
        ]