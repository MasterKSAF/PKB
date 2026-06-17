# rag_builder_service_spd/tests/unit/test_search_service.py

import pytest

from rag_builder.models.domain import EmbeddingResult
from rag_builder.services.search_service import SearchService
from rag_builder.models.search import (
    SearchChunkResult,
    SearchContextItem,
    SearchRequest,
)


class FakeEmbeddingProvider:
    def __init__(self) -> None:
        self.received_text = None


    def create_embedding_with_usage(self, text: str) -> EmbeddingResult:
        self.received_text = text

        return EmbeddingResult(
            embedding=[0.1, 0.2, 0.3],
            token_count=7,
            cost_usd=0.000001,
        )


class FakeSearchRepository:
    def __init__(self) -> None:
        self.received_embedding = None
        self.received_top_k = None
        self.received_filters = None
        self.received_query_text = None
        self.received_expand_document_section_id = None

    def vector_search(
        self,
        query_embedding,
        top_k,
        filters=None,
    ) -> list[SearchChunkResult]:
        self.received_embedding = query_embedding
        self.received_top_k = top_k
        self.received_filters = filters

        return [
            SearchChunkResult(
                chunk_id=1001,
                document_id=420000,
                document_version_id=420001,
                document_section_id=10,
                section_id=8,
                clause="6.1",
                path="6/6.1",
                page=2,
                bbox=None,
                chunk_index=0,
                chunk_type="text",
                content="Допуск соосности должен соответствовать таблице.",
                score=0.95,
                distance=0.05,
            )
        ]

    def expand_context(
            self,
            document_section_id: int,
    ):
        self.received_expand_document_section_id = document_section_id

        return [
            SearchContextItem(
                relation="parent",
                document_section_id=7,
                section_id=7,
                parent_id=None,
                clause="6",
                title="Допуски формы и расположения поверхностей",
                path="6",
                page=1,
                section_type="text",
                content={
                    "text": "Допуски формы и расположения поверхностей установлены..."
                },
            ),
            SearchContextItem(
                relation="child",
                document_section_id=10,
                section_id=8,
                parent_id=7,
                clause="6.1",
                title="Допуск соосности",
                path="6/6.1",
                page=2,
                section_type="text",
                content={
                    "text": "Дубликат основного результата."
                },
            ),
        ]

    def text_search(
            self,
            query_text,
            top_k,
            filters=None,
    ) -> list[SearchChunkResult]:
        self.received_query_text = query_text
        self.received_top_k = top_k
        self.received_filters = filters

        return [
            SearchChunkResult(
                chunk_id=1001,
                document_id=420000,
                document_version_id=420001,
                document_section_id=10,
                section_id=8,
                clause="6.1",
                path="6/6.1",
                page=2,
                bbox=None,
                chunk_index=0,
                chunk_type="text",
                content="Допуск соосности найден текстовым поиском.",
                score=1.0,
                distance=None,
            ),
            SearchChunkResult(
                chunk_id=1002,
                document_id=420000,
                document_version_id=420001,
                document_section_id=11,
                section_id=9,
                clause="table-1",
                path="6/6.1/table1",
                page=2,
                bbox=None,
                chunk_index=0,
                chunk_type="table",
                content="Таблица допусков соосности.",
                score=1.0,
                distance=None,
            ),
        ]

def test_search_service_runs_dense_search():
    repository = FakeSearchRepository()
    embedding_provider = FakeEmbeddingProvider()

    service = SearchService(
        repository=repository,
        embedding_provider=embedding_provider,
    )

    response = service.search(
        SearchRequest(
            query="допуск соосности",
            top_k=5,
        )
    )

    assert embedding_provider.received_text == "допуск соосности"
    assert repository.received_embedding == [0.1, 0.2, 0.3]
    assert repository.received_top_k == 5

    assert response.query == "допуск соосности"
    assert response.search_type_used == "dense"
    assert response.total_found == 1
    assert response.embedding_tokens == 7
    assert response.embedding_cost_usd == 0.000001
    assert response.results[0].clause == "6.1"
    assert response.context_expanded is False


def test_search_service_runs_sparse_search_without_embedding():
    repository = FakeSearchRepository()
    embedding_provider = FakeEmbeddingProvider()

    service = SearchService(
        repository=repository,
        embedding_provider=embedding_provider,
    )

    response = service.search(
        SearchRequest(
            query="допуск соосности",
            top_k=5,
            search_type="sparse",
        )
    )

    assert embedding_provider.received_text is None
    assert repository.received_query_text == "допуск соосности"
    assert repository.received_top_k == 5

    assert response.query == "допуск соосности"
    assert response.search_type_used == "sparse"
    assert response.total_found == 2
    assert response.embedding_tokens == 0
    assert response.embedding_cost_usd == 0.0
    assert response.results[0].score == 1.0
    assert response.results[0].clause == "6.1"

def test_search_service_expands_context_when_requested():
    repository = FakeSearchRepository()
    embedding_provider = FakeEmbeddingProvider()

    service = SearchService(
        repository=repository,
        embedding_provider=embedding_provider,
    )

    response = service.search(
        SearchRequest(
            query="допуск",
            expand_context=True,
        )
    )

    assert repository.received_expand_document_section_id == 10

    assert response.context_expanded is True
    assert response.results[0].context
    assert response.results[0].context[0].relation == "parent"
    assert response.results[0].context[0].clause == "6"
    assert response.results[0].context[0].path == "6"

    context_section_ids = {
        item.document_section_id
        for item in response.results[0].context
    }

    assert 7 in context_section_ids
    assert 10 not in context_section_ids

def test_search_service_runs_hybrid_search_with_rrf_no_duplicates():
    repository = FakeSearchRepository()
    embedding_provider = FakeEmbeddingProvider()

    service = SearchService(
        repository=repository,
        embedding_provider=embedding_provider,
    )

    response = service.search(
        SearchRequest(
            query="допуск соосности",
            top_k=5,
            search_type="hybrid",
        )
    )

    assert embedding_provider.received_text == "допуск соосности"

    assert repository.received_query_text == "допуск соосности"
    assert repository.received_embedding == [0.1, 0.2, 0.3]
    assert repository.received_top_k == 5

    assert response.query == "допуск соосности"
    assert response.search_type_used == "hybrid"
    assert response.embedding_tokens == 7
    assert response.embedding_cost_usd == 0.000001

    assert response.total_found == 2

    assert response.results[0].chunk_id == 1001
    assert response.results[1].chunk_id == 1002

    expected_duplicate_score = (1.0 / 61) + (1.0 / 61)
    expected_sparse_only_score = 1.0 / 62

    assert response.results[0].score == expected_duplicate_score
    assert response.results[1].score == expected_sparse_only_score

