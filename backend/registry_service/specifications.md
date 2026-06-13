# Registry Service Specifications & Findings

This document provides a comprehensive overview of the current implementation of the `registry_service` component, covering its API routes, business logic, database architecture, constraints, indexes, and key findings.

---

## 1. API Routing & Endpoint Logic
The service is built on FastAPI and exposes several RESTful endpoints grouped by domain:

### 1.1. Documents Registry (`/registry/documents/`)
* **`GET /registry/documents/`**: Lists all documents with pagination (`page`, `page_size`) and optional query filters (`doc_code`, `title`, `status`, `mks_oks_code`, `source_type`, `okstu_code`, `era`, `validity_status`, `jurisdiction`, `issuing_body`, `title_hash_sha256`, `date_from`, `date_to`).
* **`GET /registry/documents/export`**: Exports registry documents as a CSV file.
* **`POST /registry/documents/import`**: Bulk imports documents from a file. (Currently a **static stub** returning `{"data": {"message": "Import accepted"}}`).
* **`POST /registry/documents/check-uniqueness`**: Performs duplicate checking on document metadata by verifying if a record with the same computed title hash exists.
* **`GET /registry/documents/{document_id}`**: Retrieves a single document by its BIGINT ID.
* **`GET /registry/documents/{document_id}/sections`**: Bundles the document metadata along with all its sections (clauses, titles, levels, paths, pages, content) for RAG builder consumption.
* **`POST /registry/documents/`**: Creates a new document. Supports standard JSON creation and pipeline-ingested payload formats. Automatically computes `title_hash_sha256` to prevent duplicate insertions.
* **`PUT /registry/documents/{document_id}`**: Updates all fields of a document.
* **`PATCH /registry/documents/{document_id}`**: Partially updates document fields.
* **`PATCH /registry/documents/{document_id}/status`**: Updates the document workflow status (FSM transition: `draft` -> `uploaded` -> `validating` -> `processing` -> `review_required` -> `approved`/`failed` -> `registry` -> `archived`). Enforces valid state transitions, records audit log details to `document_history`, and returns a compact response payload containing `id`, `status`, `previous_status`, `history_id`, and `updated_at`.
* **`DELETE /registry/documents/{document_id}`**: Deletes a document by ID.
* **`GET /registry/documents/{document_id}/history`**: Retrieves the history/audit log of status transitions for a document.
* **`GET /registry/documents/{document_id}/succession`**: Returns the succession chain of a document (predecessor and successor documents).

### 1.2. Classifiers (`/registry/classifiers/`)
* **`POST /registry/classifiers/`**: Creates a new classifier entry. Enforces uniqueness on `(classifier_system, code)`.
* **`GET /registry/classifiers/`**: Lists all classifiers in a flat format with optional paging and query filters.
* **`GET /registry/classifiers/tree`**: Returns an hierarchical tree-like structure of classifiers based on a specified `classifier_system`.
* **`POST /registry/classifiers/import`**: Imports classifiers from a file (Currently a **static stub**).
* **`GET /registry/classifiers/pending`**: Lists pending classifiers currently held in "quarantine".
* **`POST /registry/classifiers/pending/{pending_id}/accept`**: Accepts a quarantined classifier and adds it to the registry.
* **`POST /registry/classifiers/pending/{pending_id}/reject`**: Rejects a quarantined classifier.
* **`POST /registry/classifiers/validate`**: Validates a batch classification payload.
* **`GET /registry/classifiers/{code}`**: Retrieves a single classifier entry by `code` and `classifier_system`.
* **`PUT /registry/classifiers/{code}`**: Fully updates a classifier.
* **`PATCH /registry/classifiers/{code}`**: Partially updates a classifier.
* **`DELETE /registry/classifiers/{code}`**: Deletes a classifier. Prevents deletion if child classifiers or documents exist, unless `force=true` is supplied.

### 1.3. Terminology (`/registry/terminology/`)
* **`POST /registry/terminology/`**: Creates a term. Supports properties such as `synonyms`, `scope`, `is_case_sensitive`, `is_blocked`, and `definition`.
* **`GET /registry/terminology/`**: Lists terms with paging and filters.
* **`GET /registry/terminology/normalize`**: Normalizes and returns the standardized form of a term.
* **`POST /registry/terminology/import`**: Imports terms from a file (Currently a **static stub**).
* **`GET /registry/terminology/{term_id}`**: Retrieves a single term.
* **`PUT /registry/terminology/{term_id}`**: Updates a term.
* **`PATCH /registry/terminology/{term_id}`**: Partially updates a term.
* **`DELETE /registry/terminology/{term_id}`**: Deletes a term.

### 1.4. Common & Health
* **`GET /registry/enums`**: Returns a dictionary of system-wide enum lists grouped by their enum key.
* **`GET /registry/stats`**: Provides database metrics and document distribution statistics by status, source type, and era.
* **`GET /health`**: Returns `{"status": "ok"}` for service health checking.

---

## 2. Database Architecture & Schema Details
The database runs on PostgreSQL and all objects reside in the `registry` schema.

### 2.1. System-Wide UUID to BIGINT Conversion
All primary and foreign key columns originally defined as UUID have been migrated to **BIGINT** (using serial sequences) across the database and codebase. Unused UUID dialect imports have been cleaned up or marked obsolete.

### 2.2. Table Schemas, Constraints, and Indexes

#### 1. `registry.classifiers`
Stores the classification nodes of various NSI systems (e.g., MKS, UDC, OKSTU).
* **Primary Key**: `(classifier_system, code)` (composite key).
* **Columns**:
  * `classifier_system` (varchar(50), NOT NULL)
  * `code` (text, NOT NULL)
  * `full_name` (text, NOT NULL)
  * `description` (text)
  * `status` (varchar(50), DEFAULT 'active')
  * `parent_code` (text)
  * `created_at` (timestamptz)
  * `updated_at` (timestamptz)
  * `effective_date` (date)
  * `replaced_by` (text)
* **Comments**: `'Classifier entries (system, code, names, status) used by the registry service.'`

#### 2. `registry.documents`
Holds the core metadata for stored documents.
* **Primary Key**: `id` (bigint, autoincremented via `documents_id_seq`).
* **Columns**:
  * `id` (bigint, NOT NULL)
  * `doc_code` (text, NOT NULL)
  * `title` (text, NOT NULL)
  * `normalized_title` (text)
  * `source_type` (varchar(50))
  * `group` (varchar(50))
  * `mks_oks_code` (text)
  * `okstu_code` (text)
  * `udc` (text)
  * `era` (varchar(50))
  * `validity_status` (varchar(50))
  * `status` (varchar(50))
  * `jurisdiction` (varchar(50))
  * `issuing_body` (text)
  * `adoption_date` (date)
  * `effective_from` (date)
  * `replaces` (text)
  * `status_note` (text)
  * `file_hash_sha256` (text)
  * `title_hash_sha256` (text)
  * `file_size_bytes` (bigint)
  * `processing_status` (varchar(50))
  * `chunk_count` (integer, DEFAULT 0)
  * `successor_doc_id` (bigint)
  * `predecessor_doc_id` (bigint)
  * `created_by` (text)
  * `updated_by` (text)
  * `created_at` (timestamptz)
  * `updated_at` (timestamptz)
* **Constraints**:
  * `unique_doc_code_era`: UNIQUE (`doc_code`, `era`)
  * `documents_successor_doc_id_fkey`: FOREIGN KEY (`successor_doc_id`) REFERENCES `registry.documents(id)` ON DELETE SET NULL
  * `documents_predecessor_doc_id_fkey`: FOREIGN KEY (`predecessor_doc_id`) REFERENCES `registry.documents(id)` ON DELETE SET NULL

#### 3. `registry.document_sections`
Stores hierarchical parts/sections of ingested documents for RAG processing.
* **Primary Key**: `id` (bigint, NOT NULL).
* **Columns**:
  * `id` (bigint, NOT NULL)
  * `document_id` (bigint, NOT NULL)
  * `parent_id` (bigint)
  * `clause` (text)
  * `title` (text)
  * `level` (integer)
  * `path` (text)
  * `page` (integer)
  * `bbox` (jsonb)
  * `type` (varchar(50))
  * `content` (jsonb)
  * `created_at` (timestamptz)
* **Constraints**:
  * `document_sections_document_id_fkey`: FOREIGN KEY (`document_id`) REFERENCES `registry.documents(id)` ON DELETE CASCADE

#### 4. `registry.document_references`
Tracks references and citations between documents.
* **Primary Key**: `id` (bigint, autoincremented via `document_references_id_seq`).
* **Columns**:
  * `id` (bigint, NOT NULL)
  * `source_document_id` (bigint, NOT NULL)
  * `target_doc_code` (text, NOT NULL)
  * `reference_type` (varchar(50))
  * `context` (text)
  * `replaced_by` (text)
  * `replacement_date` (date)
  * `is_resolved` (boolean, DEFAULT false)
  * `resolved_document_id` (bigint)
  * `created_at` (timestamptz, DEFAULT now())
* **Constraints**:
  * `document_references_source_document_id_fkey`: FOREIGN KEY (`source_document_id`) REFERENCES `registry.documents(id)` ON DELETE CASCADE
  * `document_references_resolved_document_id_fkey`: FOREIGN KEY (`resolved_document_id`) REFERENCES `registry.documents(id)` ON DELETE SET NULL

#### 5. `registry.document_history`
Stores audit trails of document events and status transitions.
* **Primary Key**: `id` (bigint, autoincremented via `document_history_id_seq`).
* **Columns**:
  * `id` (bigint, NOT NULL)
  * `document_id` (bigint, NOT NULL)
  * `event_type` (text)
  * `old_status` (varchar(50))
  * `new_status` (varchar(50))
  * `comment` (text)
  * `changed_by` (text)
  * `document_snapshot` (jsonb)
  * `event_at` (timestamptz, DEFAULT now())
* **Comments**: 
  * Table comment: `'Audit log of document processing events'`
  * Column `document_snapshot`: `'Enriched JSON snapshot at event time'`
* **Constraints**:
  * `document_history_document_id_fkey`: FOREIGN KEY (`document_id`) REFERENCES `registry.documents(id)` ON DELETE CASCADE

#### 6. `registry.document_versions`
Tracks physical file versioning for documents.
* **Primary Key**: `id` (bigint, autoincremented via `document_versions_id_seq`).
* **Columns**:
  * `id` (bigint, NOT NULL)
  * `document_id` (bigint, NOT NULL)
  * `version_number` (integer)
  * `file_hash_sha256` (text)
  * `file_size_bytes` (bigint)
  * `format_code` (text)
  * `format_label` (text)
  * `file_key` (text)
  * `uploaded_by` (text)
  * `uploaded_at` (timestamptz)
* **Constraints**:
  * `document_versions_document_id_fkey`: FOREIGN KEY (`document_id`) REFERENCES `registry.documents(id)` ON DELETE CASCADE

#### 7. `registry.terminology`
Stores standardized NSI terms, abbreviations, and case-sensitivity settings.
* **Primary Key**: `id` (bigint, autoincremented via `terminology_id_seq`).
* **Columns**:
  * `id` (bigint, NOT NULL)
  * `raw_term` (text, NOT NULL)
  * `normalized_value` (text)
  * `standard_term` (text)
  * `term_type` (varchar(50))
  * `is_blocked` (boolean)
  * `definition` (text)
  * `created_at` (timestamptz)
  * `updated_at` (timestamptz)
  * `is_case_sensitive` (boolean, DEFAULT false)
  * `synonyms` (jsonb, DEFAULT '[]')
  * `related_docs` (jsonb, DEFAULT '[]')
  * `scope` (jsonb, DEFAULT '[]')

#### 8. `registry.rs_enums`
System-wide allowed enumerations (e.g. document types, valid statuses).
* **Primary Key**: `id` (bigint, autoincremented via `rs_enums_id_seq`).
* **Columns**:
  * `id` (bigint, NOT NULL)
  * `enum_key` (varchar(128), NOT NULL)
  * `enum_value` (varchar(256), NOT NULL)
  * `description` (text)
  * `metadata` (jsonb)
  * `created_at` (timestamptz, DEFAULT now())
* **Constraints**:
  * `uq_rs_enums_key_value`: UNIQUE (`enum_key`, `enum_value`)

---

## 3. Discrepancies & Key Findings

1. **`classifier_pending` Table**:
   * **SQL Schema/Dump**: The `classifier_pending` table is missing entirely from the database schema and does not exist in `1. db_dump.sql`.
   * **Codebase Implementation**: The table's SQLAlchemy model is defined in `api/v1/models/classifier_pending.py` and is fully referenced in `api/v1/crud/classifier.py` and `api/v1/routes.py`. It should be created in the database before quarantine features are utilized.
2. **Bulk File Imports**:
   * API routes for importing classifiers (`POST /registry/classifiers/import`), terminology (`POST /registry/terminology/import`), and documents (`POST /registry/documents/import`) are currently static stubs and do not implement parser logic.
3. **Foreign Keys on `classifiers`**:
   * In `002_update_documents.sql`, foreign keys `documents_mks_oks_code_fkey` and `documents_okstu_code_fkey` are designed to link documents directly to classifiers. If `classifier_system` is not populated on documents in production, these keys may evaluate to null defaults unless updated by the ingestion pipeline.
