# src/rag_builder/services/indexing_service.py

from rag_builder.chunking.service import ChunkingService
from rag_builder.models.contracts import BuildRequest
from rag_builder.models.domain import EmbeddedChunk
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

    def index_document(self, request: BuildRequest) -> list[EmbeddedChunk]:
        """
        Индексирует документ.

        Возвращает список чанков с эмбеддингами.
        """

        chunks = self.chunking_service.build_chunks(request)

        embedded_chunks = [
            self.embedding_service.enrich_chunk(chunk)
            for chunk in chunks
        ]

        if self.repository is not None:
            self.repository.save_chunks(embedded_chunks)

        return embedded_chunks
