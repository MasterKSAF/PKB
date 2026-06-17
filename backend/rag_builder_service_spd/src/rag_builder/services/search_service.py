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

            results = self._rrf_fuse_results(
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

        context_expanded = False

        if request.expand_context:
            results = self._expand_context_for_results(results)
            context_expanded = True

        processing_time_ms = int((perf_counter() - started_at) * 1000)

        return SearchResponse(
            query=request.query,
            search_type_used=request.search_type,
            results=results,
            total_found=len(results),
            processing_time_ms=processing_time_ms,
            embedding_tokens=embedding_tokens,
            embedding_cost_usd=embedding_cost_usd,
            context_expanded=context_expanded,
        )

    def _rrf_fuse_results(
            self,
            sparse_results,
            dense_results,
            top_k: int,
            rrf_k: int = 60,
    ):
        by_chunk_id = {}

        for rank, result in enumerate(sparse_results, start=1):
            item = by_chunk_id.setdefault(
                result.chunk_id,
                {
                    "result": result,
                    "score": 0.0,
                },
            )
            item["score"] += 1.0 / (rrf_k + rank)

        for rank, result in enumerate(dense_results, start=1):
            item = by_chunk_id.setdefault(
                result.chunk_id,
                {
                    "result": result,
                    "score": 0.0,
                },
            )
            item["score"] += 1.0 / (rrf_k + rank)

        fused_items = sorted(
            by_chunk_id.values(),
            key=lambda item: item["score"],
            reverse=True,
        )

        return [
            item["result"].model_copy(
                update={
                    "score": item["score"],
                }
            )
            for item in fused_items[:top_k]
        ]

    def _expand_context_for_results(self, results):
        expanded_results = []

        result_section_ids = {
            result.document_section_id
            for result in results
        }

        for result in results:
            context = self.repository.expand_context(
                document_section_id=result.document_section_id,
            )

            filtered_context = [
                item
                for item in context
                if item.document_section_id not in result_section_ids
            ]

            expanded_results.append(
                result.model_copy(
                    update={
                        "context": filtered_context,
                    }
                )
            )

        return expanded_results
