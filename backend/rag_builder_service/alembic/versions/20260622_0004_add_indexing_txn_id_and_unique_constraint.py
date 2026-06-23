"""add indexing_txn_id column and UNIQUE(section_id, chunk_index)

Revision ID: 20260622_0004
Revises: 20260616_0003
Create Date: 2026-06-22 00:00:00
"""

from __future__ import annotations

from alembic import op

revision = "20260622_0004"
down_revision = "20260616_0003"
branch_labels = None
depends_on = None



def upgrade() -> None:
    # DB-18: add indexing_txn_id UUID column
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'rag'
                  AND table_name = 'document_chunks'
                  AND column_name = 'indexing_txn_id'
            ) THEN
                ALTER TABLE rag.document_chunks
                ADD COLUMN indexing_txn_id UUID;
            END IF;
        END $$;
        """
    )

    # DB-4: add UNIQUE(section_id, chunk_index) if not exists
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'uq_rag_chunks_section_chunk'
            ) THEN
                -- Clean up any duplicates before adding constraint
                DELETE FROM rag.document_chunks
                WHERE ctid NOT IN (
                    SELECT MIN(ctid)
                    FROM rag.document_chunks
                    GROUP BY section_id, chunk_index
                );
                ALTER TABLE rag.document_chunks
                ADD CONSTRAINT uq_rag_chunks_section_chunk
                UNIQUE (section_id, chunk_index);
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE IF EXISTS rag.document_chunks DROP CONSTRAINT IF EXISTS uq_rag_chunks_section_chunk")
    op.execute("ALTER TABLE IF EXISTS rag.document_chunks DROP COLUMN IF EXISTS indexing_txn_id")
