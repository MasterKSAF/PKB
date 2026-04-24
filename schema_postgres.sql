-- PKB Neuroassistant (MVP) Postgres schema
-- Creates tables for documents and ingestion runs metadata.
--
-- Usage:
--   psql "$DATABASE_URL" -f schema_postgres.sql

BEGIN;

CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL,
    filename TEXT NOT NULL,
    content_type TEXT NULL,
    sha256 TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    metadata JSONB NOT NULL,
    status TEXT NOT NULL,
    latest_ingestion_id TEXT NULL
);

CREATE INDEX IF NOT EXISTS idx_documents_status
    ON documents (status);

CREATE INDEX IF NOT EXISTS idx_documents_sha256
    ON documents (sha256);

CREATE TABLE IF NOT EXISTS ingestion_runs (
    ingestion_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL,
    classification JSONB NULL,
    errors JSONB NOT NULL DEFAULT '[]'::jsonb,
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_ingestion_runs_document_id
    ON ingestion_runs (document_id);

CREATE INDEX IF NOT EXISTS idx_ingestion_runs_status
    ON ingestion_runs (status);

-- Optional FK (kept NOT VALID to avoid blocking if you import runs first)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_ingestion_runs_document'
    ) THEN
        ALTER TABLE ingestion_runs
            ADD CONSTRAINT fk_ingestion_runs_document
            FOREIGN KEY (document_id)
            REFERENCES documents (document_id)
            NOT VALID;
    END IF;
END $$;

COMMIT;

