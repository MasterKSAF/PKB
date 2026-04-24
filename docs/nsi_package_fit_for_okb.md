# NSI package fit for OKB

Date: 2026-04-21

## Analysed materials

- `C:\Users\Misha\Documents\GitHub\OKB\docs\1_Описание_структуры_данных_и_полей_2_Процесс_внесения_НСИ_документа.docx`
- `C:\Users\Misha\Downloads\Telegram Desktop\NSI DDL v2.7 (clean + production-safe).docx`
- `C:\Users\Misha\Downloads\Telegram Desktop\DDL v2.7 (Production-Ready).sql`
- `C:\Users\Misha\Downloads\Telegram Desktop\Презентация_Нейро_консультант_для_ПКБ_«Петробалт».pdf`
- `C:\Users\Misha\Documents\GitHub\OKB\docs\mvp_12_week_plan.md`
- `C:\Users\Misha\Documents\GitHub\OKB\docs\knowledge_base_reading_report.md`

## Short conclusion

If we assess the NSI materials as a package rather than as a single explanatory document, they are a strong fit for the OKB knowledge-base core:

- about `80-85%` fit as a base for normative storage, sections, chunks, glossary, graph links, query history, and hybrid retrieval;
- about `60-65%` fit as a base for the whole OKB MVP without additional schema work.

The package is strong as a `knowledge infrastructure` for RAG.
It is not yet a complete OKB-ready schema for page-level OCR, source ingestion, project documentation, and requirement-vs-project comparison workflows.

## What this package already covers well

### 1. Normative document registry

Already covered:

- `documents`
- `document_versions`
- validity dates and status
- legal force and authority metadata
- soft delete and audit fields

Why this is useful for OKB:

- it gives a clean registry for normative sources;
- it supports versioning and lifecycle;
- it fits the rule that the assistant must work over a managed corpus, not just over files.

### 2. Structure-aware knowledge base

Already covered:

- `document_sections` with `ltree`
- `chunks`
- `chunk_strategy`
- `bbox`
- `confidence`
- `chunk_translations`

Why this is useful for OKB:

- it matches our need for section-aware chunking;
- it supports hybrid retrieval and future multilingual handling;
- it is much better than flat file indexing.

### 3. Graph and terminology layer

Already covered:

- `document_relations`
- `chunk_relations`
- `glossary_terms`
- `glossary_term_chunks`

Why this is useful for OKB:

- it supports cross-references between norms;
- it aligns with the presentation idea of a graph of dependencies and conflicts;
- it gives a place for normalized terminology and synonym control.

### 4. Retrieval operations and production concerns

Already covered:

- `tsvector` trigger
- pgvector index
- cache
- query history
- feedback
- PostgreSQL roles
- default privileges

Why this is useful for OKB:

- it shows real production thinking rather than a toy schema;
- it supports observability, caching, and evaluation loops;
- it is a reasonable foundation for a pilot.

### 5. Product logic from the presentation

Already covered conceptually:

- `Fast Pipeline` for bulk processing
- `Quality Path` for critical documents with human review
- graph-based context expansion
- model as answer formatter, not source of truth
- hybrid retrieval

Why this is useful for OKB:

- it is very close to the right product framing for a regulated engineering domain;
- it matches our earlier conclusion that the system should help review, not replace engineering judgment.

## What is missing for OKB

### 1. Version-bound derived entities

Current issue:

- `document_sections`, `chunks`, `images`, and `extracted_tables` are tied mostly to `document_id`.

Why this is a problem:

- OKB will work with changing editions and revisions;
- without `document_version_id`, sections and chunks from different versions can be mixed.

What to change:

- bind all derived artefacts to `document_version_id`;
- keep `document_id` only as a parent reference when needed for aggregation.

### 2. Page-level processing model

Current issue:

- there is only a `page` field on some tables;
- there is no page entity with OCR and parsing lifecycle.

Why this is a problem:

- our corpus contains low-text PDFs and OCR candidates;
- reprocessing, page errors, confidence, and extraction status need to be tracked at page level.

What to add:

- `document_pages`
- `page_processing_runs` or equivalent status fields
- OCR route, text-layer status, extraction status, confidence, and error details

### 3. Source and ingestion layer

Current issue:

- the schema assumes documents already arrive in the system;
- there is no explicit model for source adapters, file registry, import batches, or sync lineage.

Why this is a problem:

- OKB already has local folders, downloaded corpora, registry sheets, and Google Drive-derived sources;
- we need traceability from source to stored document version.

What to add:

- `sources`
- `source_files`
- `ingestion_runs`
- `ingestion_items`
- content hash, duplicate candidates, and sync strategy fields

### 4. Project and drawing context

Current issue:

- the package is strong for normative documents, but weak for project documentation and drawing metadata.

Why this is a problem:

- OKB is not only about norms;
- it also needs to compare project artefacts with norms.

What to add:

- `projects`
- `project_documents`
- drawing code and revision metadata
- title block metadata
- ship type, discipline, and document family tags

### 5. Comparison workflow

Current issue:

- there is no dedicated schema for requirement-vs-project checks.

Why this is a problem:

- comparison is one of the distinctive OKB features;
- storing only chunks is not enough for reviewable mismatch workflows.

What to add:

- `comparison_runs`
- `comparison_items`
- source links to both normative and project-side evidence
- normalized values, units, status, ambiguity reason, reviewer state

### 6. Citation contract and answer traceability

Current issue:

- `query_history` and `query_sources` exist, but the response model is still generic.

Why this is a problem:

- OKB needs strong citation discipline in user-facing answers.

What to add:

- explicit citation payload storage or structured answer references
- stable source locator fields: document, version, page, section, chunk, bbox

## What to keep without major changes

- `documents`
- `document_versions`
- `document_relations`
- `chunk_relations`
- `glossary_terms`
- `glossary_term_chunks`
- `query_history`
- `query_sources`
- `feedback`
- `query_cache`
- role and privilege structure

## What to keep but refactor

- `document_sections`
- `chunks`
- `chunk_translations`
- `images`
- `extracted_tables`

Refactor rule:

- move them from `document_id` centric design to `document_version_id` centric design;
- keep `document_id` only where it helps global lookup.

## What to add in DDL v3 for OKB

### Must-have

- `sources`
- `source_files`
- `ingestion_runs`
- `document_pages`
- `document_processing_events` or equivalent processing log
- `projects`
- `project_documents`
- `comparison_runs`
- `comparison_items`

### Strongly recommended

- `document_title_blocks`
- `table_cells` or richer extracted-table structure for reviewable comparisons
- `chunk_citations` or structured answer citation snapshots
- `review_tasks` for manual validation of critical documents

### Optional later

- ACL model beyond tenant-level separation
- richer graph traversal tables
- model registry for embeddings/OCR/parser variants

## Suggested DDL v3 direction

Core hierarchy for OKB should look like this:

1. `sources` -> where the file came from
2. `source_files` -> specific file instance with hash and path
3. `documents` -> logical document identity
4. `document_versions` -> concrete edition or revision
5. `document_pages` -> per-page OCR and parsing state
6. `document_sections` -> section tree for a specific version
7. `chunks` -> retrieval units for a specific version and page
8. `images` and `extracted_tables` -> extracted artefacts tied to version and page
9. `projects` and `project_documents` -> project context
10. `comparison_runs` and `comparison_items` -> engineering review workflow

This keeps the strongest parts of NSI DDL v2.7, but extends them into an OKB-specific system rather than a generic NSI storage schema.

## Practical recommendation

The right move is not to discard the NSI package.
The right move is:

1. take it as the base for `knowledge base core`;
2. redesign version binding and page binding;
3. add source ingestion and project comparison layers;
4. only then call the result `OKB DDL v3`.

That path preserves the strongest work already done and avoids rebuilding the useful parts from scratch.
