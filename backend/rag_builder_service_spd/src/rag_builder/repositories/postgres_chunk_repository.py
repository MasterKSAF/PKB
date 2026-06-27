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

    def _embedding_dim_sql(self) -> sql.SQL:
        """
        Returns EMBEDDING_DIM as a safe SQL fragment for pgvector type DDL.

        This method validates configuration only. Runtime schema creation is
        managed by Alembic and must not be performed by repository startup code.
        """
        embedding_dim = settings.EMBEDDING_DIM

        if embedding_dim <= 0:
            raise ValueError("EMBEDDING_DIM must be a positive integer")

        if embedding_dim > 4000:
            raise ValueError(
                "EMBEDDING_DIM must be less than or equal to 4000 "
                "because HNSW halfvec index supports up to 4000 dimensions"
            )

        return sql.SQL(str(embedding_dim))

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

    def _embedding_halfvec_dim_sql(self) -> sql.SQL:
        embedding_dim = int(settings.EMBEDDING_DIM)

        if embedding_dim <= 0:
            raise ValueError(
                f"Invalid EMBEDDING_DIM={embedding_dim}. "
                "EMBEDDING_DIM must be a positive integer."
            )

        if embedding_dim > 4000:
            raise ValueError(
                f"Invalid EMBEDDING_DIM={embedding_dim}. "
                "HNSW halfvec index supports up to 4000 dimensions."
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

    def mark_stale_indexing_jobs_failed(
        self,
        stale_after_seconds: int,
    ) -> int:
        if stale_after_seconds <= 0:
            return 0

        stale_error = {
            "code": "INDEXING_JOB_STALE",
            "message": "Indexing job marked as failed after stale timeout",
            "stale_after_seconds": stale_after_seconds,
        }

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL(
                        """
                        UPDATE {schema}.indexing_jobs
                        SET
                            status = 'failed',
                            errors = errors || %s::jsonb,
                            updated_at = now()
                        WHERE status IN ('pending_index', 'indexing')
                          AND updated_at < now() - (%s * interval '1 second')
                        """
                    ).format(
                        schema=sql.Identifier(settings.POSTGRES_SCHEMA),
                    ),
                    (
                        json.dumps([stale_error]),
                        stale_after_seconds,
                    ),
                )

                marked_count = cur.rowcount

            conn.commit()

        return marked_count


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

    def count_active_indexing_jobs(
        self,
        stale_after_seconds: int,
    ) -> int:
        if stale_after_seconds <= 0:
            return 0

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL(
                        """
                        SELECT count(*)
                        FROM {schema}.indexing_jobs
                        WHERE status IN ('pending_index', 'indexing')
                          AND updated_at >= now() - (%s * interval '1 second')
                        """
                    ).format(
                        schema=sql.Identifier(settings.POSTGRES_SCHEMA),
                    ),
                    (stale_after_seconds,),
                )

                row = cur.fetchone()

        return int(row[0])


    def get_active_indexing_job_for_document(
        self,
        document_id: int,
        stale_after_seconds: int,
    ) -> dict | None:
        if stale_after_seconds <= 0:
            return None

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL(
                        """
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
                        FROM {schema}.indexing_jobs
                        WHERE document_id = %s
                          AND status IN ('pending_index', 'indexing')
                          AND updated_at >= now() - (%s * interval '1 second')
                        ORDER BY created_at DESC, id DESC
                        LIMIT 1
                        """
                    ).format(
                        schema=sql.Identifier(settings.POSTGRES_SCHEMA),
                    ),
                    (
                        document_id,
                        stale_after_seconds,
                    ),
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


    def assert_schema_ready(self) -> None:
        """
        Checks that the database schema has already been initialized by Alembic.

        RAG Builder runtime must not create or mutate schema objects. Run:
        python -m alembic -c alembic.ini upgrade head
        before starting the service.
        """
        required_tables = (
            "indexing_jobs",
            "document_sections",
            "chunks",
            "cross_references",
            "images",
            "extracted_tables",
            "formulas",
            "formula_parameters",
        )
        required_extensions = (
            "vector",
            "ltree",
        )

        logger.info("assert_schema_ready: start")

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = %s
                      AND table_name = ANY(%s)
                    """,
                    (settings.POSTGRES_SCHEMA, list(required_tables)),
                )
                existing_tables = {row[0] for row in cur.fetchall()}
                missing_tables = sorted(set(required_tables) - existing_tables)

                if missing_tables:
                    raise RuntimeError(
                        "Database schema is not initialized or incomplete. "
                        f"Missing tables in schema {settings.POSTGRES_SCHEMA!r}: "
                        f"{', '.join(missing_tables)}. "
                        "Run: python -m alembic -c alembic.ini upgrade head"
                    )

                cur.execute(
                    """
                    SELECT extname
                    FROM pg_extension
                    WHERE extname = ANY(%s)
                    """,
                    (list(required_extensions),),
                )
                existing_extensions = {row[0] for row in cur.fetchall()}
                missing_extensions = sorted(
                    set(required_extensions) - existing_extensions
                )

                if missing_extensions:
                    raise RuntimeError(
                        "Database schema dependencies are not initialized. "
                        f"Missing PostgreSQL extensions: "
                        f"{', '.join(missing_extensions)}. "
                        "Run: python -m alembic -c alembic.ini upgrade head"
                    )

        logger.info("assert_schema_ready: done")

    def ensure_schema(self) -> None:
        """
        Backward-compatible wrapper.

        The schema is managed by Alembic migrations. This method intentionally
        does not run DDL anymore.
        """
        logger.warning(
            "ensure_schema() is deprecated and no longer runs DDL; "
            "use assert_schema_ready()"
        )
        self.assert_schema_ready()

    def cleanup_document_index(
            self,
            request: BuildRequest,
    ) -> None:
        """
        Полностью очищает старый индекс документа перед новой индексацией.

        В RAG-хранилище хранится актуальный индекс документа,
        поэтому очистка выполняется по document_id, а не только
        по document_id.
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
                document_id = chunks[0].chunk.document_id

                cur.execute(
                    f"""
                    DELETE FROM {settings.POSTGRES_SCHEMA}.chunks
                    WHERE document_id = %s
                    """,
                    (document_id,),
                )

                cur.execute(
                    f"""
                    SELECT section_id, id
                    FROM {settings.POSTGRES_SCHEMA}.document_sections
                    WHERE document_id = %s
                    """,
                    (document_id,),
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
                            f"document_id={document_id}, "
                            f"section_id={item.chunk.section_id}"
                        )

                    cur.execute(
                        f"""
                        INSERT INTO {settings.POSTGRES_SCHEMA}.chunks (
                            document_id,
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
                            to_tsvector('russian'::regconfig, %s),
                            %s, %s
                        )
                        """,
                        (
                            item.chunk.document_id,
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
                    WHERE document_id = %s
                    """,
                    (request.metadata.document_id,),
                )

                for section in request.sections:
                    cur.execute(
                        f"""
                        INSERT INTO {settings.POSTGRES_SCHEMA}.document_sections (
                            document_id,
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
                            %s, %s, %s, %s
                        )
                        """,
                        (
                            request.metadata.document_id,
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
                    WHERE document_id = %s
                    """,
                    (request.metadata.document_id,),
                )

                cur.execute(
                    f"""
                    SELECT section_id, id
                    FROM {settings.POSTGRES_SCHEMA}.document_sections
                    WHERE document_id = %s
                    """,
                    (request.metadata.document_id,),
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
                            f"document_id={request.metadata.document_id}, "
                            f"section_id={section.section_id}"
                        )

                    for ref in section.references:
                        cur.execute(
                            f"""
                            INSERT INTO {settings.POSTGRES_SCHEMA}.cross_references (
                                document_id,
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
                                %s, %s, %s
                            )
                            """,
                            (
                                request.metadata.document_id,
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
                    WHERE document_id = %s
                    """,
                    (request.metadata.document_id,),
                )

                cur.execute(
                    f"""
                    SELECT section_id, id
                    FROM {settings.POSTGRES_SCHEMA}.document_sections
                    WHERE document_id = %s
                    """,
                    (request.metadata.document_id,),
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
                            %s, %s
                        )
                        """,
                        (
                            request.metadata.document_id,
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
                    WHERE document_id = %s
                    """,
                    (request.metadata.document_id,),
                )

                cur.execute(
                    f"""
                    SELECT section_id, id
                    FROM {settings.POSTGRES_SCHEMA}.document_sections
                    WHERE document_id = %s
                    """,
                    (request.metadata.document_id,),
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
                            %s, %s, %s, %s
                        )
                        """,
                        (
                            request.metadata.document_id,
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
                    WHERE document_id = %s
                    """,
                    (request.metadata.document_id,),
                )

                cur.execute(
                    f"""
                    SELECT section_id, id
                    FROM {settings.POSTGRES_SCHEMA}.document_sections
                    WHERE document_id = %s
                    """,
                    (request.metadata.document_id,),
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
                            f"document_id={request.metadata.document_id}, "
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
                            %s, %s, %s, %s
                        )
                        RETURNING id
                        """,
                        (
                            request.metadata.document_id,
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
