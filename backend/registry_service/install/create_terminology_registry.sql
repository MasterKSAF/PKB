CREATE TABLE IF NOT EXISTS registry.terminology (
CREATE TABLE IF NOT EXISTS registry.terminology (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_term TEXT NOT NULL,
    normalized_value TEXT,
    standard_term TEXT,
    term_type TEXT DEFAULT 'term',
    is_case_sensitive BOOLEAN DEFAULT FALSE,
    definition TEXT,
    synonyms JSONB DEFAULT '[]',
    related_docs JSONB DEFAULT '[]',
    scope JSONB DEFAULT '[]',
    is_blocked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_terminology_term_type ON registry.terminology (term_type);
CREATE INDEX IF NOT EXISTS idx_terminology_is_blocked ON registry.terminology (is_blocked);

-- Comments
COMMENT ON TABLE registry.terminology IS 'Terminology registry entries: terms, synonyms, definitions and related docs';
COMMENT ON COLUMN registry.terminology.raw_term IS 'Original raw term text';
COMMENT ON COLUMN registry.terminology.normalized_value IS 'Normalized term value used for lookup';
COMMENT ON COLUMN registry.terminology.standard_term IS 'Canonical standard term mapped from raw_term';
COMMENT ON COLUMN registry.terminology.synonyms IS 'JSON array of synonym strings';
COMMENT ON COLUMN registry.terminology.related_docs IS 'JSON array of related document identifiers';
COMMENT ON COLUMN registry.terminology.scope IS 'JSON array describing scope or domains for the term';

-- Optional: unique constraint on (normalized_value, term_type) if desired
-- ALTER TABLE registry.terminology ADD CONSTRAINT unique_norm_type UNIQUE (normalized_value, term_type);
