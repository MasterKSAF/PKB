-- ==========================================
-- OKB DDL v3 Skeleton
-- Draft schema for the OKB project
-- Built on top of NSI v2.7 ideas, adapted for:
-- source ingestion, document versioning, page-level OCR,
-- RAG, project context, and comparison workflows
-- ==========================================

-- 0. Extensions
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS ltree;

-- 1. Schema
CREATE SCHEMA IF NOT EXISTS okb;

-- 2. Enums
CREATE TYPE okb.user_role AS ENUM (
    'engineer',
    'knowledge_admin',
    'system_admin'
);

CREATE TYPE okb.source_kind AS ENUM (
    'local_folder',
    'google_drive',
    'registry_sheet',
    'manual_upload',
    'downloaded_corpus',
    'external_registry'
);

CREATE TYPE okb.document_domain AS ENUM (
    'normative',
    'project',
    'reference',
    'registry'
);

CREATE TYPE okb.document_status AS ENUM (
    'draft',
    'active',
    'deprecated',
    'archived'
);

CREATE TYPE okb.version_status AS ENUM (
    'draft',
    'current',
    'superseded',
    'archived'
);

CREATE TYPE okb.legal_force AS ENUM (
    'mandatory',
    'recommended',
    'informational'
);

CREATE TYPE okb.processing_status AS ENUM (
    'queued',
    'processing',
    'completed',
    'partial',
    'failed'
);

CREATE TYPE okb.page_text_status AS ENUM (
    'native_text',
    'ocr_required',
    'ocr_done',
    'low_text',
    'unreadable'
);

CREATE TYPE okb.quality_mode AS ENUM (
    'fast',
    'quality'
);

CREATE TYPE okb.relation_type AS ENUM (
    'reference',
    'conflict',
    'mandatory',
    'derived'
);

CREATE TYPE okb.comparison_status AS ENUM (
    'ok',
    'warning',
    'potential_mismatch',
    'needs_review',
    'not_enough_evidence'
);

CREATE TYPE okb.review_status AS ENUM (
    'pending',
    'approved',
    'rejected',
    'needs_fix'
);

-- 3. Users
CREATE TABLE okb.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT NOT NULL UNIQUE,
    role okb.user_role NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 4. Sources and ingestion lineage
CREATE TABLE okb.sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_name TEXT NOT NULL,
    source_kind okb.source_kind NOT NULL,
    external_ref TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES okb.users(id)
);

CREATE TABLE okb.source_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES okb.sources(id) ON DELETE CASCADE,
    external_file_id TEXT,
    source_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    media_type TEXT,
    size_bytes BIGINT,
    checksum_sha256 TEXT,
    file_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    discovered_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE TABLE okb.ingestion_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID REFERENCES okb.sources(id),
    run_label TEXT,
    run_mode okb.quality_mode NOT NULL DEFAULT 'fast',
    status okb.processing_status NOT NULL DEFAULT 'queued',
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMP,
    triggered_by UUID REFERENCES okb.users(id),
    stats JSONB NOT NULL DEFAULT '{}'::jsonb,
    error_summary TEXT
);

-- 5. Documents and versions
CREATE TABLE okb.documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_domain okb.document_domain NOT NULL,
    title TEXT NOT NULL,
    doc_code TEXT,
    doc_type TEXT,
    source_authority TEXT,
    original_language TEXT,
    norm_category TEXT,
    legal_force okb.legal_force,
    authority_level TEXT,
    approval_body TEXT,
    applicability_scope JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    tenant_id TEXT NOT NULL DEFAULT 'default',
    status okb.document_status NOT NULL DEFAULT 'draft',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP,
    created_by UUID REFERENCES okb.users(id)
);

CREATE TABLE okb.document_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES okb.documents(id) ON DELETE CASCADE,
    source_file_id UUID REFERENCES okb.source_files(id),
    ingestion_run_id UUID REFERENCES okb.ingestion_runs(id),
    version_label TEXT NOT NULL,
    version_number INT,
    revision_label TEXT,
    version_status okb.version_status NOT NULL DEFAULT 'draft',
    is_current BOOLEAN NOT NULL DEFAULT FALSE,
    quality_mode okb.quality_mode NOT NULL DEFAULT 'fast',
    source_published_at DATE,
    valid_from DATE NOT NULL DEFAULT '1900-01-01',
    valid_to DATE NOT NULL DEFAULT '9999-12-31',
    file_checksum_sha256 TEXT,
    parser_profile TEXT,
    processing_status okb.processing_status NOT NULL DEFAULT 'queued',
    change_log TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    reviewed_by UUID REFERENCES okb.users(id),
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES okb.users(id),
    CONSTRAINT chk_version_dates CHECK (valid_to >= valid_from),
    CONSTRAINT uq_document_version_label UNIQUE (document_id, version_label)
);

CREATE TABLE okb.ingestion_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ingestion_run_id UUID NOT NULL REFERENCES okb.ingestion_runs(id) ON DELETE CASCADE,
    source_file_id UUID NOT NULL REFERENCES okb.source_files(id) ON DELETE CASCADE,
    status okb.processing_status NOT NULL DEFAULT 'queued',
    detected_document_domain okb.document_domain,
    duplicate_of_source_file_id UUID REFERENCES okb.source_files(id),
    created_document_id UUID REFERENCES okb.documents(id),
    created_version_id UUID REFERENCES okb.document_versions(id),
    message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 6. Page-level processing
CREATE TABLE okb.document_pages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_version_id UUID NOT NULL REFERENCES okb.document_versions(id) ON DELETE CASCADE,
    page_number INT NOT NULL,
    text_status okb.page_text_status NOT NULL DEFAULT 'native_text',
    processing_status okb.processing_status NOT NULL DEFAULT 'queued',
    ocr_engine TEXT,
    parser_engine TEXT,
    confidence FLOAT,
    native_text_char_count INT,
    image_path TEXT,
    ocr_required BOOLEAN NOT NULL DEFAULT FALSE,
    error_message TEXT,
    page_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_document_page UNIQUE (document_version_id, page_number)
);

-- 7. Structure and retrieval units
CREATE TABLE okb.document_sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_version_id UUID NOT NULL REFERENCES okb.document_versions(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES okb.document_sections(id),
    title TEXT,
    section_code TEXT,
    level INT NOT NULL,
    path LTREE NOT NULL,
    start_page_number INT,
    end_page_number INT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_section_path UNIQUE (document_version_id, path)
);

CREATE TABLE okb.chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_version_id UUID NOT NULL REFERENCES okb.document_versions(id) ON DELETE CASCADE,
    section_id UUID REFERENCES okb.document_sections(id),
    page_id UUID REFERENCES okb.document_pages(id),
    page_number INT,
    chunk_index INT NOT NULL,
    original_text TEXT NOT NULL,
    normalized_text TEXT,
    search_text TEXT NOT NULL,
    -- Replace dimension when the embedding model is fixed for the project.
    embedding VECTOR(1536),
    tsv TSVECTOR,
    chunk_strategy TEXT NOT NULL DEFAULT 'semantic_512',
    bbox JSONB,
    confidence FLOAT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP
);

CREATE TABLE okb.chunk_translations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id UUID NOT NULL REFERENCES okb.chunks(id) ON DELETE CASCADE,
    language TEXT NOT NULL,
    translated_text TEXT NOT NULL,
    translation_model TEXT,
    confidence FLOAT,
    needs_review BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_chunk_translation UNIQUE (chunk_id, language)
);

-- 8. Visual and table artefacts
CREATE TABLE okb.images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_version_id UUID NOT NULL REFERENCES okb.document_versions(id) ON DELETE CASCADE,
    page_id UUID REFERENCES okb.document_pages(id),
    page_number INT,
    file_path TEXT NOT NULL,
    file_type TEXT,
    title TEXT,
    caption TEXT,
    description TEXT,
    bbox JSONB,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE okb.chunk_images (
    chunk_id UUID NOT NULL REFERENCES okb.chunks(id) ON DELETE CASCADE,
    image_id UUID NOT NULL REFERENCES okb.images(id) ON DELETE CASCADE,
    PRIMARY KEY (chunk_id, image_id)
);

CREATE TABLE okb.extracted_tables (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_version_id UUID NOT NULL REFERENCES okb.document_versions(id) ON DELETE CASCADE,
    section_id UUID REFERENCES okb.document_sections(id),
    page_id UUID REFERENCES okb.document_pages(id),
    page_number INT,
    table_title TEXT,
    table_data JSONB NOT NULL,
    bbox JSONB,
    confidence FLOAT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE okb.document_title_blocks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_version_id UUID NOT NULL REFERENCES okb.document_versions(id) ON DELETE CASCADE,
    page_id UUID REFERENCES okb.document_pages(id),
    page_number INT,
    extracted_fields JSONB NOT NULL DEFAULT '{}'::jsonb,
    confidence FLOAT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 9. Graph and terminology
CREATE TABLE okb.document_relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_version_id UUID NOT NULL REFERENCES okb.document_versions(id) ON DELETE CASCADE,
    to_version_id UUID NOT NULL REFERENCES okb.document_versions(id) ON DELETE CASCADE,
    relation_type okb.relation_type NOT NULL,
    relation_origin TEXT NOT NULL DEFAULT 'auto',
    score FLOAT,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE okb.chunk_relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_chunk_id UUID NOT NULL REFERENCES okb.chunks(id) ON DELETE CASCADE,
    to_chunk_id UUID NOT NULL REFERENCES okb.chunks(id) ON DELETE CASCADE,
    relation_type okb.relation_type NOT NULL,
    score FLOAT,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_no_self_chunk_relation CHECK (from_chunk_id <> to_chunk_id),
    CONSTRAINT uq_chunk_relation UNIQUE (from_chunk_id, to_chunk_id, relation_type)
);

CREATE TABLE okb.glossary_terms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    term_key TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'ru',
    term TEXT NOT NULL,
    definition TEXT,
    category TEXT,
    synonyms TEXT[],
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_glossary_key UNIQUE (term_key, language)
);

CREATE TABLE okb.glossary_term_chunks (
    term_id UUID NOT NULL REFERENCES okb.glossary_terms(id) ON DELETE CASCADE,
    chunk_id UUID NOT NULL REFERENCES okb.chunks(id) ON DELETE CASCADE,
    PRIMARY KEY (term_id, chunk_id)
);

-- 10. Projects and project document binding
CREATE TABLE okb.projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    ship_type TEXT,
    class_code TEXT,
    project_status TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES okb.users(id)
);

CREATE TABLE okb.project_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES okb.projects(id) ON DELETE CASCADE,
    document_version_id UUID NOT NULL REFERENCES okb.document_versions(id) ON DELETE CASCADE,
    document_role TEXT NOT NULL,
    discipline TEXT,
    drawing_code TEXT,
    revision_label TEXT,
    title_block_id UUID REFERENCES okb.document_title_blocks(id),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_project_document_version UNIQUE (project_id, document_version_id, document_role)
);

-- 11. Comparison workflow
CREATE TABLE okb.comparison_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES okb.projects(id) ON DELETE CASCADE,
    run_label TEXT,
    status okb.processing_status NOT NULL DEFAULT 'queued',
    started_by UUID REFERENCES okb.users(id),
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMP,
    query_text TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE okb.comparison_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    comparison_run_id UUID NOT NULL REFERENCES okb.comparison_runs(id) ON DELETE CASCADE,
    normative_chunk_id UUID REFERENCES okb.chunks(id),
    project_chunk_id UUID REFERENCES okb.chunks(id),
    normative_table_id UUID REFERENCES okb.extracted_tables(id),
    project_table_id UUID REFERENCES okb.extracted_tables(id),
    normalized_requirement_value TEXT,
    normalized_requirement_unit TEXT,
    normalized_project_value TEXT,
    normalized_project_unit TEXT,
    comparison_status okb.comparison_status NOT NULL DEFAULT 'needs_review',
    ambiguity_reason TEXT,
    review_status okb.review_status NOT NULL DEFAULT 'pending',
    reviewed_by UUID REFERENCES okb.users(id),
    reviewed_at TIMESTAMP,
    evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE okb.review_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type TEXT NOT NULL,
    entity_id UUID NOT NULL,
    task_type TEXT NOT NULL,
    review_status okb.review_status NOT NULL DEFAULT 'pending',
    assigned_to UUID REFERENCES okb.users(id),
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMP
);

-- 12. Assistant operations and evaluation
CREATE TABLE okb.query_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES okb.users(id),
    project_id UUID REFERENCES okb.projects(id),
    query TEXT NOT NULL,
    answer_text TEXT,
    answer_json JSONB,
    latency_ms INT,
    model_name TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE okb.query_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_id UUID NOT NULL REFERENCES okb.query_history(id) ON DELETE CASCADE,
    chunk_id UUID REFERENCES okb.chunks(id),
    rank_position INT,
    score FLOAT,
    citation_payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE okb.feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_id UUID NOT NULL REFERENCES okb.query_history(id) ON DELETE CASCADE,
    chunk_id UUID REFERENCES okb.chunks(id),
    rating INT CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE okb.query_cache (
    query_hash TEXT PRIMARY KEY,
    response JSONB NOT NULL,
    sources JSONB NOT NULL DEFAULT '[]'::jsonb,
    source_checksum TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL DEFAULT NOW() + INTERVAL '7 days',
    last_accessed TIMESTAMP NOT NULL DEFAULT NOW(),
    hits INT NOT NULL DEFAULT 0
);

-- 13. Indexes
CREATE INDEX idx_sources_kind ON okb.sources(source_kind);
CREATE INDEX idx_source_files_source ON okb.source_files(source_id);
CREATE INDEX idx_source_files_checksum ON okb.source_files(checksum_sha256);
CREATE INDEX idx_source_files_path ON okb.source_files(source_id, source_path);
CREATE INDEX idx_ingestion_runs_source ON okb.ingestion_runs(source_id, status);
CREATE INDEX idx_ingestion_items_run ON okb.ingestion_items(ingestion_run_id, status);

CREATE INDEX idx_documents_domain ON okb.documents(document_domain, status);
CREATE INDEX idx_documents_tenant ON okb.documents(tenant_id);
CREATE INDEX idx_documents_metadata ON okb.documents USING GIN(metadata);

CREATE UNIQUE INDEX idx_document_current_version
ON okb.document_versions(document_id)
WHERE is_current = TRUE;

CREATE INDEX idx_document_versions_document ON okb.document_versions(document_id);
CREATE INDEX idx_document_versions_status ON okb.document_versions(processing_status, version_status);
CREATE INDEX idx_document_pages_version ON okb.document_pages(document_version_id, page_number);
CREATE INDEX idx_document_pages_failed ON okb.document_pages(document_version_id)
WHERE processing_status IN ('failed', 'partial');

CREATE INDEX idx_sections_version ON okb.document_sections(document_version_id);
CREATE INDEX idx_sections_path ON okb.document_sections USING GIST(path);

CREATE INDEX idx_chunks_version ON okb.chunks(document_version_id);
CREATE INDEX idx_chunks_section ON okb.chunks(section_id);
CREATE INDEX idx_chunks_page ON okb.chunks(page_id);
CREATE INDEX idx_chunks_tsv ON okb.chunks USING GIN(tsv);
CREATE INDEX idx_chunks_embedding_hnsw
ON okb.chunks USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
CREATE INDEX idx_chunks_active
ON okb.chunks(document_version_id, page_number)
WHERE deleted_at IS NULL;

CREATE INDEX idx_images_version ON okb.images(document_version_id);
CREATE INDEX idx_tables_version ON okb.extracted_tables(document_version_id);
CREATE INDEX idx_title_blocks_version ON okb.document_title_blocks(document_version_id);

CREATE INDEX idx_document_relations_from ON okb.document_relations(from_version_id);
CREATE INDEX idx_document_relations_to ON okb.document_relations(to_version_id);
CREATE INDEX idx_chunk_relations_from ON okb.chunk_relations(from_chunk_id);
CREATE INDEX idx_chunk_relations_to ON okb.chunk_relations(to_chunk_id);

CREATE INDEX idx_glossary_term_chunks_chunk ON okb.glossary_term_chunks(chunk_id);
CREATE INDEX idx_glossary_term_chunks_term ON okb.glossary_term_chunks(term_id);

CREATE INDEX idx_projects_status ON okb.projects(project_status);
CREATE INDEX idx_project_documents_project ON okb.project_documents(project_id);
CREATE INDEX idx_project_documents_version ON okb.project_documents(document_version_id);

CREATE INDEX idx_comparison_runs_project ON okb.comparison_runs(project_id, status);
CREATE INDEX idx_comparison_items_run ON okb.comparison_items(comparison_run_id, comparison_status);
CREATE INDEX idx_review_tasks_status ON okb.review_tasks(review_status, assigned_to);

CREATE INDEX idx_query_history_user ON okb.query_history(user_id, created_at);
CREATE INDEX idx_query_history_project ON okb.query_history(project_id, created_at);
CREATE INDEX idx_query_sources_query ON okb.query_sources(query_id, rank_position);
CREATE INDEX idx_feedback_query ON okb.feedback(query_id);
CREATE INDEX idx_query_cache_expired ON okb.query_cache(expires_at);

-- 14. Triggers
CREATE OR REPLACE FUNCTION okb.set_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_documents_updated
BEFORE UPDATE ON okb.documents
FOR EACH ROW EXECUTE FUNCTION okb.set_updated_at();

CREATE TRIGGER trg_projects_updated
BEFORE UPDATE ON okb.projects
FOR EACH ROW EXECUTE FUNCTION okb.set_updated_at();

CREATE OR REPLACE FUNCTION okb.update_chunks_tsv() RETURNS trigger AS $$
BEGIN
    NEW.tsv := to_tsvector('russian', COALESCE(NEW.search_text, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_chunks_tsv
BEFORE INSERT OR UPDATE OF search_text ON okb.chunks
FOR EACH ROW EXECUTE FUNCTION okb.update_chunks_tsv();
