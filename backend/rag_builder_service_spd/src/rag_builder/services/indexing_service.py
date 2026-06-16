# src/rag_builder/services/indexing_service.py

from rag_builder.core.logger import logger
from rag_builder.chunking.service import ChunkingService
from rag_builder.models.contracts import BuildRequest
from rag_builder.models.domain import (
    EmbeddedChunk,
    IndexingResult,
)
from rag_builder.repositories.chunk_repository import ChunkRepository
from rag_builder.services.embedding_service import EmbeddingService


class IndexingService:
    """
    Главный сервис индексации документа.

    Конвейер MVP:

        BuildRequest
              ↓
        ChunkingService
              ↓
        EmbeddingService
              ↓
        Result

    Пока данные сохраняются в память.
    """
    def __init__(self, repository: ChunkRepository | None = None) -> None:
        self.chunking_service = ChunkingService()
        self.embedding_service = EmbeddingService()
        self.repository = repository

    def index_document(
            self,
            request: BuildRequest,
    ) -> IndexingResult:
        """
        Индексирует документ.

        Возвращает список чанков с эмбеддингами.
        """
        logger.info(
            "Received %s sections for document_id=%s",
            len(request.sections),
            request.metadata.document_id,
        )

        if self.repository is not None:
            self.repository.save_sections(request)
            self.repository.save_cross_references(request)
            self.repository.save_images(request)
            self.repository.save_extracted_tables(request)
            self.repository.save_formulas(request)

        chunks = self.chunking_service.build_chunks(request)

        logger.info(
            "Produced %s chunks for document_id=%s",
            len(chunks),
            request.metadata.document_id,
        )


        embedded_chunks = (
            self.embedding_service.enrich_chunks(chunks)
        )

        total_tokens = 0
        total_cost = 0.0

        if self.repository is not None:
            self.repository.save_chunks(embedded_chunks)

        return IndexingResult(
            chunks=embedded_chunks,
            embedding_tokens=total_tokens,
            embedding_cost_usd=total_cost,
        )
