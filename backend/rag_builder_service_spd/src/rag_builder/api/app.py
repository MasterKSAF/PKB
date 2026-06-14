# src/rag_builder/api/app.py

from fastapi import FastAPI

from rag_builder.models.contracts import BuildRequest
from rag_builder.repositories.postgres_chunk_repository import PostgresChunkRepository
from rag_builder.services.indexing_service import IndexingService


app = FastAPI(
    title="RAG Builder SPD",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict:
    return {
        "status": "ok",
        "service": "rag_builder_service_spd",
    }


@app.post("/index")
def index_document(request: BuildRequest) -> dict:
    """
    Принимает chunk-container,
    строит чанки,
    считает embeddings
    и сохраняет результат в PostgreSQL.
    """

    repository = PostgresChunkRepository()
    repository.ensure_schema()

    service = IndexingService(repository=repository)

    embedded_chunks = service.index_document(request)

    return {
        "status": "indexed",
        "document_id": request.metadata.document_id,
        "document_version_id": request.metadata.document_version_id,
        "chunks_count": len(embedded_chunks),
    }
