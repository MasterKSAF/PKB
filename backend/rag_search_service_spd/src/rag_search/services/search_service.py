from time import perf_counter

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from rag_search.core.config import settings
from rag_search.core.logger import logger
from rag_search.core.metrics import (
    SEARCH_DURATION_MS,
    SEARCH_EMBEDDING_TOKENS_TOTAL,
    SEARCH_REQUESTS_FAILED_TOTAL,
    SEARCH_REQUESTS_TOTAL,
    SEARCH_RESULTS_COUNT,
)
from rag_search.models.search import SearchRequest, SearchResponse
from rag_search.repositories.postgres_search_repository import (
    PostgresSearchRepository,
)
from rag_search.services.embedding_service import build_embedding_provider


tracer = trace.get_tracer(__name__)


class SearchService:
    """Service layer for RAG Search."""

    def __init__(
        self,
        repository: PostgresSearchRepository | None = None,
        embedding_provider=None,
    ) -> None:
        self.repository = repository or PostgresSearchRepository()
        self.embedding_provider = (
            embedding_provider or build_embedding_provider()
        )

    async def search(self, request: SearchRequest) -> SearchResponse:
        started_at = perf_counter()

        with tracer.start_as_current_span("rag_search.search") as span:
            span.set_attribute("search_type", request.search_type)
            span.set_attribute("top_k", request.top_k)
            span.set_attribute("query_length", len(request.query))
            span.set_attribute("expand_context", request.expand_context)
            span.set_attribute("embedding_provider", settings.EMBEDDING_PROVIDER)
            span.set_attribute("embedding_model", settings.EMBEDDING_MODEL)
            span.set_attribute("embedding_dim", settings.EMBEDDING_DIM)

            span.add_event(
                "query_received",
                {
                    "search_type": request.search_type,
                    "top_k": request.top_k,
                    "query_length": len(request.query),
                    "expand_context": request.expand_context,
                },
            )

            embedding_tokens = 0
            embedding_cost_usd = 0.0

            request_metric_attributes = {
                "search_type": request.search_type,
                "embedding_provider": settings.EMBEDDING_PROVIDER,
                "embedding_model": settings.EMBEDDING_MODEL,
                "embedding_dim": settings.EMBEDDING_DIM,
                "expand_context": request.expand_context,
            }
            SEARCH_REQUESTS_TOTAL.add(1, request_metric_attributes)

            try:
                if request.search_type == "dense":
                    if not self._supports_dense_search():
                        raise ValueError(
                            "Dense search requires a real embedding provider"
                        )

                    with tracer.start_as_current_span(
                        "rag_search.create_query_embedding",
                    ) as embedding_span:
                        embedding_span.set_attribute(
                            "embedding_provider",
                            settings.EMBEDDING_PROVIDER,
                        )
                        embedding_span.set_attribute(
                            "embedding_model",
                            settings.EMBEDDING_MODEL,
                        )
                        embedding_span.set_attribute(
                            "embedding_dim",
                            settings.EMBEDDING_DIM,
                        )

                        embedding_result = (
                            self.embedding_provider.create_embedding_with_usage(
                                request.query,
                            )
                        )

                        embedding_tokens = embedding_result.token_count
                        embedding_cost_usd = embedding_result.cost_usd

                        embedding_span.set_attribute(
                            "embedding_tokens",
                            embedding_tokens,
                        )
                        embedding_span.set_attribute(
                            "embedding_cost_usd",
                            embedding_cost_usd,
                        )

                    with tracer.start_as_current_span(
                        "rag_search.vector_search",
                    ) as vector_span:
                        vector_span.set_attribute("top_k", request.top_k)
                        results = self.repository.vector_search(
                            query_embedding=embedding_result.embedding,
                            top_k=request.top_k,
                            filters=request.filters,
                        )
                        vector_span.set_attribute("results_count", len(results))

                elif request.search_type == "sparse":
                    with tracer.start_as_current_span(
                        "rag_search.text_search",
                    ) as text_span:
                        text_span.set_attribute("top_k", request.top_k)
                        results = self.repository.text_search(
                            query_text=request.query,
                            top_k=request.top_k,
                            filters=request.filters,
                        )
                        text_span.set_attribute("results_count", len(results))

                elif request.search_type == "hybrid":
                    with tracer.start_as_current_span(
                        "rag_search.text_search",
                    ) as text_span:
                        text_span.set_attribute("top_k", request.top_k)
                        sparse_results = self.repository.text_search(
                            query_text=request.query,
                            top_k=request.top_k,
                            filters=request.filters,
                        )
                        text_span.set_attribute(
                            "results_count",
                            len(sparse_results),
                        )

                    if self._supports_dense_search():
                        with tracer.start_as_current_span(
                            "rag_search.create_query_embedding",
                        ) as embedding_span:
                            embedding_span.set_attribute(
                                "embedding_provider",
                                settings.EMBEDDING_PROVIDER,
                            )
                            embedding_span.set_attribute(
                                "embedding_model",
                                settings.EMBEDDING_MODEL,
                            )
                            embedding_span.set_attribute(
                                "embedding_dim",
                                settings.EMBEDDING_DIM,
                            )

                            embedding_result = (
                                self.embedding_provider.create_embedding_with_usage(
                                    request.query,
                                )
                            )

                            embedding_tokens = embedding_result.token_count
                            embedding_cost_usd = embedding_result.cost_usd

                            embedding_span.set_attribute(
                                "embedding_tokens",
                                embedding_tokens,
                            )
                            embedding_span.set_attribute(
                                "embedding_cost_usd",
                                embedding_cost_usd,
                            )

                        with tracer.start_as_current_span(
                            "rag_search.vector_search",
                        ) as vector_span:
                            vector_span.set_attribute("top_k", request.top_k)
                            dense_results = self.repository.vector_search(
                                query_embedding=embedding_result.embedding,
                                top_k=request.top_k,
                                filters=request.filters,
                            )
                            vector_span.set_attribute(
                                "results_count",
                                len(dense_results),
                            )

                        with tracer.start_as_current_span(
                            "rag_search.rrf_fuse_results",
                        ) as fuse_span:
                            fuse_span.set_attribute(
                                "sparse_results_count",
                                len(sparse_results),
                            )
                            fuse_span.set_attribute(
                                "dense_results_count",
                                len(dense_results),
                            )
                            results = self._rrf_fuse_results(
                                sparse_results=sparse_results,
                                dense_results=dense_results,
                                top_k=request.top_k,
                            )
                            fuse_span.set_attribute(
                                "results_count",
                                len(results),
                            )
                    else:
                        span.add_event(
                            "dense_search_skipped",
                            {
                                "reason": "embedding_provider_does_not_support_dense",
                                "embedding_provider": settings.EMBEDDING_PROVIDER,
                            },
                        )
                        results = sparse_results

                else:
                    raise ValueError(
                        f"Unsupported search_type: {request.search_type}"
                    )

                context_expanded = False

                if request.expand_context:
                    with tracer.start_as_current_span(
                        "rag_search.expand_context",
                    ) as context_span:
                        context_span.set_attribute(
                            "input_results_count",
                            len(results),
                        )
                        results = self._expand_context_for_results(results)
                        context_expanded = True
                        context_span.set_attribute(
                            "output_results_count",
                            len(results),
                        )

                processing_time_ms = int(
                    (perf_counter() - started_at) * 1000
                )

                success_metric_attributes = {
                    **request_metric_attributes,
                    "status": "ok",
                }
                SEARCH_DURATION_MS.record(
                    processing_time_ms,
                    success_metric_attributes,
                )
                SEARCH_RESULTS_COUNT.record(
                    len(results),
                    success_metric_attributes,
                )
                if embedding_tokens:
                    SEARCH_EMBEDDING_TOKENS_TOTAL.add(
                        embedding_tokens,
                        success_metric_attributes,
                    )

                span.set_attribute("processing_time_ms", processing_time_ms)
                span.set_attribute("total_found", len(results))
                span.set_attribute("embedding_tokens", embedding_tokens)
                span.set_attribute("embedding_cost_usd", embedding_cost_usd)
                span.set_attribute("context_expanded", context_expanded)

                span.add_event(
                    "search_finished",
                    {
                        "search_type": request.search_type,
                        "top_k": request.top_k,
                        "total_found": len(results),
                        "processing_time_ms": processing_time_ms,
                        "context_expanded": context_expanded,
                    },
                )

                logger.info(
                    "Search request completed",
                    extra={
                        "search_type": request.search_type,
                        "top_k": request.top_k,
                        "total_found": len(results),
                        "processing_time_ms": processing_time_ms,
                        "context_expanded": context_expanded,
                        "embedding_provider": settings.EMBEDDING_PROVIDER,
                        "embedding_model": settings.EMBEDDING_MODEL,
                        "embedding_dim": settings.EMBEDDING_DIM,
                        "embedding_tokens": embedding_tokens,
                        "embedding_cost_usd": embedding_cost_usd,
                    },
                )

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

            except Exception as exc:
                processing_time_ms = int(
                    (perf_counter() - started_at) * 1000
                )

                failure_metric_attributes = {
                    **request_metric_attributes,
                    "status": "failed",
                    "error_type": type(exc).__name__,
                }
                SEARCH_REQUESTS_FAILED_TOTAL.add(
                    1,
                    failure_metric_attributes,
                )
                SEARCH_DURATION_MS.record(
                    processing_time_ms,
                    failure_metric_attributes,
                )

                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, str(exc)))
                span.set_attribute("processing_time_ms", processing_time_ms)
                span.set_attribute("error_type", type(exc).__name__)

                span.add_event(
                    "search_failed",
                    {
                        "search_type": request.search_type,
                        "top_k": request.top_k,
                        "processing_time_ms": processing_time_ms,
                        "error_type": type(exc).__name__,
                    },
                )

                log_extra = {
                    "search_type": request.search_type,
                    "top_k": request.top_k,
                    "processing_time_ms": processing_time_ms,
                    "error_type": type(exc).__name__,
                    "embedding_provider": settings.EMBEDDING_PROVIDER,
                    "embedding_model": settings.EMBEDDING_MODEL,
                    "embedding_dim": settings.EMBEDDING_DIM,
                }

                if isinstance(exc, ValueError):
                    logger.warning(
                        "Search request rejected",
                        extra=log_extra,
                    )
                else:
                    logger.exception(
                        "Search request failed",
                        extra=log_extra,
                    )

                raise

    def _supports_dense_search(self) -> bool:
        return bool(
            getattr(self.embedding_provider, "supports_dense", True)
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
                    "mode": "hybrid",
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
