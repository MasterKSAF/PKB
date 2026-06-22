-- Черновик структуры nsi.chunks
-- Не утверждено
-- Требует согласования с Knowledge Base

CREATE SCHEMA IF NOT EXISTS nsi;

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS nsi.chunks (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    document_id BIGINT NOT NULL,
    document_version_id BIGINT NOT NULL,
    section_id BIGINT NOT NULL,
    parent_id BIGINT,

    clause TEXT,
    path TEXT,

    page INTEGER,
    bbox JSONB,

    chunk_index INTEGER NOT NULL,
    chunk_type TEXT NOT NULL,

    content TEXT NOT NULL,
    metadata JSONB,

    embedding VECTOR(2048), -- Must match EMBEDDING_DIM

    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_chunks_document
    ON nsi.chunks(document_id);

CREATE INDEX idx_chunks_version
    ON nsi.chunks(document_version_id);