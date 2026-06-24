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

    # def _embedding_dim_sql(self) -> sql.SQL:
    #     embedding_dim = int(settings.EMBEDDING_DIM)
    #
    #     supported_dims = {
    #         1536,
    #         2048,
    #         2560,
    #         4096,
    #     }
    #
    #     if embedding_dim not in supported_dims:
    #         raise ValueError(
    #             f"Unsupported EMBEDDING_DIM={embedding_dim}. "
    #             f"Supported values: {sorted(supported_dims)}"
    #         )
    #
    #     return sql.SQL(str(embedding_dim))

    def _embedding_dim_sql(self) -> sql.SQL:
        embedding_dim = int(settings.EMBEDDING_DIM)

        if embedding_dim <= 0:
            raise ValueError(
                f"Invalid EMBEDDING_DIM={embedding_dim}. "
                "EMBEDDING_DIM must be a positive integer."
            )

        if embedding_dim > 16000:
            raise ValueError(
                f"Invalid EMBEDDING_DIM={embedding_dim}. "
                "EMBEDDING_DIM is too large for pgvector VECTOR."
            )

        return sql.SQL(str(embedding_dim))


    def create_indexing_job(
        self,
        document_id: int,
        indexing_txn_id: str,
        status: str = "indexing",
    ) -> int:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {settings.POSTGRES_SCHEMA}.indexing_jobs (
                        indexing_txn_id,
                        document_id,
                        status
                    )
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (
                        indexing_txn_id,
                        document_id,
                        status,
                    ),
                )

                task_id = cur.fetchone()[0]

            conn.commit()

        return task_id

    def mark_indexing_job_indexing(
        self,
        indexing_txn_id: str,
    ) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE {settings.POSTGRES_SCHEMA}.indexing_jobs
                    SET
                        status = 'indexing',
                        updated_at = now()
                    WHERE indexing_txn_id = %s
                    """,
                    (indexing_txn_id,),
                )

            conn.commit()

    def mark_indexing_job_indexed(
        self,
        indexing_txn_id: str,
        chunks_count: int,
        index_stats: dict,
        warnings: list[dict] | None = None,
        errors: list[dict] | None = None,
    ) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE {settings.POSTGRES_SCHEMA}.indexing_jobs
                    SET
                        status = 'indexed',
                        chunks_count = %s,
                        has_embeddings = %s,
                        indexed_at = now(),
                        index_stats = %s,
                        warnings = %s,
                        errors = %s,
                        updated_at = now()
                    WHERE indexing_txn_id = %s
                    """,
                    (
                        chunks_count,
                        chunks_count > 0,
                        json.dumps(index_stats),
                        json.dumps(warnings or []),
                        json.dumps(errors or []),
                        indexing_txn_id,
                    ),
                )

            conn.commit()

    def mark_indexing_job_failed(
        self,
        indexing_txn_id: str,
        errors: list[dict],
        warnings: list[dict] | None = None,
    ) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE {settings.POSTGRES_SCHEMA}.indexing_jobs
                    SET
                        status = 'failed',
                        errors = %s,
                        warnings = %s,
                        updated_at = now()
                    WHERE indexing_txn_id = %s
                    """,
                    (
                        json.dumps(errors),
                        json.dumps(warnings or []),
                        indexing_txn_id,
                    ),
                )

            conn.commit()

    def get_indexing_job(
        self,
        indexing_txn_id: str,
    ) -> dict | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT
                        document_id,
                        status,
                        indexing_txn_id::text,
                        chunks_count,
                        has_embeddings,
                        indexed_at,
                        index_stats,
                        warnings,
                        errors
                    FROM {settings.POSTGRES_SCHEMA}.indexing_jobs
                    WHERE indexing_txn_id = %s
                    """,
                    (indexing_txn_id,),
                )

                row = cur.fetchone()

        if row is None:
            return None

        return {
            "document_id": row[0],
            "status": row[1],
            "indexing_txn_id": row[2],
            "chunks_count": row[3],
            "has_embeddings": row[4],
            "indexed_at": row[5],
            "index_stats": row[6] or {},
            "warnings": row[7] or [],
            "errors": row[8] or [],
        }

    def get_latest_indexing_job_for_document(
        self,
        document_id: int,
    ) -> dict | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT
                        document_id,
                        status,
                        indexing_txn_id::text,
                        chunks_count,
                        has_embeddings,
                        indexed_at,
                        index_stats,
                        warnings,
                        errors
                    FROM {settings.POSTGRES_SCHEMA}.indexing_jobs
                    WHERE document_id = %s
                    ORDER BY created_at DESC, id DESC
                    LIMIT 1
                    """,
                    (document_id,),
                )

                row = cur.fetchone()

        if row is None:
            return None

        return {
            "document_id": row[0],
            "status": row[1],
            "indexing_txn_id": row[2],
            "chunks_count": row[3],
            "has_embeddings": row[4],
            "indexed_at": row[5],
            "index_stats": row[6] or {},
            "warnings": row[7] or [],
            "errors": row[8] or [],
        }

# Создание схемы базы данных и таблиц

    def _ensure_chunks_embedding_dim(self, cur) -> None:
        embedding_dim = int(settings.EMBEDDING_DIM)

        cur.execute(
            """
            SELECT atttypmod
            FROM pg_attribute
            WHERE attrelid = %s::regclass
              AND attname = 'embedding'
              AND NOT attisdropped
            """,
            (f"{settings.POSTGRES_SCHEMA}.chunks",),
        )

        row = cur.fetchone()

        if row is None:
            return

        current_dim = row[0]

        if current_dim == embedding_dim:
            return

        logger.warning(
            "Changing chunks.embedding dimension from %s to %s. "
            "Existing embeddings will be cleared; documents must be reindexed.",
            current_dim,
            embedding_dim,
        )

        cur.execute(
            sql.SQL(
                """
                UPDATE {schema}.chunks
                SET embedding = NULL
                WHERE embedding IS NOT NULL
                """
            ).format(
                schema=sql.Identifier(settings.POSTGRES_SCHEMA),
            )
        )

        cur.execute(
            sql.SQL(
                """
                ALTER TABLE {schema}.chunks
                ALTER COLUMN embedding TYPE VECTOR({embedding_dim})
                """
            ).format(
                schema=sql.Identifier(settings.POSTGRES_SCHEMA),
                embedding_dim=self._embedding_dim_sql(),
            )
        )

    def list_indexing_jobs(
        self,
        status_filter: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[dict], int]:
        offset = (page - 1) * page_size

        where_clause = sql.SQL("")
        params: list[object] = []

        if status_filter is not None:
            where_clause = sql.SQL("WHERE status = %s")
            params.append(status_filter)

        count_query = sql.SQL(
            """
            SELECT count(*)
            FROM {schema}.indexing_jobs
            {where_clause}
            """
        ).format(
            schema=sql.Identifier(settings.POSTGRES_SCHEMA),
            where_clause=where_clause,
        )

        list_query = sql.SQL(
            """
            SELECT
                id,
                indexing_txn_id::text,
                document_id,
                status,
                chunks_count,
                has_embeddings,
                indexed_at,
                index_stats,
                warnings,
                errors,
                created_at,
                updated_at
            FROM {schema}.indexing_jobs
            {where_clause}
            ORDER BY created_at DESC, id DESC
            LIMIT %s
            OFFSET %s
            """
        ).format(
            schema=sql.Identifier(settings.POSTGRES_SCHEMA),
            where_clause=where_clause,
        )

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(count_query, params)
                total = cur.fetchone()[0]

                cur.execute(
                    list_query,
                    [
                        *params,
                        page_size,
                        offset,
                    ],
                )
                rows = cur.fetchall()

        items = [
            {
                "id": row[0],
                "indexing_txn_id": row[1],
                "document_id": row[2],
                "status": row[3],
                "chunks_count": row[4],
                "has_embeddings": row[5],
                "indexed_at": row[6],
                "index_stats": row[7] or {},
                "warnings": row[8] or [],
                "errors": row[9] or [],
                "created_at": row[10],
                "updated_at": row[11],
            }
            for row in rows
        ]

        return items, total


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

                logger.info("ensure_schema: before create table indexing_jobs")
                cur.execute(
                    sql.SQL(
                        """
                        CREATE TABLE IF NOT EXISTS {}.indexing_jobs (
                            id BIGINT GENERATED ALWAYS AS IDENTITY UNIQUE,

                            indexing_txn_id UUID PRIMARY KEY,
                            document_id BIGINT NOT NULL,

                            status TEXT NOT NULL,
                            chunks_count INTEGER NOT NULL DEFAULT 0,
                            has_embeddings BOOLEAN NOT NULL DEFAULT false,
                            indexed_at TIMESTAMPTZ,

                            index_stats JSONB NOT NULL DEFAULT jsonb_build_object(),
                            warnings JSONB NOT NULL DEFAULT jsonb_build_array(),
                            errors JSONB NOT NULL DEFAULT jsonb_build_array(),

                            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

                            CONSTRAINT chk_indexing_jobs_status
                                CHECK (status IN (
                                    'pending_index',
                                    'indexing',
                                    'indexed',
                                    'failed'
                                ))
                        )
                        """
                    ).format(sql.Identifier(settings.POSTGRES_SCHEMA))
                )

                cur.execute(
                    sql.SQL(
                        """
                        CREATE INDEX IF NOT EXISTS idx_indexing_jobs_document_id
                        ON {}.indexing_jobs(document_id)
                        """
                    ).format(sql.Identifier(settings.POSTGRES_SCHEMA))
                )

                cur.execute(
                    sql.SQL(
                        """
                        CREATE INDEX IF NOT EXISTS idx_indexing_jobs_status
                        ON {}.indexing_jobs(status)
                        """
                    ).format(sql.Identifier(settings.POSTGRES_SCHEMA))
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

                logger.info("ensure_schema: before create index document_sections_ltree")
                cur.execute(
                    sql.SQL(
                        """
                        CREATE INDEX IF NOT EXISTS idx_document_sections_ltree
                        ON {}.document_sections
                        USING GIST(path_ltree)
                        """
                    ).format(
                        sql.Identifier(settings.POSTGRES_SCHEMA)
                    )
                )

                logger.info("ensure_schema: before create table chunks")
                cur.execute(
                    sql.SQL(
                        """
                        CREATE TABLE IF NOT EXISTS {schema}.chunks (
                            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                            document_id BIGINT NOT NULL,
                            document_version_id BIGINT NOT NULL,
                            indexing_txn_id UUID,
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
                            content_tsv TSVECTOR,
                            metadata JSONB,
                            embedding VECTOR({embedding_dim}),
                            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

                            CONSTRAINT fk_chunks_document_section
                                FOREIGN KEY (document_section_id)
                                REFERENCES {schema}.document_sections(id)
                                ON DELETE CASCADE
                        )
                        """
                    ).format(
                        schema=sql.Identifier(settings.POSTGRES_SCHEMA),
                        embedding_dim=self._embedding_dim_sql(),
                    )
                )

                logger.info("ensure_schema: before alter chunks add indexing_txn_id")
                cur.execute(
                    sql.SQL(
                        """
                        ALTER TABLE {}.chunks
                        ADD COLUMN IF NOT EXISTS indexing_txn_id UUID
                        """
                    ).format(sql.Identifier(settings.POSTGRES_SCHEMA))
                )

                self._ensure_chunks_embedding_dim(cur)

                cur.execute(
                    sql.SQL(
                        """
                        CREATE INDEX IF NOT EXISTS idx_chunks_indexing_txn_id
                        ON {}.chunks(indexing_txn_id)
                        """
                    ).format(sql.Identifier(settings.POSTGRES_SCHEMA))
                )

                logger.info("ensure_schema: before create index chunks_content_tsv")
                cur.execute(
                    sql.SQL(
                        """
                        CREATE INDEX IF NOT EXISTS idx_chunks_content_tsv
                        ON {}.chunks
                        USING GIN (content_tsv)
                        """
                    ).format(
                        sql.Identifier(settings.POSTGRES_SCHEMA)
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

                logger.info("ensure_schema: before create table images")
                cur.execute(
                    sql.SQL(
                        """
                        CREATE TABLE IF NOT EXISTS {}.images (
                            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    
                            document_id BIGINT NOT NULL,
                            document_version_id BIGINT NOT NULL,
                            document_section_id BIGINT NOT NULL,
    
                            source_section_id BIGINT NOT NULL,
                            clause TEXT,
                            path TEXT,
                            page INTEGER,
                            bbox JSONB,
    
                            title TEXT,
                            caption TEXT,
                            description TEXT,
                            image_key TEXT,
    
                            metadata JSONB,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    
                            CONSTRAINT fk_images_document_section
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

                logger.info("ensure_schema: before create table extracted_tables")
                cur.execute(
                    sql.SQL(
                        """
                        CREATE TABLE IF NOT EXISTS {}.extracted_tables (
                            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    
                            document_id BIGINT NOT NULL,
                            document_version_id BIGINT NOT NULL,
                            document_section_id BIGINT NOT NULL,
    
                            source_section_id BIGINT NOT NULL,
                            clause TEXT,
                            path TEXT,
                            page INTEGER,
                            bbox JSONB,
    
                            title TEXT,
                            caption TEXT,
    
                            table_markdown TEXT,
                            table_json JSONB,
    
                            metadata JSONB,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    
                            CONSTRAINT fk_extracted_tables_document_section
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

                logger.info("ensure_schema: before create table formulas")
                cur.execute(
                    sql.SQL(
                        """
                        CREATE TABLE IF NOT EXISTS {}.formulas (
                            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    
                            document_id BIGINT NOT NULL,
                            document_version_id BIGINT NOT NULL,
                            document_section_id BIGINT NOT NULL,
    
                            source_section_id BIGINT NOT NULL,
                            clause TEXT,
                            path TEXT,
                            page INTEGER,
                            bbox JSONB,
    
                            title TEXT,
                            formula_text TEXT,
                            formula_latex TEXT,
                            formula_type TEXT,
    
                            metadata JSONB,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    
                            CONSTRAINT fk_formulas_document_section
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

                logger.info("ensure_schema: before create table formula_parameters")
                cur.execute(
                    sql.SQL(
                        """
                        CREATE TABLE IF NOT EXISTS {}.formula_parameters (
                            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    
                            formula_id BIGINT NOT NULL,
    
                            symbol TEXT NOT NULL,
                            name TEXT,
                            unit TEXT,
                            description TEXT,
    
                            metadata JSONB,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    
                            CONSTRAINT fk_formula_parameters_formula
                                FOREIGN KEY (formula_id)
                                REFERENCES {}.formulas(id)
                                ON DELETE CASCADE
                        )
                        """
                    ).format(
                        sql.Identifier(settings.POSTGRES_SCHEMA),
                        sql.Identifier(settings.POSTGRES_SCHEMA),
                    )
                )


            conn.commit()

        logger.info("ensure_schema: done")

# Конец создания схемы базы данных и таблиц

    def cleanup_document_index(
            self,
            request: BuildRequest,
    ) -> None:
        """
        Полностью очищает старый индекс документа перед новой индексацией.

        В RAG-хранилище хранится актуальный индекс документа,
        поэтому очистка выполняется по document_id, а не только
        по document_version_id.
        """
        document_id = request.metadata.document_id

        logger.info(
            "Cleaning old index for document_id=%s",
            document_id,
        )

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    DELETE FROM {settings.POSTGRES_SCHEMA}.formula_parameters
                    WHERE formula_id IN (
                        SELECT id
                        FROM {settings.POSTGRES_SCHEMA}.formulas
                        WHERE document_id = %s
                    )
                    """,
                    (document_id,),
                )

                for table_name in (
                    "formulas",
                    "extracted_tables",
                    "images",
                    "cross_references",
                    "chunks",
                    "document_sections",
                ):
                    cur.execute(
                        sql.SQL(
                            """
                            DELETE FROM {schema}.{table}
                            WHERE document_id = %s
                            """
                        ).format(
                            schema=sql.Identifier(settings.POSTGRES_SCHEMA),
                            table=sql.Identifier(table_name),
                        ),
                        (document_id,),
                    )

            conn.commit()

    def delete_document_index(
            self,
            document_id: int,
    ) -> int:
        """
        Удаляет индекс документа по document_id.

        Возвращает количество удалённых chunks.
        Используется API endpoint:
        DELETE /rag/build/{document_id}
        """
        logger.info(
            "Deleting index for document_id=%s",
            document_id,
        )

        deleted_chunks_count = 0

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    DELETE FROM {settings.POSTGRES_SCHEMA}.formula_parameters
                    WHERE formula_id IN (
                        SELECT id
                        FROM {settings.POSTGRES_SCHEMA}.formulas
                        WHERE document_id = %s
                    )
                    """,
                    (document_id,),
                )

                for table_name in (
                    "formulas",
                    "extracted_tables",
                    "images",
                    "cross_references",
                    "chunks",
                    "document_sections",
                ):
                    cur.execute(
                        sql.SQL(
                            """
                            DELETE FROM {schema}.{table}
                            WHERE document_id = %s
                            """
                        ).format(
                            schema=sql.Identifier(settings.POSTGRES_SCHEMA),
                            table=sql.Identifier(table_name),
                        ),
                        (document_id,),
                    )

                    if table_name == "chunks":
                        deleted_chunks_count = cur.rowcount

            conn.commit()

        return deleted_chunks_count

    def save_chunks(
            self,
            chunks: list[EmbeddedChunk],
            indexing_txn_id: str | None = None,
    ) -> None:
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
                            indexing_txn_id,
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
                            content_tsv,
                            metadata,
                            embedding
                        )
                        VALUES (
                            %s, %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, %s, %s, %s,
                            %s,
                            to_tsvector('russian'::regconfig, %s),
                            %s, %s
                        )
                        """,
                        (
                            item.chunk.document_id,
                            item.chunk.document_version_id,
                            indexing_txn_id,
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
                            path_ltree,
                            page,
                            bbox,
                            section_type,
                            metadata
                        )
                        VALUES (
                            %s, %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, %s, %s, %s, %s
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
                            self._to_ltree_path(section.path),
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

    def save_images(
            self,
            request: BuildRequest,
    ) -> None:
        logger.info(
            "Saving images for document_id=%s",
            request.metadata.document_id,
        )

        with self._connect() as conn:
            with conn.cursor() as cur:

                cur.execute(
                    f"""
                    DELETE FROM {settings.POSTGRES_SCHEMA}.images
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
                    for section_id, document_section_id
                    in cur.fetchall()
                }

                for section in request.sections:

                    if section.type != "image":
                        continue

                    document_section_id = (
                        section_id_to_db_id[section.section_id]
                    )

                    caption = (
                        section.content.get("caption")
                        if isinstance(section.content, dict)
                        else None
                    )

                    cur.execute(
                        f"""
                        INSERT INTO {settings.POSTGRES_SCHEMA}.images (
                            document_id,
                            document_version_id,
                            document_section_id,
                            source_section_id,
                            clause,
                            path,
                            page,
                            bbox,
                            title,
                            caption,
                            metadata
                        )
                        VALUES (
                            %s, %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, %s, %s
                        )
                        """,
                        (
                            request.metadata.document_id,
                            request.metadata.document_version_id,
                            document_section_id,
                            section.section_id,
                            section.clause,
                            section.path,
                            section.page,
                            json.dumps(section.bbox),
                            section.title,
                            caption,
                            json.dumps(section.content),
                        ),
                    )

            conn.commit()

    def _render_table_markdown(self, content: dict,) -> str | None:
        headers = content.get("headers")
        rows = content.get("rows")

        if not isinstance(headers, list) or not isinstance(rows, list):
            return None

        lines = [
            "| " + " | ".join(map(str, headers)) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
        ]

        for row in rows:
            if isinstance(row, list):
                lines.append(
                    "| " + " | ".join(map(str, row)) + " |"
                )

        return "\n".join(lines)


    def _to_ltree_path(self, path: str | None,) -> str | None:
        if not path:
            return None

        parts = path.split("/")

        normalized_parts = []

        for part in parts:
            value = (
                str(part)
                .strip()
                .lower()
                .replace(".", "_")
                .replace("-", "_")
            )

            if value and value[0].isdigit():
                value = f"p{value}"

            normalized_parts.append(value)

        return ".".join(normalized_parts)

    def save_extracted_tables(
            self,
            request: BuildRequest,
    ) -> None:
        logger.info(
            "Saving tables for document_id=%s",
            request.metadata.document_id,
        )

        with self._connect() as conn:
            with conn.cursor() as cur:

                cur.execute(
                    f"""
                    DELETE FROM {settings.POSTGRES_SCHEMA}.extracted_tables
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
                    for section_id, document_section_id
                    in cur.fetchall()
                }

                for section in request.sections:

                    if section.type != "table":
                        continue

                    document_section_id = (
                        section_id_to_db_id[section.section_id]
                    )

                    caption = (
                        section.content.get("caption")
                        if isinstance(section.content, dict)
                        else None
                    )

                    table_markdown = (
                        self._render_table_markdown(section.content)
                        if isinstance(section.content, dict)
                        else None
                    )

                    cur.execute(
                        f"""
                        INSERT INTO {settings.POSTGRES_SCHEMA}.extracted_tables (
                            document_id,
                            document_version_id,
                            document_section_id,
                            source_section_id,
                            clause,
                            path,
                            page,
                            bbox,
                            title,
                            caption,
                            table_markdown,
                            table_json,
                            metadata
                        )
                        VALUES (
                            %s, %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, %s, %s, %s, %s
                        )
                        """,
                        (
                            request.metadata.document_id,
                            request.metadata.document_version_id,
                            document_section_id,
                            section.section_id,
                            section.clause,
                            section.path,
                            section.page,
                            json.dumps(section.bbox),
                            section.title,
                            caption,
                            table_markdown,
                            json.dumps(section.content),  # table_json
                            json.dumps(section.content),  # metadata
                        ),
                    )

                conn.commit()

    def save_formulas(
            self,
            request: BuildRequest,
    ) -> None:
        logger.info(
            "Saving formulas for document_id=%s",
            request.metadata.document_id,
        )

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    DELETE FROM {settings.POSTGRES_SCHEMA}.formulas
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
                    for section_id, document_section_id
                    in cur.fetchall()
                }

                for section in request.sections:
                    if section.type != "formula":
                        continue

                    document_section_id = section_id_to_db_id.get(
                        section.section_id
                    )

                    if document_section_id is None:
                        raise ValueError(
                            "No document_section_id found for "
                            f"document_version_id={request.metadata.document_version_id}, "
                            f"section_id={section.section_id}"
                        )

                    content = (
                        section.content
                        if isinstance(section.content, dict)
                        else {}
                    )

                    cur.execute(
                        f"""
                        INSERT INTO {settings.POSTGRES_SCHEMA}.formulas (
                            document_id,
                            document_version_id,
                            document_section_id,
                            source_section_id,
                            clause,
                            path,
                            page,
                            bbox,
                            title,
                            formula_text,
                            formula_latex,
                            formula_type,
                            metadata
                        )
                        VALUES (
                            %s, %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, %s, %s, %s, %s
                        )
                        RETURNING id
                        """,
                        (
                            request.metadata.document_id,
                            request.metadata.document_version_id,
                            document_section_id,
                            section.section_id,
                            section.clause,
                            section.path,
                            section.page,
                            json.dumps(section.bbox),
                            section.title,
                            content.get("text"),
                            content.get("latex"),
                            content.get("formula_type"),
                            json.dumps(content),
                        ),
                    )

                    formula_id = cur.fetchone()[0]

                    parameters = content.get("parameters", [])

                    if not isinstance(parameters, list):
                        parameters = []

                    for param in parameters:
                        if not isinstance(param, dict):
                            continue

                        symbol = param.get("symbol")

                        if not symbol:
                            continue

                        cur.execute(
                            f"""
                            INSERT INTO {settings.POSTGRES_SCHEMA}.formula_parameters (
                                formula_id,
                                symbol,
                                name,
                                unit,
                                description,
                                metadata
                            )
                            VALUES (
                                %s, %s, %s,
                                %s, %s, %s
                            )
                            """,
                            (
                                formula_id,
                                symbol,
                                param.get("name"),
                                param.get("unit"),
                                param.get("description"),
                                json.dumps(param),
                            ),
                        )

            conn.commit()



