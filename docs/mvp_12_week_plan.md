# MVP plan: neuro-assistant for engineering documents

Source of timeline: project brief defines MVP horizon as 3 months. The extended technical brief defines the execution estimate as 12 weeks, about 240 hours.

## Scope baseline

The MVP is limited to:

- loading engineering documents and source registries;
- OCR and text extraction from PDF, scans, specifications, and drawing PDFs;
- page/layout parsing for text, tables, title blocks, and drawing annotations;
- knowledge base creation with document/page/chunk metadata;
- semantic search and RAG answers with mandatory citations;
- basic comparison of extracted drawing/specification parameters with normative requirements;
- UI for upload, search, cited answer, source preview, and processing errors.

The MVP excludes:

- final engineering decision-making by AI;
- structural strength calculations;
- hydrostatics calculations;
- full CAD geometry analysis;
- automatic editing of source drawings;
- fine-tuning models;
- mobile applications.

## 12-week phase plan

| # | Phase | Duration | Effort | Calendar window | Main outcome |
|---|---:|---:|---:|---|---|
| 1 | Preparation | 1 week | 20 h | Week 1 | Scope, dataset inventory, architecture baseline |
| 2 | Ingestion + OCR | 2 weeks | 40 h | Weeks 2-3 | Document loading, parsing, OCR pipeline |
| 3 | RAG | 2 weeks | 40 h | Weeks 4-5 | Searchable knowledge base and cited retrieval |
| 4 | Dialog | 1 week | 24 h | Week 6 | Conversational query flow with clarifying questions |
| 5 | Decision checking | 2 weeks | 40 h | Weeks 7-8 | Basic requirement-vs-document comparison |
| 6 | Integrations | 1 week | 20 h | Week 9 | Source integrations and import automation |
| 7 | Frontend | 3 weeks | 60 h | Weeks 10-12 | User-facing MVP interface |
| 8 | Deploy | 1 week | 16 h | Week 12 | Deployable environment and operations baseline |
| 9 | Testing | 2 weeks | 32 h | Weeks 11-12 | Evaluation, regression tests, acceptance checks |

Note: the table preserves the phases and estimates from the technical brief. In execution, frontend, deploy, and testing work can overlap within weeks 10-12, but the phase budget remains unchanged.

## Phase details

### 1. Preparation, week 1, 20 h

Goals:

- freeze MVP scope according to the primary technical brief;
- inventory the available datasets;
- define the first version of the data model and processing statuses;
- choose baseline OCR, parsing, embedding, and storage components.

Inputs:

- primary technical brief;
- local Google Drive corpus;
- RKO publications corpus;
- registry spreadsheets.

Deliverables:

- dataset inventory;
- source registry model;
- MVP architecture note;
- acceptance metric draft;
- backlog for phases 2-9.

Exit criteria:

- scope is explicitly limited to OCR, parsing, RAG, citations, and basic mismatch highlighting;
- out-of-scope items are documented;
- all known source folders are registered as future ingestion sources.

### 2. Ingestion + OCR, weeks 2-3, 40 h

Goals:

- load local files and external source registry entries;
- parse text-first documents;
- run OCR for scanned or low-text PDFs;
- preserve page-level traceability.

Supported in MVP:

- PDF with text layer;
- scanned PDF through OCR;
- DOCX;
- XLSX;
- RTF;
- TXT;
- drawing PDFs with readable annotations and title blocks.

Deferred:

- native DWG geometry analysis;
- CAD model interpretation.

Deliverables:

- document ingestion service;
- file type detection;
- page extraction;
- OCR fallback path;
- per-page processing status;
- extraction artifacts stored with document/page references.

Exit criteria:

- processed pages have document ID and page number;
- low-text PDFs are detected and routed to OCR;
- text, table-like content, and errors are persisted;
- failed pages can be reprocessed.

### 3. RAG, weeks 4-5, 40 h

Goals:

- build searchable knowledge base;
- create chunks with stable source references;
- support semantic search and hybrid filtering;
- return citations with document and page.

Core pipeline:

- normalize extracted text;
- split into chunks;
- attach metadata;
- create embeddings;
- index chunks;
- retrieve and rerank relevant fragments.

Deliverables:

- chunking strategy;
- vector index;
- search API;
- citation model;
- answer generation prompt with source constraints.

Exit criteria:

- each result contains document, page, fragment, and source ID;
- answers are blocked or marked insufficient when sources are weak;
- top-k retrieval can be evaluated on a small control set.

### 4. Dialog, week 6, 24 h

Goals:

- support engineer-style questions;
- ask clarifying questions when the request is too broad;
- retain short conversation context without losing source traceability.

Deliverables:

- chat/query endpoint;
- dialog state model;
- clarification logic;
- answer format with citations and confidence notes.

Exit criteria:

- the assistant can distinguish a specific query from an underspecified query;
- every factual answer includes sources;
- insufficient evidence leads to clarification or refusal to conclude.

### 5. Decision checking, weeks 7-8, 40 h

Goals:

- extract candidate parameters from drawings/specifications;
- retrieve relevant normative requirements;
- highlight possible mismatches for engineer review.

Important rule:

The system does not issue final engineering conclusions. It only marks possible `OK`, `WARNING`, or `POTENTIAL_MISMATCH` cases for human verification.

Deliverables:

- parameter extraction prototype;
- requirement extraction prototype;
- comparison result model;
- explanation with source fragments on both sides.

Exit criteria:

- comparison output includes source for the requirement and source for the checked value;
- ambiguous cases are marked as requiring engineer review;
- no final approval/rejection language is used.

### 6. Integrations, week 9, 20 h

Goals:

- formalize imports from known sources;
- support source registries;
- prepare future connection to internal systems.

MVP integrations:

- local folder import;
- registry spreadsheet import;
- RKO downloaded corpus import;
- Google Drive downloaded corpus import.

Future integrations:

- RS catalog crawler;
- NTD/KARABI source mapping;
- Meridian API.

Deliverables:

- source adapter interface;
- registry import command;
- source metadata normalization;
- duplicate detection by filename, code, and content hash.

Exit criteria:

- every imported document is tied to a source;
- duplicate candidates are visible;
- source-specific metadata is preserved.

### 7. Frontend, weeks 10-12, 60 h

Goals:

- provide a usable MVP interface for engineers and admins;
- expose upload/import, processing state, search, cited answers, and source preview.

Screens:

- document registry;
- upload/import status;
- search/chat;
- cited answer view;
- page/source preview;
- processing errors;
- comparison result view.

Deliverables:

- frontend application;
- document list and filters;
- chat/search interface;
- citation cards;
- document page viewer;
- admin processing log.

Exit criteria:

- engineer can ask a question and open cited source page;
- admin can see processing errors;
- user does not see documents outside permitted scope, if permissions are enabled in MVP.

### 8. Deploy, week 12, 16 h

Goals:

- make the MVP reproducible and deployable;
- provide baseline operational setup.

Deliverables:

- Docker compose or equivalent local deployment;
- backend service;
- frontend service;
- PostgreSQL/pgvector;
- Redis/queue if used;
- storage volume layout;
- environment configuration.

Exit criteria:

- fresh environment can start from documented commands;
- sample corpus can be imported;
- search and cited answer work after deployment.

### 9. Testing, weeks 11-12, 32 h

Goals:

- validate retrieval, OCR, citations, and user workflows;
- prepare demo acceptance.

Test areas:

- ingestion test set;
- OCR quality check;
- retrieval top-k check;
- citation coverage;
- answer latency;
- UI acceptance flow;
- reprocessing failed documents.

Deliverables:

- smoke tests;
- evaluation query set;
- acceptance checklist;
- known limitations report.

Exit criteria:

- at least 80% of control queries return a relevant source in top 3;
- at least 90% of factual answers include document and page citation;
- known OCR failures are logged and visible;
- MVP demo scenario is repeatable.

## Pipeline structure

### Pipeline A. Source registry and import

Purpose:

Track where each document came from and keep source lineage intact.

Steps:

1. Read source definition.
2. Import local folder, registry spreadsheet, or crawled URL list.
3. Normalize metadata.
4. Create or update source record.
5. Create document version record.
6. Store binary file or external reference.
7. Enqueue processing job.

Outputs:

- source records;
- document records;
- document versions;
- import logs.

### Pipeline B. Document extraction

Purpose:

Turn files into page-level text, tables, blocks, and processing artifacts.

Steps:

1. Detect file type.
2. Extract pages or logical sections.
3. Try text-first extraction.
4. Detect low-text pages.
5. Run OCR for scanned pages.
6. Parse layout and tables where possible.
7. Save page text, blocks, tables, and confidence.
8. Mark failed pages for reprocessing.

Outputs:

- pages;
- text blocks;
- tables;
- OCR artifacts;
- processing errors.

### Pipeline C. Knowledge base and indexing

Purpose:

Prepare extracted content for search and RAG.

Steps:

1. Normalize text.
2. Split into chunks.
3. Attach source metadata.
4. Deduplicate near-identical documents and chunks.
5. Generate embeddings.
6. Store vector records.
7. Build lexical filters.
8. Run retrieval evaluation.

Outputs:

- chunks;
- embeddings;
- vector index;
- retrieval metrics.

### Pipeline D. Assistant answer generation

Purpose:

Answer engineer questions using only retrieved and cited sources.

Steps:

1. Normalize user query.
2. Detect missing context.
3. Retrieve candidate chunks.
4. Rerank candidates.
5. Generate answer from evidence.
6. Attach citations.
7. Return clarification if evidence is insufficient.

Outputs:

- answer;
- cited fragments;
- source pages;
- confidence/limitations note.

### Pipeline E. Requirement comparison

Purpose:

Highlight possible mismatches between normative requirements and project/specification values.

Steps:

1. Extract candidate values from project document.
2. Retrieve relevant normative requirement.
3. Normalize units and terminology where possible.
4. Compare value/condition against requirement.
5. Classify as `OK`, `WARNING`, or `POTENTIAL_MISMATCH`.
6. Show both source fragments to the engineer.

Outputs:

- comparison result;
- requirement citation;
- project document citation;
- engineer-review note.

## Dataset workstream

This workstream supports all phases and should run continuously.

Week 1:

- inventory available datasets;
- classify by source, format, and relevance.

Weeks 2-3:

- identify text PDFs vs scanned PDFs;
- select OCR validation sample.

Weeks 4-5:

- create first control query set;
- map query to expected source document/page.

Weeks 6-8:

- create comparison test cases;
- map requirement fragments to project/specification fragments.

Weeks 9-12:

- freeze demo corpus;
- collect evaluation metrics;
- document known gaps.

## Acceptance metrics

Target MVP metrics:

- at least 90% of factual answers include source document and page;
- at least 80% of control queries return relevant source in top 3;
- typical answer time for indexed documents is no more than 10 seconds where infrastructure allows;
- scanned/low-text pages are either OCR-processed or explicitly flagged as problematic;
- comparison results are always marked as engineer-review aids, not final decisions.

