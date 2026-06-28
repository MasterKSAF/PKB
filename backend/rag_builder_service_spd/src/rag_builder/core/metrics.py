# src/rag_builder/core/metrics.py

from opentelemetry import metrics

meter = metrics.get_meter("rag_builder_service_spd")

INDEXING_JOBS_STARTED_TOTAL = meter.create_counter(
    name="rag_builder_indexing_jobs_started_total",
    unit="1",
    description="Total number of accepted RAG Builder indexing jobs.",
)

INDEXING_JOBS_COMPLETED_TOTAL = meter.create_counter(
    name="rag_builder_indexing_jobs_completed_total",
    unit="1",
    description="Total number of successfully completed RAG Builder indexing jobs.",
)

INDEXING_JOBS_FAILED_TOTAL = meter.create_counter(
    name="rag_builder_indexing_jobs_failed_total",
    unit="1",
    description="Total number of failed RAG Builder indexing jobs.",
)

INDEXING_DURATION_MS = meter.create_histogram(
    name="rag_builder_indexing_duration_ms",
    unit="ms",
    description="RAG Builder indexing job duration in milliseconds.",
)

CHUNKS_CREATED_TOTAL = meter.create_counter(
    name="rag_builder_chunks_created_total",
    unit="1",
    description="Total number of chunks created by RAG Builder.",
)

EMBEDDINGS_CREATED_TOTAL = meter.create_counter(
    name="rag_builder_embeddings_created_total",
    unit="1",
    description="Total number of embeddings created by RAG Builder.",
)
