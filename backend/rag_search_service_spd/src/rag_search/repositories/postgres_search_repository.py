import math

import psycopg
from psycopg import sql

from rag_search.core.config import settings
from rag_search.models.search import (
    SearchChunkResult,
    SearchContextItem,
    SearchFilters,
)


class PostgresSearchRepository:
    """Read-only repository for searching indexed chunks in PostgreSQL."""

    def _connect(self):
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

    def vector_search(
        self,
        query_embedding: list[float],
        top_k: int,
        filters: SearchFilters | None = None,
    ) -> list[SearchChunkResult]:
        embedding_literal = self._to_vector_literal(query_embedding)

        where_clauses = [sql.SQL("embedding IS NOT NULL")]
        params: list[object] = [embedding_literal]

        self._append_filters(where_clauses, params, filters)

        params.append(embedding_literal)
        params.append(top_k)

        query = sql.SQL(
            """
            SELECT
                id AS chunk_id,
                document_id,
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

        return [self._row_to_result(row) for row in rows]

    def text_search(
        self,
        query_text: str,
        top_k: int,
        filters: SearchFilters | None = None,
    ) -> list[SearchChunkResult]:
        where_clauses = [
            sql.SQL(
                """
                content_tsv @@ websearch_to_tsquery('russian', %s)
                """
            )
        ]
        params: list[object] = [
            query_text,
            query_text,
        ]

        self._append_filters(where_clauses, params, filters)

        params.append(top_k)

        query = sql.SQL(
            """
            SELECT
                id AS chunk_id,
                document_id,
                document_section_id,
                section_id,
                clause,
                path,
                page,
                bbox,
                chunk_index,
                chunk_type,
                content,
                NULL AS distance,
                ts_rank_cd(
                    content_tsv,
                    websearch_to_tsquery('russian', %s)
                ) AS rank_score
            FROM {schema}.chunks
            WHERE {where_clause}
            ORDER BY rank_score DESC, id
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
            self._row_to_result_with_score(
                row,
                score=float(row[12] or 0.0),
                mode="sparse",
            )
            for row in rows
        ]

    def expand_context(
        self,
        document_section_id: int,
        child_limit: int = 10,
    ) -> list[SearchContextItem]:
        query = sql.SQL(
            """
            WITH current_section AS (
                SELECT
                    id,
                    document_id,
                    path_ltree
                FROM {schema}.document_sections
                WHERE id = %s
            ),
            parent_section AS (
                SELECT
                    'parent' AS relation,
                    s.id AS document_section_id,
                    s.section_id,
                    s.parent_id,
                    s.clause,
                    s.title,
                    s.path,
                    s.page,
                    s.section_type,
                    s.metadata -> 'raw_content' AS content
                FROM {schema}.document_sections s
                JOIN current_section c
                    ON s.document_id = c.document_id
                WHERE
                    c.path_ltree IS NOT NULL
                    AND s.path_ltree IS NOT NULL
                    AND s.path_ltree @> c.path_ltree
                    AND s.path_ltree <> c.path_ltree
                    AND nlevel(s.path_ltree) = nlevel(c.path_ltree) - 1
                LIMIT 1
            ),
            child_sections AS (
                SELECT
                    'child' AS relation,
                    s.id AS document_section_id,
                    s.section_id,
                    s.parent_id,
                    s.clause,
                    s.title,
                    s.path,
                    s.page,
                    s.section_type,
                    s.metadata -> 'raw_content' AS content
                FROM {schema}.document_sections s
                JOIN current_section c
                    ON s.document_id = c.document_id
                WHERE
                    c.path_ltree IS NOT NULL
                    AND s.path_ltree IS NOT NULL
                    AND s.path_ltree <@ c.path_ltree
                    AND s.path_ltree <> c.path_ltree
                    AND nlevel(s.path_ltree) = nlevel(c.path_ltree) + 1
                ORDER BY s.path_ltree::text
                LIMIT %s
            )
            SELECT * FROM parent_section
            UNION ALL
            SELECT * FROM child_sections
            """
        ).format(
            schema=sql.Identifier(settings.POSTGRES_SCHEMA),
        )

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    query,
                    (
                        document_section_id,
                        child_limit,
                    ),
                )
                rows = cur.fetchall()

        return [self._row_to_context_item(row) for row in rows]

    def _append_filters(
        self,
        where_clauses: list,
        params: list[object],
        filters: SearchFilters | None,
    ) -> None:
        if filters is None:
            return

        if filters.document_id is not None:
            where_clauses.append(sql.SQL("document_id = %s"))
            params.append(filters.document_id)

        if filters.section_id is not None:
            where_clauses.append(sql.SQL("section_id = %s"))
            params.append(filters.section_id)

        if filters.chunk_type is not None:
            where_clauses.append(sql.SQL("chunk_type = %s"))
            params.append(filters.chunk_type)

    def _row_to_context_item(self, row) -> SearchContextItem:
        return SearchContextItem(
            relation=row[0],
            document_section_id=row[1],
            section_id=row[2],
            parent_id=row[3],
            clause=row[4],
            title=row[5],
            path=row[6],
            page=row[7],
            section_type=row[8],
            content=row[9],
        )

    def _row_to_result_with_score(
        self,
        row,
        score: float,
        mode: str | None = None,
    ) -> SearchChunkResult:
        return SearchChunkResult(
            chunk_id=row[0],
            document_id=row[1],
            document_section_id=row[2],
            section_id=row[3],
            clause=row[4],
            path=row[5],
            page=row[6],
            bbox=row[7],
            chunk_index=row[8],
            chunk_type=row[9],
            content=row[10],
            distance=row[11],
            score=score,
            mode=mode,
        )

    def _row_to_result(self, row) -> SearchChunkResult:
        raw_distance = row[11]
        distance = (
            float(raw_distance)
            if raw_distance is not None
            else None
        )

        return SearchChunkResult(
            chunk_id=row[0],
            document_id=row[1],
            document_section_id=row[2],
            section_id=row[3],
            clause=row[4],
            path=row[5],
            page=row[6],
            bbox=row[7],
            chunk_index=row[8],
            chunk_type=row[9],
            content=row[10],
            distance=distance,
            score=self._distance_to_score(distance),
            mode="dense",
        )

    def _distance_to_score(self, distance: float | None) -> float:
        if distance is None:
            return 0.0

        if math.isnan(distance):
            return 0.0

        return 1.0 / (1.0 + distance)

    def _to_vector_literal(self, embedding: list[float]) -> str:
        return "[" + ",".join(str(value) for value in embedding) + "]"
