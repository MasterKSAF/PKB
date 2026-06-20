# src/rag_builder/api/app.py

import time
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, status

from rag_builder.api.search_routes import router as search_router
from rag_builder.core.logger import logger
from rag_builder.models.contracts import BuildRequest
from rag_builder.models.responses import (
    HealthResponse,
    IndexResponse,
    IndexStatusResponse,
)
from rag_builder.repositories.postgres_chunk_repository import (
    PostgresChunkRepository,
)
from rag_builder.services.indexing_service import IndexingService


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting RAG Builder service")

    repository = PostgresChunkRepository()
    repository.ensure_schema()

    logger.info("Database schema ensured")

    yield

    logger.info("Stopping RAG Builder service")


app = FastAPI(
    title="RAG Builder SPD",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(search_router)


@app.get(
    "/health",
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

    try:
        repository.mark_indexing_job_indexing(indexing_txn_id)

        result = service.index_document(
            request,
            indexing_txn_id=indexing_txn_id,
        )

        chunks_count = len(result.chunks)

        repository.mark_indexing_job_indexed(
            indexing_txn_id=indexing_txn_id,
            chunks_count=chunks_count,
            index_stats={
                "sections": len(request.sections),
                "chunks": chunks_count,
                "embeddings": chunks_count,
            },
            warnings=[],
            errors=[],
        )

        logger.info(
            "Indexing job %s indexed %s chunks for document_id=%s",
            indexing_txn_id,
            chunks_count,
            request.metadata.document_id,
        )

    except Exception as exc:
        logger.exception(
            "Indexing job %s failed for document_id=%s",
            indexing_txn_id,
            request.metadata.document_id,
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