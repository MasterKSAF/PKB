-- Align registry.documents with docs/api/registry_service_api.md §5.4 (registry_document.status)
ALTER TABLE registry.documents
    ADD COLUMN IF NOT EXISTS status VARCHAR(30);

UPDATE registry.documents
SET status = 'draft'
WHERE status IS NULL;

ALTER TABLE registry.documents
    ALTER COLUMN status SET DEFAULT 'draft',
    ALTER COLUMN status SET NOT NULL;
