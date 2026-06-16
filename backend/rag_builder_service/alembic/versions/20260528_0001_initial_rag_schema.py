"""initial rag schema

Revision ID: 20260528_0001
Revises:
Create Date: 2026-05-28 00:00:01
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260528_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS rag")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "ltree"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS rag.document_chunks (
            id BIGSERIAL PRIMARY KEY,
            section_id BIGINT NOT NULL,
            document_id BIGINT NOT NULL,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            embedding VECTOR(1536),
            tsv TSVECTOR,
            strategy VARCHAR(32) NOT NULL,
            page INTEGER,
            bbox JSONB,
            confidence DOUBLE PRECISION,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("ALTER TABLE rag.document_chunks ADD COLUMN IF NOT EXISTS tsv TSVECTOR")
    op.execute("ALTER TABLE rag.document_chunks ADD COLUMN IF NOT EXISTS bbox JSONB")
    op.execute("ALTER TABLE rag.document_chunks ADD COLUMN IF NOT EXISTS confidence DOUBLE PRECISION")
    op.execute("ALTER TABLE rag.document_chunks ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT now()")
    op.execute("ALTER TABLE rag.document_chunks ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now()")
    op.execute("ALTER TABLE rag.document_chunks ALTER COLUMN created_at SET NOT NULL")
    op.execute("ALTER TABLE rag.document_chunks ALTER COLUMN updated_at SET NOT NULL")
    op.execute("ALTER TABLE rag.document_chunks ALTER COLUMN strategy TYPE VARCHAR(32)")
    op.execute("ALTER TABLE rag.document_chunks ALTER COLUMN strategy SET NOT NULL")
    op.execute("ALTER TABLE rag.document_chunks ALTER COLUMN content SET NOT NULL")
    op.execute("ALTER TABLE rag.document_chunks ALTER COLUMN chunk_index SET NOT NULL")
    op.execute("ALTER TABLE rag.document_chunks ALTER COLUMN document_id SET NOT NULL")
    op.execute("ALTER TABLE rag.document_chunks ALTER COLUMN id TYPE BIGINT")
    op.execute("ALTER TABLE rag.document_chunks ALTER COLUMN section_id TYPE BIGINT")
    op.execute("ALTER TABLE rag.document_chunks ALTER COLUMN document_id TYPE BIGINT USING document_id::bigint")
    op.execute("ALTER TABLE rag.document_chunks ALTER COLUMN embedding TYPE VECTOR(1536) USING NULL::VECTOR(1536)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_rag_doc_chunks_doc_id ON rag.document_chunks(document_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_rag_doc_chunks_tsv ON rag.document_chunks USING gin(tsv)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_rag_doc_chunks_embedding_ivfflat "
        "ON rag.document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS rag.ix_rag_doc_chunks_embedding_ivfflat")
    op.execute("DROP INDEX IF EXISTS rag.ix_rag_doc_chunks_tsv")
    op.execute("DROP INDEX IF EXISTS rag.ix_rag_doc_chunks_doc_id")
    op.execute("DROP TABLE IF EXISTS rag.document_chunks")
    op.execute("DROP EXTENSION IF EXISTS vector")
    op.execute("DROP SCHEMA IF EXISTS rag")
