"""reconcile document_id to BIGINT and embedding to correct vector dimension

Revision ID: 20260616_0003
Revises: 20260614_0002
Create Date: 2026-06-16 00:00:00

Fixes tables created by older migrations that used UUID for document_id
or wrong vector dimension.
Runs safely on already-correct schemas (idempotent).
"""

from __future__ import annotations

import os

from alembic import op

revision = "20260616_0003"
down_revision = "20260614_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    vector_dim = int(os.environ.get("VECTOR_DIMENSION", os.environ.get("EMBEDDING_DIM", "2048")))
    expected_vector_type = f"vector({vector_dim})"

    # 1. Convert document_id to BIGINT if it is still UUID (or any non-bigint type)
    op.execute(
        """
        DO $$
        DECLARE
            col_type text;
        BEGIN
            SELECT format_type(a.atttypid, a.atttypmod) INTO col_type
            FROM pg_attribute a
            WHERE a.attrelid = 'rag.document_chunks'::regclass
              AND a.attname = 'document_id'
              AND NOT a.attisdropped;

            IF col_type IS NOT NULL AND col_type <> 'bigint' THEN
                -- Drop FK that may reference uuid-typed registry.documents
                ALTER TABLE rag.document_chunks
                    DROP CONSTRAINT IF EXISTS fk_rag_document_chunks_document_id;

                -- Wipe existing data: UUID values cannot be cast to BIGINT sensibly.
                -- In a fresh / test DB there is nothing important here.
                -- In production this migration should be run on an empty rag schema.
                DELETE FROM rag.document_chunks;

                ALTER TABLE rag.document_chunks
                    ALTER COLUMN document_id TYPE BIGINT USING 0;
            END IF;
        END $$;
        """
    )

    # 2. Convert section_id to BIGINT if needed
    op.execute(
        """
        DO $$
        DECLARE
            col_type text;
        BEGIN
            SELECT format_type(a.atttypid, a.atttypmod) INTO col_type
            FROM pg_attribute a
            WHERE a.attrelid = 'rag.document_chunks'::regclass
              AND a.attname = 'section_id'
              AND NOT a.attisdropped;

            IF col_type IS NOT NULL AND col_type <> 'bigint' THEN
                ALTER TABLE rag.document_chunks
                    DROP CONSTRAINT IF EXISTS fk_rag_document_chunks_section_id;
                ALTER TABLE rag.document_chunks
                    ALTER COLUMN section_id TYPE BIGINT USING 0;
            END IF;
        END $$;
        """
    )

    # 3. Re-create embedding column with correct dimension (from VECTOR_DIMENSION env).
    expected = expected_vector_type
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
                CREATE INDEX IF NOT EXISTS ix_rag_doc_chunks_embedding_ivfflat
                    ON rag.document_chunks
                    USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100);
            END IF;
        END $$;
        """
    )

    # 4. Re-apply FK to registry.documents only if types are now compatible (both bigint)
    op.execute(
        """
        DO $$
        DECLARE
            registry_documents_regclass regclass;
            chunk_doc_type text;
            registry_doc_type text;
        BEGIN
            registry_documents_regclass := to_regclass('registry.documents');

            IF registry_documents_regclass IS NOT NULL THEN
                SELECT format_type(a.atttypid, a.atttypmod) INTO chunk_doc_type
                FROM pg_attribute a
                WHERE a.attrelid = 'rag.document_chunks'::regclass
                  AND a.attname = 'document_id'
                  AND NOT a.attisdropped;

                SELECT format_type(a.atttypid, a.atttypmod) INTO registry_doc_type
                FROM pg_attribute a
                WHERE a.attrelid = registry_documents_regclass
                  AND a.attname = 'id'
                  AND NOT a.attisdropped;
            END IF;

            IF registry_documents_regclass IS NOT NULL
               AND chunk_doc_type IS NOT NULL
               AND registry_doc_type IS NOT NULL
               AND chunk_doc_type = registry_doc_type
               AND NOT EXISTS (
                   SELECT 1 FROM pg_constraint
                   WHERE conname = 'fk_rag_document_chunks_document_id'
               )
            THEN
                ALTER TABLE rag.document_chunks
                ADD CONSTRAINT fk_rag_document_chunks_document_id
                FOREIGN KEY (document_id) REFERENCES registry.documents(id);
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    # Intentionally left empty: converting back to UUID or smaller vector is destructive
    pass
