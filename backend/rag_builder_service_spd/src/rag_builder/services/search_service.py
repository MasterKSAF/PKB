# rag_builder_service_spd/src/rag_builder/services/search_service.py

from time import perf_counter

from rag_builder.embeddings.factory import build_embedding_provider
from rag_builder.models.search import SearchRequest, SearchResponse
from rag_builder.repositories.postgres_search_repository import (
    PostgresSearchRepository,
)


class SearchService:
    """
    Service layer for RAG Search.

    Orchestrates query embedding and read-only chunk retrieval.
    """

    def __init__(
        self,
        repository: PostgresSearchRepository | None = None,
        embedding_provider=None,
    ) -> None:
        self.repository = repository or PostgresSearchRepository()
        self.embedding_provider = embedding_provider or build_embedding_provider()

    def search(self, request: SearchRequest) -> SearchResponse:
        started_at = perf_counter()

        if request.expand_context:
            raise ValueError(
                "Context expansion is not supported in RAG Search MVP"
            )

        if request.search_type == "dense":
            embedding_result = self.embedding_provider.create_embedding_with_usage(
                request.query,
            )

            results = self.repository.vector_search(
                query_embedding=embedding_result.embedding,
                top_k=request.top_k,
                filters=request.filters,
            )

            embedding_tokens = embedding_result.token_count
            embedding_cost_usd = embedding_result.cost_usd

        elif request.search_type == "sparse":
            results = self.repository.text_search(
                query_text=request.query,
                top_k=request.top_k,
                filters=request.filters,
            )

            embedding_tokens = 0
            embedding_cost_usd = 0.0

        elif request.search_type == "hybrid":
            sparse_results = self.repository.text_search(
                query_text=request.query,
                top_k=request.top_k,
                filters=request.filters,
            )

            embedding_result = self.embedding_provider.create_embedding_with_usage(
                request.query,
            )

            dense_results = self.repository.vector_search(
                query_embedding=embedding_result.embedding,
                top_k=request.top_k,
                filters=request.filters,
            )

            results = self._merge_results_without_duplicates(
                sparse_results=sparse_results,
                dense_results=dense_results,
                top_k=request.top_k,
            )

            embedding_tokens = embedding_result.token_count
            embedding_cost_usd = embedding_result.cost_usd

        else:
            raise ValueError(
                f"Unsupported search_type: {request.search_type}"
            )

        processing_time_ms = int((perf_counter() - started_at) * 1000)

        return SearchResponse(
            query=request.query,
            search_type_used=request.search_type,
            results=results,
            total_found=len(results),
            processing_time_ms=processing_time_ms,
            embedding_tokens=embedding_tokens,
            embedding_cost_usd=embedding_cost_usd,
            context_expanded=False,
        )

    def _merge_results_without_duplicates(
            self,
            sparse_results,
            dense_results,
            top_k: int,
    ):
        merged = []
        seen_chunk_ids = set()

        for result in sparse_results + dense_results:
            if result.chunk_id in seen_chunk_ids:
                continue

            merged.append(result)
            seen_chunk_ids.add(result.chunk_id)

            if len(merged) >= top_k:
                break

        return merged