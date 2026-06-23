"""reconcile embedding vector dimension to 2048 (Qwen3)

Revision ID: 20260622_0005
Revises: 20260622_0004
Create Date: 2026-06-22 23:59:00
"""

from __future__ import annotations

import os

from alembic import op

revision = "20260622_0005"
down_revision = "20260622_0004"
branch_labels = None
depends_on = None

EXPECTED_VECTOR_DIM = int(
    os.environ.get("VECTOR_DIMENSION", os.environ.get("EMBEDDING_DIM", "2048"))
)


def upgrade() -> None:
    expected = f"vector({EXPECTED_VECTOR_DIM})"
    op.execute(
        f"""
        DO $$
        DECLARE
            col_type text;
        BEGIN
            SELECT format_type(a.atttypid, a.atttypmod) INTO col_type
            FROM pg_attribute a
            WHERE a.attrelid = 'rag.document_chunks'::regclass
              AND a.attname = 'embedding'
              AND NOT a.attisdropped;

            IF col_type IS NOT NULL AND col_type <> '{expected}' THEN
                DROP INDEX IF EXISTS rag.ix_rag_doc_chunks_embedding_ivfflat;
                ALTER TABLE rag.document_chunks DROP COLUMN embedding;
                ALTER TABLE rag.document_chunks ADD COLUMN embedding {expected};
                -- Note: ivfflat index not recreated here because pgvector limits
                -- ivfflat to 2000 dims in standard builds. Create it manually:
                -- CREATE INDEX ON rag.document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    # Intentionally no-op: reverting vector dimension is destructive
    pass
