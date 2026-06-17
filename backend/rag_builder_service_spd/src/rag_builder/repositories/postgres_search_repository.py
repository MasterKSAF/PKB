# rag_builder_service_spd/src/rag_builder/repositories/postgres_search_repository.py

import psycopg
from psycopg import sql
import math

from rag_builder.core.config import settings
from rag_builder.core.logger import logger
from rag_builder.models.search import SearchChunkResult, SearchFilters


class PostgresSearchRepository:
    """
    Read-only repository for searching chunks in PostgreSQL.
    """

    def _connect(self):
        logger.info(
            "PostgreSQL search connect host=%s port=%s db=%s user=%s",
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

    def vector_search(
        self,
        query_embedding: list[float],
        top_k: int,
        filters: SearchFilters | None = None,
    ) -> list[SearchChunkResult]:
        embedding_literal = self._to_vector_literal(query_embedding)

        where_clauses = [sql.SQL("embedding IS NOT NULL")]
        params: list[object] = [
            embedding_literal,
            embedding_literal,
        ]

        if filters is not None:
            if filters.document_id is not None:
                where_clauses.append(sql.SQL("document_id = %s"))
                params.append(filters.document_id)

            if filters.document_version_id is not None:
                where_clauses.append(sql.SQL("document_version_id = %s"))
                params.append(filters.document_version_id)

            if filters.section_id is not None:
                where_clauses.append(sql.SQL("section_id = %s"))
                params.append(filters.section_id)

            if filters.chunk_type is not None:
                where_clauses.append(sql.SQL("chunk_type = %s"))
                params.append(filters.chunk_type)

        params.append(top_k)

        query = sql.SQL(
            """
            SELECT
                id AS chunk_id,
                document_id,
                document_version_id,
                document_section_id,
                section_id,
                clause,
                path,
                page,
                bbox,
                chunk_index,
                chunk_type,
                content,
                embedding <=> %s::vector AS distance
            FROM {schema}.chunks
            WHERE {where_clause}
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """
        ).format(
            schema=sql.Identifier(settings.POSTGRES_SCHEMA),
            where_clause=sql.SQL(" AND ").join(where_clauses),
        )

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()

        return [
            self._row_to_result(row)
            for row in rows
        ]

    def text_search(
            self,
            query_text: str,
            top_k: int,
            filters: SearchFilters | None = None,
    ) -> list[SearchChunkResult]:
        where_clauses = [
            sql.SQL("content ILIKE %s")
        ]
        params: list[object] = [
            f"%{query_text}%"
        ]

        if filters is not None:
            if filters.document_id is not None:
                where_clauses.append(sql.SQL("document_id = %s"))
                params.append(filters.document_id)

            if filters.document_version_id is not None:
                where_clauses.append(sql.SQL("document_version_id = %s"))
                params.append(filters.document_version_id)

            if filters.section_id is not None:
                where_clauses.append(sql.SQL("section_id = %s"))
                params.append(filters.section_id)

            if filters.chunk_type is not None:
                where_clauses.append(sql.SQL("chunk_type = %s"))
                params.append(filters.chunk_type)

        params.append(top_k)

        query = sql.SQL(
            """
            SELECT
                id AS chunk_id,
                document_id,
                document_version_id,
                document_section_id,
                section_id,
                clause,
                path,
                page,
                bbox,
                chunk_index,
                chunk_type,
                content,
                NULL AS distance
            FROM {schema}.chunks
            WHERE {where_clause}
            ORDER BY
                CASE
                    WHEN content ILIKE %s THEN 0
                    ELSE 1
                END,
                id
            LIMIT %s
            """
        ).format(
            schema=sql.Identifier(settings.POSTGRES_SCHEMA),
            where_clause=sql.SQL(" AND ").join(where_clauses),
        )

        params.insert(-1, f"%{query_text}%")

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()

        return [
            self._row_to_result_with_score(row, score=1.0)
            for row in rows
        ]

    def _row_to_result_with_score(
            self,
            row,
            score: float,
    ) -> SearchChunkResult:
        return SearchChunkResult(
            chunk_id=row[0],
            document_id=row[1],
            document_version_id=row[2],
            document_section_id=row[3],
            section_id=row[4],
            clause=row[5],
            path=row[6],
            page=row[7],
            bbox=row[8],
            chunk_index=row[9],
            chunk_type=row[10],
            content=row[11],
            distance=row[12],
            score=score,
        )

    def _row_to_result(self, row) -> SearchChunkResult:
        raw_distance = row[12]
        distance = float(raw_distance) if raw_distance is not None else None

        return SearchChunkResult(
            chunk_id=row[0],
            document_id=row[1],
            document_version_id=row[2],
            document_section_id=row[3],
            section_id=row[4],
            clause=row[5],
            path=row[6],
            page=row[7],
            bbox=row[8],
            chunk_index=row[9],
            chunk_type=row[10],
            content=row[11],
            distance=distance,
            score=self._distance_to_score(distance),
        )

    def _distance_to_score(self, distance: float | None) -> float:
        if distance is None:
            return 0.0

        if math.isnan(distance):
            return 0.0

        return 1.0 / (1.0 + distance)

    def _to_vector_literal(self, embedding: list[float]) -> str:
        return "[" + ",".join(str(value) for value in embedding) + "]"