"""consolidated rag schema (single base migration)

Revision ID: 20260623_0001
Revises:
Create Date: 2026-06-23 00:00:01

Смержены 5 исторических миграций в одну базовую:
- 20260528_0001 — initial rag schema
- 20260614_0002 — optional registry fks (исключены)
- 20260616_0003 — reconcile bigint and vector dim
- 20260622_0004 — add indexing_txn_id (включено)
- 20260622_0005 — reconcile vector dimension

Отличия от исторических миграций:
- UNIQUE(section_id, chunk_index) НЕ создаётся — ломает индексацию нескольких документов
- FK на registry НЕ создаются — опциональные и не обязательные для работы
"""

from __future__ import annotations

import os

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260623_0001"
down_revision = None
branch_labels = None
depends_on = None

EXPECTED_VECTOR_DIM = int(
    os.environ.get("VECTOR_DIMENSION", os.environ.get("EMBEDDING_DIM", "2048"))
)


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS rag")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS rag.document_chunks (
            id BIGSERIAL PRIMARY KEY,
            section_id BIGINT NOT NULL,
            document_id BIGINT NOT NULL,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            embedding VECTOR({dim}),
            tsv TSVECTOR,
            strategy VARCHAR(32) NOT NULL,
            page INTEGER,
            bbox JSONB,
            confidence FLOAT,
            indexing_txn_id UUID,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """.format(dim=EXPECTED_VECTOR_DIM)
    )
    # Индексы
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_rag_doc_chunks_doc_id "
        "ON rag.document_chunks (document_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_rag_doc_chunks_tsv "
        "ON rag.document_chunks USING GIN (tsv)"
    )
    # Удаляем старый IVFFlat индекс, если он был создан предыдущими миграциями
    op.execute(
        "DROP INDEX IF EXISTS rag.ix_rag_doc_chunks_embedding_ivfflat"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_rag_doc_chunks_embedding_hnsw "
        "ON rag.document_chunks USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS rag.ix_rag_doc_chunks_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS rag.ix_rag_doc_chunks_embedding_ivfflat")
    op.execute("DROP INDEX IF EXISTS rag.ix_rag_doc_chunks_tsv")
    op.execute("DROP INDEX IF EXISTS rag.ix_rag_doc_chunks_doc_id")
    op.execute("DROP TABLE IF EXISTS rag.document_chunks")
