# src/rag_builder/embeddings/factory.py

from rag_builder.core.config import settings
from rag_builder.embeddings.stub import StubEmbeddingProvider


def build_embedding_provider():

    if settings.EMBEDDING_PROVIDER == "stub":
        return StubEmbeddingProvider()

    if settings.EMBEDDING_PROVIDER == "openai":

        from rag_builder.embeddings.openai_provider import (
            OpenAIEmbeddingProvider,
        )

        return OpenAIEmbeddingProvider()

    raise ValueError(
        f"Unsupported EMBEDDING_PROVIDER: "
        f"{settings.EMBEDDING_PROVIDER}"
    )

