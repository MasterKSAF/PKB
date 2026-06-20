# tests/unit/test_embeddings.py

from rag_builder.core.config import settings
from rag_builder.services.embedding_service import EmbeddingService


def test_embedding_stub():
    service = EmbeddingService()

    embedding = service.create_embedding("ГОСТ 20868-81")

    assert len(embedding) == settings.EMBEDDING_DIM
    assert embedding[:3] == [0.0, 0.0, 0.0]
