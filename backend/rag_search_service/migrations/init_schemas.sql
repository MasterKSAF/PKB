-- =============================================================================
-- Инициализация схем для RAG Search Service (тестовая среда)
-- В продакшене эти таблицы уже существуют в общей БД
-- =============================================================================

-- Создаем расширения
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS ltree;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Создаем схемы (соответствует ТЗ: registry + rag)
CREATE SCHEMA IF NOT EXISTS registry;
CREATE SCHEMA IF NOT EXISTS rag;

-- =============================================================================
-- registry: реестр документов и секций
-- =============================================================================

-- Таблица документов (метаданные)
CREATE TABLE IF NOT EXISTS registry.documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_code TEXT,
    title TEXT NOT NULL,
    document_type TEXT,
    adoption_date DATE,
    validity_status TEXT DEFAULT 'active',
    era TEXT DEFAULT 'CURRENT',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reg_docs_document_type
    ON registry.documents(document_type);
CREATE INDEX IF NOT EXISTS idx_reg_docs_validity
    ON registry.documents(validity_status);

-- Иерархия разделов документов
CREATE TABLE IF NOT EXISTS registry.document_sections (
    id BIGSERIAL PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES registry.documents(id) ON DELETE CASCADE,
    parent_id BIGINT REFERENCES registry.document_sections(id) ON DELETE SET NULL,
    clause TEXT NOT NULL,
    title TEXT,
    level INT NOT NULL DEFAULT 1,
    path LTREE NOT NULL,
    page INT,
    bbox JSONB,
    type VARCHAR NOT NULL DEFAULT 'section',
    content JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT valid_ltree_path CHECK (
        path::TEXT ~ '^[A-Za-z0-9_]+(\.[A-Za-z0-9_]+)*$'
    )
);

CREATE INDEX IF NOT EXISTS idx_reg_sections_path
    ON registry.document_sections USING GIST (path);
CREATE INDEX IF NOT EXISTS idx_reg_sections_document
    ON registry.document_sections(document_id);

-- =============================================================================
-- rag: чанки с векторным и полнотекстовым поиском
-- =============================================================================

-- Текстовые чанки с векторным и полнотекстовым поиском
CREATE TABLE IF NOT EXISTS rag.document_chunks (
    id BIGSERIAL PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES registry.documents(id) ON DELETE CASCADE,
    section_id BIGINT REFERENCES registry.document_sections(id) ON DELETE SET NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1024),
    tsv TSVECTOR,
    page INT,
    chunk_index INT,
    chunk_strategy TEXT,
    bbox JSONB,
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    tenant_id TEXT NOT NULL DEFAULT 'default',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chunks_document
    ON rag.document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_section
    ON rag.document_chunks(section_id);

-- GIN-индекс для полнотекстового поиска
CREATE INDEX IF NOT EXISTS idx_chunks_tsv
    ON rag.document_chunks USING GIN (tsv);

-- HNSW-индекс для векторного поиска
CREATE INDEX IF NOT EXISTS idx_chunks_embedding
    ON rag.document_chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Триггер автообновления tsvector при INSERT/UPDATE
DROP TRIGGER IF EXISTS trg_chunks_tsv_update ON rag.document_chunks;
CREATE TRIGGER trg_chunks_tsv_update
    BEFORE INSERT OR UPDATE ON rag.document_chunks
    FOR EACH ROW
    EXECUTE FUNCTION tsvector_update_trigger(tsv, 'pg_catalog.russian', content);