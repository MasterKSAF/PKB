# src/rag_builder/repositories/chunk_repository.py

from datetime import datetime
from dataclasses import dataclass

from rag_builder.models.domain import EmbeddedChunk
from rag_builder.models.contracts import BuildRequest


@dataclass(frozen=True)
class ChunkRecord:
    """
    Объект хранения чанка.

    В будущем будет соответствовать записи
    таблицы nsi.chunks.
    """
    embedded_chunk: EmbeddedChunk
    created_at: datetime


class ChunkRepository:
    """
    Репозиторий для сохранения и получения чанков.

    Текущая версия является интерфейсом-заглушкой.

    В будущем будет реализовано сохранение
    в PostgreSQL (nsi.chunks).
    """
    def cleanup_document_index(
            self,
            request: BuildRequest,
    ) -> None:
        raise NotImplementedError
    def save_chunks(
            self,
            chunks: list[EmbeddedChunk],
            indexing_txn_id: str | None = None,
    ) -> None:
        """
        Сохраняет список чанков с эмбеддингами.

        Пока не реализовано.
        """
        raise NotImplementedError

    def save_sections(
            self,
            request: BuildRequest,
    ) -> None:
        raise NotImplementedError

    def save_cross_references(
            self,
            request: BuildRequest,
    ) -> None:
        raise NotImplementedError

    def save_images(
            self,
            request: BuildRequest,
    ) -> None:
        raise NotImplementedError

    def save_extracted_tables(
            self,
            request: BuildRequest,
    ) -> None:
        raise NotImplementedError

    def save_formulas(
        self,
        request: BuildRequest,
    ) -> None:
        raise NotImplementedError



class InMemoryChunkRepository(ChunkRepository):
    """
    Тестовая реализация репозитория.

    Хранит чанки в памяти процесса.
    Нужна для unit-тестов и отладки до подключения PostgreSQL.
    """

    def __init__(self) -> None:
        self._chunks: list[EmbeddedChunk] = []

    def cleanup_document_index(
            self,
            request: BuildRequest,
    ) -> None:
        self._chunks.clear()

    def save_chunks(
            self,
            chunks: list[EmbeddedChunk],
            indexing_txn_id: str | None = None,
    ) -> None:
        self._chunks.extend(chunks)

    def list_chunks(self) -> list[EmbeddedChunk]:
        return list(self._chunks)

    def count(self) -> int:
        return len(self._chunks)

    def save_sections(
            self,
            request: BuildRequest,
    ) -> None:
        pass

    def save_cross_references(
        self,
        request: BuildRequest,
    ) -> None:
        pass

    def save_images(
            self,
            request: BuildRequest,
    ) -> None:
        pass

    def save_extracted_tables(
            self,
            request: BuildRequest,
    ) -> None:
        pass

    def save_formulas(
        self,
        request: BuildRequest,
    ) -> None:
        pass
