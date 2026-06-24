from rag_search.core.config import settings
from rag_search.embeddings.base import EmbeddingProvider
from rag_search.embeddings.openai_provider import OpenAICompatibleEmbeddingProvider
from rag_search.embeddings.stub import StubEmbeddingProvider


def build_embedding_provider(
    provider_name: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
    embedding_dim: int | None = None,
) -> EmbeddingProvider:
    provider = (provider_name or settings.EMBEDDING_PROVIDER).strip().lower()

    if provider == "stub":
        return StubEmbeddingProvider()

    if provider in {
        "openai",
        "openai-compatible",
        "openai_compatible",
        "tei",
        "infinity",
    }:
        return OpenAICompatibleEmbeddingProvider(
            api_key=api_key,
            base_url=base_url,
            model=model,
            embedding_dim=embedding_dim,
        )

    raise ValueError(f"Unsupported EMBEDDING_PROVIDER: {provider}")
