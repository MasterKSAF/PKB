-- Full schema dump for `registry` including sequences, tables, indexes, and FK constraints
-- Generated from live database. Review before applying.

CREATE SCHEMA IF NOT EXISTS registry;

-- Sequences
CREATE SEQUENCE IF NOT EXISTS registry.document_sections_id_seq AS bigint START WITH 1;

-- Tables and indexes (see dump_registry_schema.sql for full CREATE TABLE definitions)
\echo 'Please ensure dump_registry_schema.sql has been applied before running constraints.'

-- Foreign key and other constraints (explicit ALTER statements)
ALTER TABLE registry.document_history
  ADD CONSTRAINT document_history_document_id_fkey FOREIGN KEY (document_id) REFERENCES registry.documents(id) ON DELETE CASCADE;

ALTER TABLE registry.document_references
  ADD CONSTRAINT document_references_resolved_document_id_fkey FOREIGN KEY (resolved_document_id) REFERENCES registry.documents(id) ON DELETE SET NULL;

ALTER TABLE registry.document_references
  ADD CONSTRAINT document_references_source_document_id_fkey FOREIGN KEY (source_document_id) REFERENCES registry.documents(id) ON DELETE CASCADE;

ALTER TABLE registry.document_sections
  ADD CONSTRAINT document_sections_document_id_fkey FOREIGN KEY (document_id) REFERENCES registry.documents(id) ON DELETE CASCADE;

ALTER TABLE registry.document_sections
  ADD CONSTRAINT document_sections_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES registry.document_sections(id) ON DELETE CASCADE;

ALTER TABLE registry.document_versions
  ADD CONSTRAINT document_versions_document_id_fkey FOREIGN KEY (document_id) REFERENCES registry.documents(id) ON DELETE CASCADE;

ALTER TABLE registry.documents
  ADD CONSTRAINT documents_predecessor_doc_id_fkey FOREIGN KEY (predecessor_doc_id) REFERENCES registry.documents(id) ON DELETE SET NULL;

ALTER TABLE registry.documents
  ADD CONSTRAINT documents_successor_doc_id_fkey FOREIGN KEY (successor_doc_id) REFERENCES registry.documents(id) ON DELETE SET NULL;

-- Note: Primary keys and unique constraints are created in table definitions. Check dump_registry_schema.sql for details.

-- End of full dump
