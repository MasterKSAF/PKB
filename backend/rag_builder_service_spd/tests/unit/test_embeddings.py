# tests/unit/test_embeddings.py

from rag_builder.services.embedding_service import EmbeddingService


def test_embedding_stub():
    service = EmbeddingService()

    embedding = service.create_embedding("ГОСТ 20868-81")

    assert embedding == [0.0, 0.0, 0.0]