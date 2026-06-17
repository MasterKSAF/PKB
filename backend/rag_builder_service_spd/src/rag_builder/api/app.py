# src/rag_builder/api/app.py

from fastapi import FastAPI
from contextlib import asynccontextmanager
from rag_builder.models.responses import (
    HealthResponse,
    IndexResponse,
)

from rag_builder.models.contracts import BuildRequest
from rag_builder.repositories.postgres_chunk_repository import PostgresChunkRepository
from rag_builder.services.indexing_service import IndexingService
from rag_builder.core.logger import logger
from rag_builder.api.search_routes import router as search_router


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
        database_ok = repository.ping()
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

@app.post(
    "/index",
    response_model=IndexResponse,
)
def index_document(
    request: BuildRequest,
) -> IndexResponse:
    """
    Принимает chunk-container,
    строит чанки,
    считает embeddings
    и сохраняет результат в PostgreSQL.
    """

    logger.info(
        "Start indexing document_id=%s",
        request.metadata.document_id,
    )

    repository = PostgresChunkRepository()

    service = IndexingService(repository=repository)

    result = service.index_document(request)

    logger.info(
        "Indexed %s chunks for document_id=%s document_version_id=%s",
        len(result.chunks),
        request.metadata.document_id,
        request.metadata.document_version_id,
    )

    return IndexResponse(
        status="indexed",
        document_id=request.metadata.document_id,
        document_version_id=request.metadata.document_version_id,
        chunks_count=len(result.chunks),
        embedding_tokens=result.embedding_tokens,
        embedding_cost_usd=result.embedding_cost_usd,
    )
