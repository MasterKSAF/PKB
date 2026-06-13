# src/rag_builder/repositories/postgres_chunk_repository.py

import json
import psycopg
from psycopg import sql

from rag_builder.core.config import settings
from rag_builder.models.domain import EmbeddedChunk
from rag_builder.repositories.chunk_repository import ChunkRepository


class PostgresChunkRepository(ChunkRepository):
    """
    Репозиторий для сохранения чанков в PostgreSQL.
    """

    def _connect(self):
        return psycopg.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            dbname=settings.POSTGRES_DB,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
        )

    def ping(self) -> bool:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()

        return result == (1,)

    def ensure_schema(self) -> None:
        """
        Создаёт расширение vector, схему и таблицу chunks,
        если они ещё не существуют.
        """

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")

                cur.execute(
                    sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(
                        sql.Identifier(settings.POSTGRES_SCHEMA)
                    )
                )

                cur.execute(
                    sql.SQL(
                        """
                        CREATE TABLE IF NOT EXISTS {}.chunks (
                            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

                            document_id BIGINT NOT NULL,
                            document_version_id BIGINT NOT NULL,

                            section_id BIGINT NOT NULL,
                            parent_id BIGINT,

                            clause TEXT,
                            path TEXT,

                            page INTEGER,
                            bbox JSONB,

                            chunk_index INTEGER NOT NULL,
                            chunk_type TEXT NOT NULL,

                            content TEXT NOT NULL,
                            metadata JSONB,

                            embedding VECTOR(1536),

                            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                        )
                        """
                    ).format(sql.Identifier(settings.POSTGRES_SCHEMA))
                )


    def save_chunks(self, chunks: list[EmbeddedChunk]) -> None:
        """
        Сохраняет чанки в PostgreSQL.
        """

        if not chunks:
            return

        with self._connect() as conn:
            with conn.cursor() as cur:

                for item in chunks:
                    cur.execute(
                        f"""
                        INSERT INTO {settings.POSTGRES_SCHEMA}.chunks (
                            document_id,
                            document_version_id,
                            section_id,
                            parent_id,
                            clause,
                            path,
                            page,
                            bbox,
                            chunk_index,
                            chunk_type,
                            content,
                            metadata,
                            embedding
                        )
                        VALUES (
                            %s, %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, %s, %s, %s, %s
                        )
                        """,
                        (
                            item.chunk.document_id,
                            item.chunk.document_version_id,
                            item.chunk.section_id,
                            item.chunk.parent_id,
                            item.chunk.clause,
                            item.chunk.path,
                            item.chunk.page,
                            json.dumps(item.chunk.bbox),
                            item.chunk.chunk_index,
                            item.chunk.chunk_type,
                            item.chunk.content,
                            json.dumps(item.chunk.metadata),
                            item.embedding,
                        ),
                    )

            conn.commit()