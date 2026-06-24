from rag_builder.embeddings.service import EmbeddingService


async def test_embeddings_deterministic_and_dimension() -> None:
    svc = EmbeddingService(dim=2048)
    vectors = await svc.embed_many(["abc", "abc"])
    assert len(vectors) == 2
    assert len(vectors[0]) == 2048
    assert vectors[0] == vectors[1]
