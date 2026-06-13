# src/rag_builder/repositories/postgres_chunk_repository.py

import psycopg

from rag_builder.core.config import settings
from rag_builder.models.domain import EmbeddedChunk
from rag_builder.repositories.chunk_repository import ChunkRepository


class PostgresChunkRepository(ChunkRepository):

    def ping(self) -> bool:
        with psycopg.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            dbname=settings.POSTGRES_DB,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()

        return result == (1,)

    def save_chunks(self, chunks: list[EmbeddedChunk]) -> None:
        raise NotImplementedError