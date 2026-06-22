# src/rag_builder/embeddings/factory.py

from rag_builder.core.config import settings
from rag_builder.embeddings.stub import StubEmbeddingProvider


def build_embedding_provider():
    provider = settings.EMBEDDING_PROVIDER.lower()

    if provider == "stub":
        return StubEmbeddingProvider()

    if provider == "openai":
        from rag_builder.embeddings.openai_provider import (
            OpenAIEmbeddingProvider,
        )

        return OpenAIEmbeddingProvider()

    if provider in {
        "openai_compatible",
        "infinity",
        "external",
    }:
        from rag_builder.embeddings.openai_provider import (
            OpenAICompatibleEmbeddingProvider,
        )

        return OpenAICompatibleEmbeddingProvider()

    raise ValueError(
        f"Unsupported EMBEDDING_PROVIDER: "
        f"{settings.EMBEDDING_PROVIDER}"
    )