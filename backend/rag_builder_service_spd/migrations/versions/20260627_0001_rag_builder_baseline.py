"""RAG Builder SPD baseline schema.

Revision ID: 20260627_0001
Revises:
Create Date: 2026-06-27
"""

from __future__ import annotations

import os
import re

from alembic import op


revision = "20260627_0001"
down_revision = None
branch_labels = None
depends_on = None


_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _schema() -> str:
    value = os.getenv("POSTGRES_SCHEMA", "nsi")

    if not _IDENTIFIER_RE.match(value):
        raise ValueError(f"Invalid POSTGRES_SCHEMA={value!r}")

    return value


def _embedding_dim() -> int:
    value = int(os.getenv("EMBEDDING_DIM", "2048"))

    if value <= 0:
        raise ValueError(f"Invalid EMBEDDING_DIM={value}")

    if value > 4000:
        raise ValueError(
            f"Invalid EMBEDDING_DIM={value}. "
            "HNSW halfvec index supports up to 4000 dimensions."
        )

    return value


def upgrade() -> None:
    schema = _schema()
    embedding_dim = _embedding_dim()

    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS ltree")
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")

    op.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {schema}.indexing_jobs (
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
    )

    op.execute(
        f"""
        CREATE INDEX IF NOT EXISTS idx_indexing_jobs_document_id
        ON {schema}.indexing_jobs(document_id)
        """
    )

    op.execute(
        f"""
        CREATE INDEX IF NOT EXISTS idx_indexing_jobs_status
        ON {schema}.indexing_jobs(status)
        """
    )

    op.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {schema}.document_sections(
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            document_id BIGINT NOT NULL,
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
            UNIQUE(document_id, section_id)
        )
        """
    )

    op.execute(
        f"""
        CREATE INDEX IF NOT EXISTS idx_document_sections_ltree
        ON {schema}.document_sections
        USING GIST(path_ltree)
        """
    )

    op.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {schema}.chunks (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            document_id BIGINT NOT NULL,
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
    )

    op.execute(
        f"""
        ALTER TABLE {schema}.chunks
        ADD COLUMN IF NOT EXISTS indexing_txn_id UUID
        """
    )

    op.execute(
        f"""
        ALTER TABLE {schema}.chunks
        ALTER COLUMN embedding TYPE VECTOR({embedding_dim})
        """
    )

    op.execute(
        f"""
        CREATE INDEX IF NOT EXISTS idx_chunks_indexing_txn_id
        ON {schema}.chunks(indexing_txn_id)
        """
    )

    op.execute(
        f"""
        CREATE INDEX IF NOT EXISTS idx_chunks_content_tsv
        ON {schema}.chunks
        USING GIN (content_tsv)
        """
    )

    op.execute(
        f"""
        DROP INDEX IF EXISTS {schema}.idx_chunks_embedding_hnsw_halfvec
        """
    )

    op.execute(
        f"""
        CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw_halfvec
        ON {schema}.chunks
        USING hnsw ((embedding::halfvec({embedding_dim})) halfvec_cosine_ops)
        WHERE embedding IS NOT NULL
        """
    )

    op.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {schema}.cross_references (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

            document_id BIGINT NOT NULL,
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
                REFERENCES {schema}.document_sections(id)
                ON DELETE CASCADE
        )
        """
    )

    op.execute(
        f"""
        CREATE INDEX IF NOT EXISTS idx_cross_references_doc
        ON {schema}.cross_references(document_id)
        """
    )

    op.execute(
        f"""
        CREATE INDEX IF NOT EXISTS idx_cross_references_target
        ON {schema}.cross_references(target_doc_code)
        """
    )

    op.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {schema}.images (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

            document_id BIGINT NOT NULL,
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
                REFERENCES {schema}.document_sections(id)
                ON DELETE CASCADE
        )
        """
    )

    op.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {schema}.extracted_tables (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

            document_id BIGINT NOT NULL,
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
                REFERENCES {schema}.document_sections(id)
                ON DELETE CASCADE
        )
        """
    )

    op.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {schema}.formulas (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

            document_id BIGINT NOT NULL,
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
                REFERENCES {schema}.document_sections(id)
                ON DELETE CASCADE
        )
        """
    )

    op.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {schema}.formula_parameters (
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
                REFERENCES {schema}.formulas(id)
                ON DELETE CASCADE
        )
        """
    )


def downgrade() -> None:
    schema = _schema()

    op.execute(f"DROP TABLE IF EXISTS {schema}.formula_parameters CASCADE")
    op.execute(f"DROP TABLE IF EXISTS {schema}.formulas CASCADE")
    op.execute(f"DROP TABLE IF EXISTS {schema}.extracted_tables CASCADE")
    op.execute(f"DROP TABLE IF EXISTS {schema}.images CASCADE")
    op.execute(f"DROP TABLE IF EXISTS {schema}.cross_references CASCADE")
    op.execute(f"DROP TABLE IF EXISTS {schema}.chunks CASCADE")
    op.execute(f"DROP TABLE IF EXISTS {schema}.document_sections CASCADE")
    op.execute(f"DROP TABLE IF EXISTS {schema}.indexing_jobs CASCADE")
