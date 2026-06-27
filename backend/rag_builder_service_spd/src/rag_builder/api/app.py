# src/rag_builder/api/app.py

import time
from contextlib import asynccontextmanager
from uuid import uuid4

from dataclasses import asdict
from typing import Literal

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, status

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from rag_builder.core.logger import logger
from rag_builder.core.config import settings
from rag_builder.core.telemetry import instrument_fastapi, setup_observability
from rag_builder.models.contracts import BuildRequest
from rag_builder.models.responses import (
    DeleteIndexResponse,
    HealthResponse,
    IndexResponse,
    IndexStatusResponse,
    IndexingJobsResponse,
)
from rag_builder.repositories.postgres_chunk_repository import (
    PostgresChunkRepository,
)
from rag_builder.services.indexing_service import IndexingService



def _mark_stale_indexing_jobs_failed(
    repository: PostgresChunkRepository,
) -> int:
    marked_count = repository.mark_stale_indexing_jobs_failed(
        settings.INDEXING_JOB_STALE_AFTER_SECONDS,
    )

    if marked_count:
        logger.warning(
            "Marked %s stale indexing jobs as failed",
            marked_count,
        )

    return marked_count


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting RAG Builder service")

    repository = PostgresChunkRepository()
    repository.assert_schema_ready()

    logger.info("Database schema is ready")
    _mark_stale_indexing_jobs_failed(repository)

    yield

    logger.info("Stopping RAG Builder service")


app = FastAPI(
    title="RAG Builder SPD",
    version="0.1.0",
    lifespan=lifespan,
)

tracer_provider, meter_provider, _observability_logger = setup_observability(
    service_name=settings.SERVICE_NAME,
    otlp_endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
    enabled=settings.OBSERVABILITY_ENABLED,
    log_level=settings.LOG_LEVEL,
)
instrument_fastapi(app, tracer_provider=tracer_provider)

tracer = trace.get_tracer(__name__)


IndexingJobStatus = Literal[
    "pending_index",
    "indexing",
    "indexed",
    "failed",
]


@app.get(
    "/api/v1/health",
    response_model=HealthResponse,
)
def health_check() -> HealthResponse:
    repository = PostgresChunkRepository()

    try:
        repository.ping()
    except Exception as exc:
        logger.exception("Database health check failed")

        return HealthResponse(
            status="degraded",
            service="rag_builder_service_spd",
            database="error",
            error=str(exc),
        )

    return HealthResponse(
        status="ok",
        service="rag_builder_service_spd",
        database="ok",
        error=None,
    )


def _run_indexing_job(
    request: BuildRequest,
    indexing_txn_id: str,
) -> None:
    repository = PostgresChunkRepository()
    service = IndexingService(repository=repository)

    document_id = request.metadata.document_id
    sections_count = len(request.sections)
    started_at = time.perf_counter()

    with tracer.start_as_current_span("rag_builder.index_document") as span:
        span.set_attribute("document_id", document_id)
        span.set_attribute("indexing_txn_id", indexing_txn_id)
        span.set_attribute("sections_count", sections_count)
        span.set_attribute("embedding_provider", settings.EMBEDDING_PROVIDER)
        span.set_attribute("embedding_model", settings.EMBEDDING_MODEL)
        span.set_attribute("embedding_dim", settings.EMBEDDING_DIM)
        span.set_attribute("chunk_strategy", settings.CHUNK_STRATEGY)

        span.add_event(
            "job_started",
            {
                "document_id": document_id,
                "indexing_txn_id": indexing_txn_id,
                "sections_count": sections_count,
            },
        )

        try:
            repository.mark_indexing_job_indexing(indexing_txn_id)
            span.add_event(
                "job_status_changed",
                {
                    "status": "indexing",
                    "indexing_txn_id": indexing_txn_id,
                },
            )

            result = service.index_document(
                request,
                indexing_txn_id=indexing_txn_id,
            )

            chunks_count = len(result.chunks)
            warnings_count = len(result.warnings)
            errors_count = len(result.errors)

            repository.mark_indexing_job_indexed(
                indexing_txn_id=indexing_txn_id,
                chunks_count=chunks_count,
                index_stats={
                    "sections": sections_count,
                    "chunks": chunks_count,
                    "embeddings": chunks_count,
                },
                warnings=[
                    asdict(issue)
                    for issue in result.warnings
                ],
                errors=[
                    asdict(issue)
                    for issue in result.errors
                ],
            )

            duration_ms = int((time.perf_counter() - started_at) * 1000)

            span.set_attribute("indexing.status", "indexed")
            span.set_attribute("duration_ms", duration_ms)
            span.set_attribute("chunks_count", chunks_count)
            span.set_attribute("warnings_count", warnings_count)
            span.set_attribute("errors_count", errors_count)

            span.add_event(
                "job_indexed",
                {
                    "document_id": document_id,
                    "indexing_txn_id": indexing_txn_id,
                    "duration_ms": duration_ms,
                    "chunks_count": chunks_count,
                    "embeddings_count": chunks_count,
                },
            )

            logger.info(
                "Indexing job indexed",
                extra={
                    "document_id": document_id,
                    "indexing_txn_id": indexing_txn_id,
                    "status": "indexed",
                    "duration_ms": duration_ms,
                    "sections_count": sections_count,
                    "chunks_count": chunks_count,
                    "embeddings_count": chunks_count,
                    "warnings_count": warnings_count,
                    "errors_count": errors_count,
                    "embedding_provider": settings.EMBEDDING_PROVIDER,
                    "embedding_model": settings.EMBEDDING_MODEL,
                    "embedding_dim": settings.EMBEDDING_DIM,
                    "chunk_strategy": settings.CHUNK_STRATEGY,
                },
            )

        except Exception as exc:
            duration_ms = int((time.perf_counter() - started_at) * 1000)

            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            span.set_attribute("indexing.status", "failed")
            span.set_attribute("duration_ms", duration_ms)
            span.set_attribute("error_type", type(exc).__name__)

            span.add_event(
                "job_failed",
                {
                    "document_id": document_id,
                    "indexing_txn_id": indexing_txn_id,
                    "duration_ms": duration_ms,
                    "error_type": type(exc).__name__,
                },
            )

            logger.exception(
                "Indexing job failed",
                extra={
                    "document_id": document_id,
                    "indexing_txn_id": indexing_txn_id,
                    "status": "failed",
                    "stage": "index_document",
                    "duration_ms": duration_ms,
                    "error_code": "BUILD_FAILED",
                    "error_type": type(exc).__name__,
                    "embedding_provider": settings.EMBEDDING_PROVIDER,
                    "embedding_model": settings.EMBEDDING_MODEL,
                    "embedding_dim": settings.EMBEDDING_DIM,
                    "chunk_strategy": settings.CHUNK_STRATEGY,
                },
            )

            repository.mark_indexing_job_failed(
                indexing_txn_id=indexing_txn_id,
                errors=[
                    {
                        "code": "BUILD_FAILED",
                        "message": str(exc),
                        "section_id": None,
                    }
                ],
                warnings=[],
            )


@app.post(
    "/api/v1/rag/build",
    response_model=IndexResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_202_ACCEPTED,
)
@app.post(
    "/index",
    response_model=IndexResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_202_ACCEPTED,
)
@app.post(
    "/rag/build",
    response_model=IndexResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_202_ACCEPTED,
)
def index_document(
    request: BuildRequest,
    background_tasks: BackgroundTasks,
) -> IndexResponse:
    logger.info(
        "Start indexing document_id=%s",
        request.metadata.document_id,
    )

    repository = PostgresChunkRepository()

    _mark_stale_indexing_jobs_failed(repository)

    active_job = repository.get_active_indexing_job_for_document(
        document_id=request.metadata.document_id,
        stale_after_seconds=settings.INDEXING_JOB_STALE_AFTER_SECONDS,
    )

    if active_job is not None:
        logger.warning(
            "Reject duplicate active indexing job for document_id=%s",
            request.metadata.document_id,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "ALREADY_PROCESSING",
                "message": "Document indexing is already in progress",
                "details": {
                    "document_id": request.metadata.document_id,
                    "indexing_txn_id": active_job["indexing_txn_id"],
                    "status": active_job["status"],
                },
            },
        )

    max_active_jobs = settings.MAX_ACTIVE_INDEXING_JOBS

    if max_active_jobs > 0:
        active_jobs_count = repository.count_active_indexing_jobs(
            settings.INDEXING_JOB_STALE_AFTER_SECONDS,
        )

        if active_jobs_count >= max_active_jobs:
            logger.warning(
                "Reject indexing job because active jobs limit is reached: %s/%s",
                active_jobs_count,
                max_active_jobs,
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "code": "TOO_MANY_REQUESTS",
                    "message": "Too many active indexing jobs",
                    "details": {
                        "active_jobs": active_jobs_count,
                        "max_active_jobs": max_active_jobs,
                    },
                },
            )

    indexing_txn_id = str(uuid4())

    task_id = repository.create_indexing_job(
        document_id=request.metadata.document_id,
        indexing_txn_id=indexing_txn_id,
        status="indexing",
    )

    background_tasks.add_task(
        _run_indexing_job,
        request,
        indexing_txn_id,
    )

    return IndexResponse(
        status="indexing",
        document_id=request.metadata.document_id,
        task_id=task_id,
        indexing_txn_id=indexing_txn_id,
    )


@app.delete(
    "/api/v1/rag/build/{document_id}",
    response_model=DeleteIndexResponse,
)
@app.delete(
    "/rag/build/{document_id}",
    response_model=DeleteIndexResponse,
)
def delete_document_index(document_id: int) -> DeleteIndexResponse:
    repository = PostgresChunkRepository()

    try:
        deleted_count = repository.delete_document_index(document_id)
    except Exception as exc:
        logger.exception(
            "Failed to delete index for document_id=%s",
            document_id,
        )
        raise HTTPException(
            status_code=500,
            detail={
                "code": "BUILD_FAILED",
                "message": str(exc),
            },
        ) from exc

    return DeleteIndexResponse(
        document_id=document_id,
        deleted_count=deleted_count,
        status="completed",
    )



@app.get(
    "/api/v1/rag/build/jobs",
    response_model=IndexingJobsResponse,
)
def list_indexing_jobs(
    status_filter: IndexingJobStatus | None = Query(
        default=None,
        alias="status",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
) -> IndexingJobsResponse:
    repository = PostgresChunkRepository()

    items, total = repository.list_indexing_jobs(
        status_filter=status_filter,
        page=page,
        page_size=page_size,
    )

    return IndexingJobsResponse(
        items=items,
        meta={
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    )


@app.get(
    "/index/status/{indexing_txn_id}",
    response_model=IndexStatusResponse,
)
def get_indexing_status(
    indexing_txn_id: str,
) -> IndexStatusResponse:
    repository = PostgresChunkRepository()

    job = repository.get_indexing_job(indexing_txn_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Indexing job not found",
        )

    return IndexStatusResponse(**job)


@app.get(
    "/api/v1/rag/build/{document_id}/status",
    response_model=IndexStatusResponse,
)
@app.get(
    "/rag/build/{document_id}/status",
    response_model=IndexStatusResponse,
)
def get_document_indexing_status(
    document_id: int,
    longpoll: int = Query(default=0, ge=0, le=30),
) -> IndexStatusResponse:
    repository = PostgresChunkRepository()

    deadline = time.monotonic() + longpoll

    while True:
        job = repository.get_latest_indexing_job_for_document(document_id)

        if job is not None:
            if job["status"] in {"indexed", "failed"}:
                return IndexStatusResponse(**job)

            if longpoll == 0 or time.monotonic() >= deadline:
                return IndexStatusResponse(**job)

        if longpoll == 0 or time.monotonic() >= deadline:
            raise HTTPException(
                status_code=404,
                detail="Indexing job not found",
            )

        time.sleep(0.5)
