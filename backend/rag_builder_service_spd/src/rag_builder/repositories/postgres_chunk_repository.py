# src/rag_builder/repositories/postgres_chunk_repository.py

import json
import psycopg
from psycopg import sql

from rag_builder.core.logger import logger
from rag_builder.core.config import settings
from rag_builder.models.domain import EmbeddedChunk
from rag_builder.repositories.chunk_repository import ChunkRepository
from rag_builder.models.contracts import BuildRequest


class PostgresChunkRepository(ChunkRepository):
    """
    Репозиторий для сохранения чанков в PostgreSQL.
    """

    def _connect(self):
        logger.info(
            "PostgreSQL connect host=%s port=%s db=%s user=%s",
            settings.POSTGRES_HOST,
            settings.POSTGRES_PORT,
            settings.POSTGRES_DB,
            settings.POSTGRES_USER,
        )

        return psycopg.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            dbname=settings.POSTGRES_DB,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            connect_timeout=5,
        )

    def ping(self) -> bool:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()

        return result == (1,)



    def ensure_schema(self) -> None:
        """
        Создаёт расширение vector, схему и таблицы  chunks,
        если они ещё не существуют.
        """
        logger.info("ensure_schema: start")
        logger.info("ensure_schema: before connect")

        with self._connect() as conn:
            logger.info("ensure_schema: after connect")

            with conn.cursor() as cur:
                logger.info("ensure_schema: before create extensions")
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
                cur.execute("CREATE EXTENSION IF NOT EXISTS ltree")

                logger.info("ensure_schema: before create schema")
                cur.execute(
                    sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(
                        sql.Identifier(settings.POSTGRES_SCHEMA)
                    )
                )

                logger.info("ensure_schema: before create table document_sections")
                cur.execute(
                    sql.SQL(
                        """
                        CREATE TABLE IF NOT EXISTS {}.document_sections(
                            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                            document_id BIGINT NOT NULL,
                            document_version_id BIGINT NOT NULL,
                            section_id BIGINT NOT NULL,
                            parent_id BIGINT,              
                            clause TEXT,
                            title TEXT,
                            level INTEGER NOT NULL,
                            path TEXT NOT NULL,
                            path_ltree LTREE,               
                            page INTEGER,
                            bbox JSONB,
                            section_type TEXT NOT NULL,
                            metadata JSONB,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                            UNIQUE(document_version_id, section_id)
                        )
                        """
                    ).format(sql.Identifier(settings.POSTGRES_SCHEMA))
                )

                logger.info("ensure_schema: before create table chunks")
                cur.execute(
                    sql.SQL(
                        """
                        CREATE TABLE IF NOT EXISTS {}.chunks (
                            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                            document_id BIGINT NOT NULL,
                            document_version_id BIGINT NOT NULL,
                            document_section_id BIGINT NOT NULL,
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
                            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

                            CONSTRAINT fk_chunks_document_section
                                FOREIGN KEY (document_section_id)
                                REFERENCES {}.document_sections(id)
                                ON DELETE CASCADE
                        )
                        """
                    ).format(
                        sql.Identifier(settings.POSTGRES_SCHEMA),
                        sql.Identifier(settings.POSTGRES_SCHEMA),
                    )
                )

                logger.info("ensure_schema: before create table cross_references")
                cur.execute(
                    sql.SQL(
                        """
                        CREATE TABLE IF NOT EXISTS {}.cross_references (
                            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

                            document_id BIGINT NOT NULL,
                            document_version_id BIGINT NOT NULL,
                            document_section_id BIGINT NOT NULL,

                            source_section_id BIGINT NOT NULL,
                            source_clause TEXT,
                            source_path TEXT,

                            target_document_id BIGINT,
                            target_doc_code TEXT NOT NULL,

                            reference_type TEXT NOT NULL,
                            context TEXT,
                            note TEXT,

                            metadata JSONB,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

                            CONSTRAINT fk_cross_references_document_section
                                FOREIGN KEY (document_section_id)
                                REFERENCES {}.document_sections(id)
                                ON DELETE CASCADE
                        )
                        """
                    ).format(
                        sql.Identifier(settings.POSTGRES_SCHEMA),
                        sql.Identifier(settings.POSTGRES_SCHEMA),
                    )
                )

                logger.info("ensure_schema: before create index cross_references")
                cur.execute(
                    sql.SQL(
                        """
                        CREATE INDEX IF NOT EXISTS idx_cross_references_doc
                        ON {}.cross_references(document_id)
                        """
                    ).format(
                        sql.Identifier(settings.POSTGRES_SCHEMA)
                    )
                )

                cur.execute(
                    sql.SQL(
                        """
                        CREATE INDEX IF NOT EXISTS idx_cross_references_target
                        ON {}.cross_references(target_doc_code)
                        """
                    ).format(
                        sql.Identifier(settings.POSTGRES_SCHEMA)
                    )
                )

            conn.commit()

        logger.info("ensure_schema: done")

    def save_chunks(self, chunks: list[EmbeddedChunk]) -> None:
        """
        Сохраняет чанки в PostgreSQL.
        """

        if not chunks:
            return

        with self._connect() as conn:
            with conn.cursor() as cur:
                document_version_id = chunks[0].chunk.document_version_id

                cur.execute(
                    f"""
                    DELETE FROM {settings.POSTGRES_SCHEMA}.chunks
                    WHERE document_version_id = %s
                    """,
                    (document_version_id,),
                )

                cur.execute(
                    f"""
                    SELECT section_id, id
                    FROM {settings.POSTGRES_SCHEMA}.document_sections
                    WHERE document_version_id = %s
                    """,
                    (document_version_id,),
                )

                section_id_to_db_id = {
                    section_id: document_section_id
                    for section_id, document_section_id in cur.fetchall()
                }

                for item in chunks:
                    document_section_id = section_id_to_db_id.get(
                        item.chunk.section_id
                    )

                    if document_section_id is None:
                        raise ValueError(
                            "No document_section_id found for "
                            f"document_version_id={document_version_id}, "
                            f"section_id={item.chunk.section_id}"
                        )

                    cur.execute(
                        f"""
                        INSERT INTO {settings.POSTGRES_SCHEMA}.chunks (
                            document_id,
                            document_version_id,
                            document_section_id,
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
                            %s, %s, %s, %s,
                            %s, %s
                        )
                        """,
                        (
                            item.chunk.document_id,
                            item.chunk.document_version_id,
                            document_section_id,
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
                            json.dumps(item.embedding),
                        ),
                    )


            conn.commit()

    def save_sections(self, request: BuildRequest) -> None:
        logger.info(
            "Saving %s document sections",
            len(request.sections),
        )

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    DELETE FROM {settings.POSTGRES_SCHEMA}.document_sections
                    WHERE document_version_id = %s
                    """,
                    (request.metadata.document_version_id,),
                )

                for section in request.sections:
                    cur.execute(
                        f"""
                        INSERT INTO {settings.POSTGRES_SCHEMA}.document_sections (
                            document_id,
                            document_version_id,
                            section_id,
                            parent_id,
                            clause,
                            title,
                            level,
                            path,
                            page,
                            bbox,
                            section_type,
                            metadata
                        )
                        VALUES (
                            %s, %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, %s, %s, %s
                        )
                        """,
                        (
                            request.metadata.document_id,
                            request.metadata.document_version_id,
                            section.section_id,
                            section.parent_id,
                            section.clause,
                            section.title,
                            section.level,
                            section.path,
                            section.page,
                            json.dumps(section.bbox),
                            section.type,
                            json.dumps({
                                "references": [
                                    ref.model_dump()
                                    for ref in section.references
                                ],
                                "raw_content": section.content,
                            }),
                        ),
                    )

            conn.commit()

    def save_cross_references(
            self,
            request: BuildRequest,
    ) -> None:
        logger.info(
            "Saving cross references for document_id=%s",
            request.metadata.document_id,
        )

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    DELETE FROM {settings.POSTGRES_SCHEMA}.cross_references
                    WHERE document_version_id = %s
                    """,
                    (request.metadata.document_version_id,),
                )

                cur.execute(
                    f"""
                    SELECT section_id, id
                    FROM {settings.POSTGRES_SCHEMA}.document_sections
                    WHERE document_version_id = %s
                    """,
                    (request.metadata.document_version_id,),
                )

                section_id_to_db_id = {
                    section_id: document_section_id
                    for section_id, document_section_id in cur.fetchall()
                }

                for section in request.sections:
                    document_section_id = section_id_to_db_id.get(
                        section.section_id
                    )

                    if document_section_id is None:
                        raise ValueError(
                            "No document_section_id found for "
                            f"document_version_id={request.metadata.document_version_id}, "
                            f"section_id={section.section_id}"
                        )

                    for ref in section.references:
                        cur.execute(
                            f"""
                            INSERT INTO {settings.POSTGRES_SCHEMA}.cross_references (
                                document_id,
                                document_version_id,
                                document_section_id,
                                source_section_id,
                                source_clause,
                                source_path,
                                target_document_id,
                                target_doc_code,
                                reference_type,
                                context,
                                note,
                                metadata
                            )
                            VALUES (
                                %s, %s, %s, %s,
                                %s, %s, %s, %s,
                                %s, %s, %s, %s
                            )
                            """,
                            (
                                request.metadata.document_id,
                                request.metadata.document_version_id,
                                document_section_id,
                                section.section_id,
                                section.clause,
                                section.path,
                                ref.target_document_id,
                                ref.target_doc_code,
                                ref.type,
                                ref.context,
                                ref.note,
                                json.dumps(ref.model_dump()),
                            ),
                        )

            conn.commit()