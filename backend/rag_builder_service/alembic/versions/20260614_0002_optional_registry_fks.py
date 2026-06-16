"""optional registry foreign keys for rag chunks

Revision ID: 20260614_0002
Revises: 20260528_0001
Create Date: 2026-06-14 23:59:00
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260614_0002"
down_revision = "20260528_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
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
                SELECT format_type(a.atttypid, a.atttypmod)
                INTO chunk_doc_type
                FROM pg_attribute a
                WHERE a.attrelid = 'rag.document_chunks'::regclass
                  AND a.attname = 'document_id'
                  AND NOT a.attisdropped;

                SELECT format_type(a.atttypid, a.atttypmod)
                INTO registry_doc_type
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
                   SELECT 1
                   FROM pg_constraint
                   WHERE conname = 'fk_rag_document_chunks_document_id'
               )
            THEN
                ALTER TABLE rag.document_chunks
                ADD CONSTRAINT fk_rag_document_chunks_document_id
                FOREIGN KEY (document_id)
                REFERENCES registry.documents(id);
            END IF;
        END
        $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF to_regclass('registry.document_sections') IS NOT NULL
               AND NOT EXISTS (
                   SELECT 1
                   FROM pg_constraint
                   WHERE conname = 'fk_rag_document_chunks_section_id'
               )
            THEN
                ALTER TABLE rag.document_chunks
                ADD CONSTRAINT fk_rag_document_chunks_section_id
                FOREIGN KEY (section_id)
                REFERENCES registry.document_sections(id);
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE IF EXISTS rag.document_chunks DROP CONSTRAINT IF EXISTS fk_rag_document_chunks_section_id")
    op.execute("ALTER TABLE IF EXISTS rag.document_chunks DROP CONSTRAINT IF EXISTS fk_rag_document_chunks_document_id")
