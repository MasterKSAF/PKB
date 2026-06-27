# src/rag_builder/services/indexing_service.py

from time import perf_counter

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from rag_builder.core.config import settings
from rag_builder.core.logger import logger
from rag_builder.chunking.service import ChunkingService
from rag_builder.models.contracts import BuildRequest
from rag_builder.models.domain import (
    EmbeddedChunk,
    IndexIssue,
    IndexingResult,
)
from rag_builder.repositories.chunk_repository import ChunkRepository
from rag_builder.services.embedding_service import EmbeddingService


tracer = trace.get_tracer(__name__)


class IndexingService:
    """Document indexing pipeline service."""

    def __init__(self, repository: ChunkRepository | None = None) -> None:
        self.chunking_service = ChunkingService()
        self.embedding_service = EmbeddingService()
        self.repository = repository

    def index_document(
        self,
        request: BuildRequest,
        indexing_txn_id: str | None = None,
    ) -> IndexingResult:
        """Index a document and return embedded chunks."""
        document_id = request.metadata.document_id
        sections_count = len(request.sections)
        started_at = perf_counter()

        with tracer.start_as_current_span(
            "rag_builder.indexing_pipeline",
        ) as span:
            span.set_attribute("document_id", document_id)
            span.set_attribute("indexing_txn_id", indexing_txn_id or "")
            span.set_attribute("sections_count", sections_count)
            span.set_attribute("embedding_provider", settings.EMBEDDING_PROVIDER)
            span.set_attribute("embedding_model", settings.EMBEDDING_MODEL)
            span.set_attribute("embedding_dim", settings.EMBEDDING_DIM)
            span.set_attribute("chunk_strategy", settings.CHUNK_STRATEGY)

            span.add_event(
                "sections_received",
                {
                    "document_id": document_id,
                    "sections_count": sections_count,
                },
            )

            logger.info(
                "Indexing pipeline received sections",
                extra={
                    "document_id": document_id,
                    "indexing_txn_id": indexing_txn_id,
                    "stage": "sections_received",
                    "sections_count": sections_count,
                },
            )

            warnings: list[IndexIssue] = []
            errors: list[IndexIssue] = []

            try:
                if self.repository is not None:
                    with tracer.start_as_current_span(
                        "rag_builder.cleanup_old_index",
                    ) as cleanup_span:
                        cleanup_span.set_attribute("document_id", document_id)
                        cleanup_span.set_attribute(
                            "indexing_txn_id",
                            indexing_txn_id or "",
                        )
                        self.repository.cleanup_document_index(request)
                        span.add_event(
                            "old_index_cleaned",
                            {"document_id": document_id},
                        )

                    with tracer.start_as_current_span(
                        "rag_builder.save_sections",
                    ) as save_sections_span:
                        save_sections_span.set_attribute(
                            "document_id",
                            document_id,
                        )
                        save_sections_span.set_attribute(
                            "sections_count",
                            sections_count,
                        )
                        self.repository.save_sections(request)
                        span.add_event(
                            "sections_saved",
                            {
                                "document_id": document_id,
                                "sections_count": sections_count,
                            },
                        )

                    with tracer.start_as_current_span(
                        "rag_builder.save_cross_references",
                    ) as cross_refs_span:
                        cross_refs_span.set_attribute("document_id", document_id)
                        self.repository.save_cross_references(request)
                        span.add_event(
                            "cross_references_saved",
                            {"document_id": document_id},
                        )

                    with tracer.start_as_current_span(
                        "rag_builder.save_images",
                    ) as images_span:
                        images_span.set_attribute("document_id", document_id)
                        self.repository.save_images(request)
                        span.add_event(
                            "images_saved",
                            {"document_id": document_id},
                        )

                    with tracer.start_as_current_span(
                        "rag_builder.save_tables",
                    ) as tables_span:
                        tables_span.set_attribute("document_id", document_id)
                        self.repository.save_extracted_tables(request)
                        span.add_event(
                            "tables_saved",
                            {"document_id": document_id},
                        )

                    with tracer.start_as_current_span(
                        "rag_builder.save_formulas",
                    ) as formulas_span:
                        formulas_span.set_attribute("document_id", document_id)
                        self.repository.save_formulas(request)
                        span.add_event(
                            "formulas_saved",
                            {"document_id": document_id},
                        )

                with tracer.start_as_current_span(
                    "rag_builder.produce_chunks",
                ) as chunking_span:
                    chunking_span.set_attribute("document_id", document_id)
                    chunks = self.chunking_service.build_chunks(request)
                    chunks_count = len(chunks)
                    chunking_span.set_attribute("chunks_count", chunks_count)

                span.set_attribute("chunks_count", chunks_count)
                span.add_event(
                    "chunks_produced",
                    {
                        "document_id": document_id,
                        "chunks_count": chunks_count,
                    },
                )

                logger.info(
                    "Indexing pipeline produced chunks",
                    extra={
                        "document_id": document_id,
                        "indexing_txn_id": indexing_txn_id,
                        "stage": "chunks_produced",
                        "sections_count": sections_count,
                        "chunks_count": chunks_count,
                    },
                )

                if not chunks:
                    warnings.append(
                        IndexIssue(
                            code="NO_INDEXABLE_CONTENT",
                            message="No indexable chunks were produced",
                            section_id=None,
                        )
                    )

                    embedded_chunks: list[EmbeddedChunk] = []
                    total_tokens = 0
                    total_cost = 0.0

                    span.add_event(
                        "no_indexable_content",
                        {"document_id": document_id},
                    )

                else:
                    with tracer.start_as_current_span(
                        "rag_builder.create_embeddings",
                    ) as embedding_span:
                        embedding_span.set_attribute(
                            "document_id",
                            document_id,
                        )
                        embedding_span.set_attribute(
                            "indexing_txn_id",
                            indexing_txn_id or "",
                        )
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
                        embedding_span.set_attribute("chunks_count", chunks_count)

                        span.add_event(
                            "embedding_batch_started",
                            {
                                "document_id": document_id,
                                "chunks_count": chunks_count,
                            },
                        )

                        embedding_result = (
                            self.embedding_service.enrich_chunks(chunks)
                        )

                        embedded_chunks = embedding_result.chunks
                        total_tokens = embedding_result.token_count
                        total_cost = embedding_result.cost_usd

                        embedding_span.set_attribute(
                            "embedding_tokens",
                            total_tokens,
                        )
                        embedding_span.set_attribute(
                            "embedding_cost_usd",
                            total_cost,
                        )

                    span.add_event(
                        "embedding_batch_finished",
                        {
                            "document_id": document_id,
                            "chunks_count": len(embedded_chunks),
                            "embedding_tokens": total_tokens,
                        },
                    )

                if self.repository is not None:
                    with tracer.start_as_current_span(
                        "rag_builder.save_chunks",
                    ) as save_chunks_span:
                        save_chunks_span.set_attribute("document_id", document_id)
                        save_chunks_span.set_attribute(
                            "indexing_txn_id",
                            indexing_txn_id or "",
                        )
                        save_chunks_span.set_attribute(
                            "chunks_count",
                            len(embedded_chunks),
                        )
                        save_chunks_span.set_attribute(
                            "embeddings_count",
                            len(embedded_chunks),
                        )

                        self.repository.save_chunks(
                            embedded_chunks,
                            indexing_txn_id=indexing_txn_id,
                        )

                    span.add_event(
                        "chunks_saved",
                        {
                            "document_id": document_id,
                            "chunks_count": len(embedded_chunks),
                            "embeddings_count": len(embedded_chunks),
                        },
                    )

                duration_ms = int((perf_counter() - started_at) * 1000)

                span.set_attribute("duration_ms", duration_ms)
                span.set_attribute("embeddings_count", len(embedded_chunks))
                span.set_attribute("embedding_tokens", total_tokens)
                span.set_attribute("embedding_cost_usd", total_cost)

                span.add_event(
                    "indexing_pipeline_finished",
                    {
                        "document_id": document_id,
                        "duration_ms": duration_ms,
                        "chunks_count": len(embedded_chunks),
                        "embeddings_count": len(embedded_chunks),
                    },
                )

                logger.info(
                    "Indexing pipeline completed",
                    extra={
                        "document_id": document_id,
                        "indexing_txn_id": indexing_txn_id,
                        "stage": "indexing_pipeline_finished",
                        "duration_ms": duration_ms,
                        "sections_count": sections_count,
                        "chunks_count": len(embedded_chunks),
                        "embeddings_count": len(embedded_chunks),
                        "embedding_tokens": total_tokens,
                        "embedding_cost_usd": total_cost,
                        "embedding_provider": settings.EMBEDDING_PROVIDER,
                        "embedding_model": settings.EMBEDDING_MODEL,
                        "embedding_dim": settings.EMBEDDING_DIM,
                        "chunk_strategy": settings.CHUNK_STRATEGY,
                        "warnings_count": len(warnings),
                        "errors_count": len(errors),
                    },
                )

                return IndexingResult(
                    chunks=embedded_chunks,
                    embedding_tokens=total_tokens,
                    embedding_cost_usd=total_cost,
                    warnings=warnings,
                    errors=errors,
                )

            except Exception as exc:
                duration_ms = int((perf_counter() - started_at) * 1000)

                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, str(exc)))
                span.set_attribute("duration_ms", duration_ms)
                span.set_attribute("error_type", type(exc).__name__)

                span.add_event(
                    "indexing_pipeline_failed",
                    {
                        "document_id": document_id,
                        "duration_ms": duration_ms,
                        "error_type": type(exc).__name__,
                    },
                )

                logger.exception(
                    "Indexing pipeline failed",
                    extra={
                        "document_id": document_id,
                        "indexing_txn_id": indexing_txn_id,
                        "stage": "indexing_pipeline",
                        "duration_ms": duration_ms,
                        "error_type": type(exc).__name__,
                        "embedding_provider": settings.EMBEDDING_PROVIDER,
                        "embedding_model": settings.EMBEDDING_MODEL,
                        "embedding_dim": settings.EMBEDDING_DIM,
                        "chunk_strategy": settings.CHUNK_STRATEGY,
                    },
                )

                raise
