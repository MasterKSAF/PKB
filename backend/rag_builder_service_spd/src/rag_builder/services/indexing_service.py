# src/rag_builder/services/indexing_service.py

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

        chunks = self.chunking_service.build_chunks(request)

        embedded_chunks: list[EmbeddedChunk] = []

        total_tokens = 0
        total_cost = 0.0

        for chunk in chunks:
            embedding_result = (
                self.embedding_service
                .create_embedding_with_usage(
                    chunk.content
                )
            )

            embedded_chunks.append(
                EmbeddedChunk(
                    chunk=chunk,
                    embedding=embedding_result.embedding,
                )
            )

            total_tokens += (
                embedding_result.token_count
            )

            total_cost += (
                embedding_result.cost_usd
            )


        if self.repository is not None:
            self.repository.save_chunks(embedded_chunks)

        return IndexingResult(
            chunks=embedded_chunks,
            embedding_tokens=total_tokens,
            embedding_cost_usd=total_cost,
        )
