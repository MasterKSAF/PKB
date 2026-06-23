import asyncio

from rag_search.models.search import (
    SearchChunkResult,
    SearchContextItem,
    SearchRequest,
)
from rag_search.services.embedding_service import EmbeddingResult
from rag_search.services.search_service import SearchService


def run(coro):
    return asyncio.run(coro)


class FakeEmbeddingProvider:
    supports_dense = True

    def create_embedding_with_usage(self, text: str) -> EmbeddingResult:
        return EmbeddingResult(
            embedding=[0.1, 0.2, 0.3],
            token_count=3,
            cost_usd=0.000001,
        )


class FakeRepository:
    def __init__(self):
        self.calls = []

    def text_search(self, query_text, top_k, filters=None):
        self.calls.append(("text", query_text, top_k, filters))
        return [
            SearchChunkResult(
                chunk_id=1,
                document_id=100,
                document_version_id=101,
                document_section_id=10,
                section_id=1,
                chunk_index=0,
                chunk_type="text",
                content="sparse result",
                score=0.9,
                mode="sparse",
            )
        ]

    def vector_search(self, query_embedding, top_k, filters=None):
        self.calls.append(("vector", query_embedding, top_k, filters))
        return [
            SearchChunkResult(
                chunk_id=2,
                document_id=100,
                document_version_id=101,
                document_section_id=20,
                section_id=2,
                chunk_index=1,
                chunk_type="text",
                content="dense result",
                score=0.8,
                distance=0.2,
                mode="dense",
            )
        ]

    def expand_context(self, document_section_id):
        self.calls.append(("context", document_section_id))
        return [
            SearchContextItem(
                relation="parent",
                document_section_id=99,
                section_id=99,
                path="root",
                section_type="text",
                content={"text": "parent context"},
            )
        ]


def test_sparse_search_uses_text_search_only() -> None:
    repository = FakeRepository()
    service = SearchService(repository=repository)

    response = run(
        service.search(
            SearchRequest(
                query="допуск",
                search_type="sparse",
            )
        )
    )

    assert response.search_type_used == "sparse"
    assert response.total_found == 1
    assert response.results[0].mode == "sparse"
    assert [call[0] for call in repository.calls] == ["text"]


def test_dense_search_uses_embedding_and_vector_search() -> None:
    repository = FakeRepository()
    service = SearchService(
        repository=repository,
        embedding_provider=FakeEmbeddingProvider(),
    )

    response = run(
        service.search(
            SearchRequest(
                query="допуск",
                search_type="dense",
            )
        )
    )

    assert response.search_type_used == "dense"
    assert response.total_found == 1
    assert response.embedding_tokens == 3
    assert response.results[0].mode == "dense"
    assert [call[0] for call in repository.calls] == ["vector"]


def test_hybrid_search_uses_rrf() -> None:
    repository = FakeRepository()
    service = SearchService(
        repository=repository,
        embedding_provider=FakeEmbeddingProvider(),
    )

    response = run(
        service.search(
            SearchRequest(
                query="допуск",
                search_type="hybrid",
            )
        )
    )

    assert response.search_type_used == "hybrid"
    assert response.total_found == 2
    assert response.results[0].mode == "hybrid"
    assert [call[0] for call in repository.calls] == ["text", "vector"]


def test_hybrid_degrades_to_sparse_with_stub_embedding_provider() -> None:
    repository = FakeRepository()
    service = SearchService(repository=repository)

    response = run(
        service.search(
            SearchRequest(
                query="допуск",
                search_type="hybrid",
            )
        )
    )

    assert response.search_type_used == "hybrid"
    assert response.total_found == 1
    assert response.results[0].mode == "sparse"
    assert [call[0] for call in repository.calls] == ["text"]


def test_context_expansion_adds_context_items() -> None:
    repository = FakeRepository()
    service = SearchService(repository=repository)

    response = run(
        service.search(
            SearchRequest(
                query="допуск",
                search_type="sparse",
                expand_context=True,
            )
        )
    )

    assert response.context_expanded is True
    assert response.results[0].context
    assert response.results[0].context[0].relation == "parent"
