-- Classifier quarantine (docs/api/registry_service_api.md §5.2)
CREATE TABLE IF NOT EXISTS registry.classifier_pending (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    system VARCHAR(20) NOT NULL,
    code TEXT NOT NULL,
    found_in_document_id UUID REFERENCES registry.documents(id) ON DELETE SET NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'new',
    admin_comment TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (system, code)
);

CREATE INDEX IF NOT EXISTS idx_classifier_pending_system_status
    ON registry.classifier_pending (system, status);
