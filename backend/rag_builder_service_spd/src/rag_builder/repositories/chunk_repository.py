# src/rag_builder/repositories/chunk_repository.py

from datetime import datetime
from dataclasses import dataclass

from rag_builder.models.domain import EmbeddedChunk


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

    def save_chunks(self, chunks: list[EmbeddedChunk]) -> None:
        """
        Сохраняет список чанков с эмбеддингами.

        Пока не реализовано.
        """
        raise NotImplementedError

class InMemoryChunkRepository(ChunkRepository):
    """
    Тестовая реализация репозитория.

    Хранит чанки в памяти процесса.
    Нужна для unit-тестов и отладки до подключения PostgreSQL.
    """

    def __init__(self) -> None:
        self._chunks: list[EmbeddedChunk] = []

    def save_chunks(self, chunks: list[EmbeddedChunk]) -> None:
        self._chunks.extend(chunks)

    def list_chunks(self) -> list[EmbeddedChunk]:
        return list(self._chunks)

    def count(self) -> int:
        return len(self._chunks)
