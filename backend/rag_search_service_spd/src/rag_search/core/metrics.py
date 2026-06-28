# src/rag_search/core/metrics.py

from opentelemetry import metrics

meter = metrics.get_meter("rag_search_service_spd")

SEARCH_REQUESTS_TOTAL = meter.create_counter(
    name="rag_search_requests_total",
    unit="1",
    description="Total number of RAG Search requests.",
)

SEARCH_REQUESTS_FAILED_TOTAL = meter.create_counter(
    name="rag_search_requests_failed_total",
    unit="1",
    description="Total number of failed or rejected RAG Search requests.",
)

SEARCH_DURATION_MS = meter.create_histogram(
    name="rag_search_duration_ms",
    unit="ms",
    description="RAG Search request duration in milliseconds.",
)

SEARCH_RESULTS_COUNT = meter.create_histogram(
    name="rag_search_results_count",
    unit="1",
    description="Number of results returned by RAG Search requests.",
)

SEARCH_EMBEDDING_TOKENS_TOTAL = meter.create_counter(
    name="rag_search_embedding_tokens_total",
    unit="1",
    description="Total number of query embedding tokens used by RAG Search.",
)
