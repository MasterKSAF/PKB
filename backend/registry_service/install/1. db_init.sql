-- PKB Registry Database Initialization Script
-- Generated from: docs/database/db_diagrams.md
-- Created: 2026-05-30

-- ============================================================================
-- Extensions
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "ltree";


-- ============================================================================
-- Schemas
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS registry;


-- ============================================================================
-- Registry Schema Tables
-- ============================================================================

-- Documents registry
CREATE TABLE registry.documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_code TEXT NOT NULL,
    title TEXT NOT NULL,
    normalized_title TEXT,
    source_type VARCHAR(50),
    "group" VARCHAR(50),
    mks_oks_code TEXT,
    okstu_code TEXT,
    udc TEXT,
    era VARCHAR(50),
    validity_status VARCHAR(50),
    status VARCHAR(30) NOT NULL DEFAULT 'draft',
    jurisdiction VARCHAR(50),
    issuing_body TEXT,
    adoption_date DATE,
    effective_from DATE,
    replaces TEXT,
    status_note TEXT,
    file_hash_sha256 TEXT,
    title_hash_sha256 TEXT,
    file_size_bytes BIGINT,
    processing_status VARCHAR(50),
    chunk_count INT DEFAULT 0,
    successor_doc_id UUID,
    predecessor_doc_id UUID,
    created_by TEXT,
    updated_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (successor_doc_id) REFERENCES registry.documents(id) ON DELETE SET NULL,
    FOREIGN KEY (predecessor_doc_id) REFERENCES registry.documents(id) ON DELETE SET NULL
);

-- Document sections (hierarchical structure)
CREATE TABLE registry.document_sections (
    id BIGSERIAL PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES registry.documents(id) ON DELETE CASCADE,
    parent_id BIGINT REFERENCES registry.document_sections(id) ON DELETE CASCADE,
    clause TEXT,
    title TEXT,
    "level" INT,
    path LTREE,
    page INT,
    bbox JSONB,
    "type" VARCHAR(50),
    content JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CHECK ("type" IN ('text', 'textBlock', 'headerFooter', 'table', 'list', 'image', 'formula'))
);

-- Document references (links between documents)
CREATE TABLE registry.document_references (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_document_id UUID NOT NULL REFERENCES registry.documents(id) ON DELETE CASCADE,
    target_doc_code TEXT NOT NULL,
    reference_type VARCHAR(50),
    context TEXT,
    current_status VARCHAR(50),
    replaced_by TEXT,
    replacement_date DATE,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_document_id UUID REFERENCES registry.documents(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Document versions (file versioning)
CREATE TABLE registry.document_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES registry.documents(id) ON DELETE CASCADE,
    version_number INT,
    file_hash_sha256 TEXT,
    file_size_bytes BIGINT,
    format_code VARCHAR(50),
    format_label TEXT,
    file_key TEXT,
    uploaded_by TEXT,
    uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

-- Document history (audit log)
CREATE TABLE registry.document_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES registry.documents(id) ON DELETE CASCADE,
    event_type TEXT,
    old_status VARCHAR(50),
    new_status VARCHAR(50),
    comment TEXT,
    changed_by TEXT,
    document_snapshot JSONB,
    event_at TIMESTAMPTZ DEFAULT NOW()
);


-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Registry.documents indexes
CREATE INDEX idx_documents_doc_code ON registry.documents(doc_code);
CREATE INDEX idx_documents_file_hash ON registry.documents(file_hash_sha256, file_size_bytes);
CREATE INDEX idx_documents_title_hash ON registry.documents(title_hash_sha256);
CREATE INDEX idx_documents_processing_status ON registry.documents(processing_status);
CREATE INDEX idx_documents_validity_status ON registry.documents(validity_status);
CREATE INDEX idx_documents_era ON registry.documents(era);
CREATE INDEX idx_documents_jurisdiction ON registry.documents(jurisdiction);
CREATE INDEX idx_documents_created_at ON registry.documents(created_at);
CREATE INDEX idx_documents_updated_at ON registry.documents(updated_at);

-- Registry.document_sections indexes
CREATE INDEX idx_sections_document_id ON registry.document_sections(document_id);
CREATE INDEX idx_sections_parent_id ON registry.document_sections(parent_id);
CREATE INDEX idx_sections_path ON registry.document_sections USING GIST(path);
CREATE INDEX idx_sections_page ON registry.document_sections(page);

-- Registry.document_references indexes
CREATE INDEX idx_references_source_document_id ON registry.document_references(source_document_id);
CREATE INDEX idx_references_resolved_document_id ON registry.document_references(resolved_document_id);
CREATE INDEX idx_references_target_doc_code ON registry.document_references(target_doc_code);
CREATE INDEX idx_references_is_resolved ON registry.document_references(is_resolved);

-- Registry.document_versions indexes
CREATE INDEX idx_versions_document_id ON registry.document_versions(document_id);
CREATE INDEX idx_versions_uploaded_at ON registry.document_versions(uploaded_at);

-- Registry.document_history indexes
CREATE INDEX idx_history_document_id ON registry.document_history(document_id);
CREATE INDEX idx_history_event_type ON registry.document_history(event_type);
CREATE INDEX idx_history_event_at ON registry.document_history(event_at);


-- ============================================================================
-- Unique Constraints
-- ============================================================================

-- Ensure document code uniqueness per era
ALTER TABLE registry.documents 
ADD CONSTRAINT unique_doc_code_era UNIQUE(doc_code, era);

-- Ensure version numbers are unique per document
ALTER TABLE registry.document_versions 
ADD CONSTRAINT unique_version_number UNIQUE(document_id, version_number);


-- ============================================================================
-- Comments / Documentation
-- ============================================================================

COMMENT ON SCHEMA registry IS 'Registry of documents with metadata, sections, references, and processing history';

COMMENT ON TABLE registry.documents IS 'Main registry of all documents';
COMMENT ON COLUMN registry.documents.processing_status IS 'FSM status: uploaded, previewing, awaiting_decision, parsing, validation, ready_for_promotion, review_required, approved, registry, pending_index, indexing, indexed, duplicate, new_version, archived, failed';
COMMENT ON COLUMN registry.documents.file_hash_sha256 IS 'Hash of binary file for duplicate detection';
COMMENT ON COLUMN registry.documents.title_hash_sha256 IS 'Hash of doc_code + title + era for duplicate detection';

COMMENT ON TABLE registry.document_sections IS 'Hierarchical sections of documents with content metadata';
COMMENT ON COLUMN registry.document_sections.path IS 'LTree path for hierarchical queries';
COMMENT ON COLUMN registry.document_sections.content IS 'JSONB content: {text, amendments} for sections, {caption, columns, rows} for tables, etc.';

COMMENT ON TABLE registry.document_references IS 'Cross-references between documents';
COMMENT ON COLUMN registry.document_references.current_status IS 'Status of target document: active, superseded';

COMMENT ON TABLE registry.document_history IS 'Audit log of document processing events';
COMMENT ON COLUMN registry.document_history.document_snapshot IS 'Enriched JSON snapshot at event time';

-- ============================================================================
-- End of Script
-- ============================================================================
