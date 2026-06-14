# src/rag_builder/api/app.py

from fastapi import FastAPI

from rag_builder.models.contracts import BuildRequest
from rag_builder.repositories.postgres_chunk_repository import PostgresChunkRepository
from rag_builder.services.indexing_service import IndexingService
from rag_builder.core.logger import logger

app = FastAPI(
    title="RAG Builder SPD",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict:
    repository = PostgresChunkRepository()

    try:
        database_ok = repository.ping()
    except Exception as exc:
        return {
            "status": "degraded",
            "service": "rag_builder_service_spd",
            "database": "error",
            "error": str(exc),
        }

    return {
        "status": "ok" if database_ok else "degraded",
        "service": "rag_builder_service_spd",
        "database": "ok" if database_ok else "error",
    }


@app.post("/index")
def index_document(request: BuildRequest) -> dict:
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
    repository.ensure_schema()

    service = IndexingService(repository=repository)

    embedded_chunks = service.index_document(request)

    logger.info(
        "Indexed %s chunks for document_id=%s document_version_id=%s",
        len(embedded_chunks),
        request.metadata.document_id,
        request.metadata.document_version_id,
    )

    return {
        "status": "indexed",
        "document_id": request.metadata.document_id,
        "document_version_id": request.metadata.document_version_id,
        "chunks_count": len(embedded_chunks),
    }
