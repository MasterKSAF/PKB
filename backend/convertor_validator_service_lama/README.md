# convertor_validator_service_lama

LAMA Document Parser service for the PKB convertor/validator pipeline.

## Responsibility

This service is block 1 of the document processing pipeline.

Input:
- source PDF

Main flow:
- LlamaParse processes the original PDF
- service stores parse_job_id and raw artifacts
- LlamaExtract passes work by parse_job_id
- Python validator/assembler builds rich_document_package.json
- Python validator/critic creates quality_report and correction_proposals

Out of scope for the document parser part of this service:
- RAG indexing
- search
- writing to the knowledge DB
- creating embeddings

The service may also expose adapter/export endpoints for the orchestrator.
Those adapter endpoints must not reduce the full `rich_document_package.json` contract.
They only prepare payloads for the current downstream service contract.

## Configuration

Use `.env.example` as a template for local configuration:

- `LAMA_CLOUD_API_KEY`
- `LAMA_PARSE_BASE_URL`
- `LAMA_EXTRACT_BASE_URL`
- `LAMA_EXTRACT_PROJECT_ID`
- `LAMA_PARSE_RESULT_FORMAT`

## Current API

- GET /health
- GET /dry-run
- POST /parse-job
- POST /parse-job/dry-run
- POST /extract-pass
- POST /extract-passes
- POST /extract-pass/dry-run
- POST /extract-passes/dry-run
- GET /extract-passes/plan
- POST /rich-document-package
- POST /rich-document-package/dry-run
- GET /rich-document-package/plan
- POST /rag-builder-payload

## LlamaParse REST scope

`POST /parse-job` executes the LlamaParse REST upload/polling flow through `httpx`:

- uploads the source PDF to LlamaCloud
- starts a parse job
- polls the parse job until completed, failed, cancelled, or timed out
- returns the raw parse result artifacts

It does not run LlamaExtract passes yet.
It does not build `rich_document_package.json` yet.

Normal unit tests use mocked `httpx` transports and do not call LlamaCloud.

`POST /parse-job` maps expected failures to HTTP responses:

- missing `LAMA_CLOUD_API_KEY` -> 400
- missing source PDF -> 404
- LlamaCloud response/job failure -> 502
- polling timeout -> 504

## LlamaExtract REST scope

`POST /extract-pass` executes one LlamaExtract REST pass by `parse_job_id`.

`POST /extract-passes` executes all planned LlamaExtract passes by `parse_job_id`:

- document_boundaries
- title_metadata
- table_of_contents
- sections
- tables
- images
- formulas
- cross_references
- validation_critic

Both endpoints use `httpx`, require `LAMA_CLOUD_API_KEY` and `LAMA_EXTRACT_PROJECT_ID`, and return raw extract artifacts.

They do not build `rich_document_package.json` yet.
They do not implement downcast to RAG Builder-compatible JSON.

Expected failures are mapped to HTTP responses:

- missing API key or extract project id -> 400
- LlamaCloud response/job failure -> 502
- polling timeout -> 504

## Rich document package assembly scope

`POST /rich-document-package` assembles a local `rich_document_package.json` structure from already available artifacts:

- LlamaParse `parse_result`
- LlamaExtract `extract_results`
- parse markdown/items/metadata/job_metadata
- extract pass results
- `quality_report` and `correction_proposals` from `validation_critic`, when available

This endpoint does not call LlamaCloud.
It does not run LlamaParse or LlamaExtract jobs.
It does not implement downcast to RAG Builder-compatible JSON.

Final corrections are still owned by the Python validator/assembler policy: `python_validator_assembler_applies_final_corrections`.

### Full document structure

The assembled package now includes a first-class `document_structure` block.

This block is part of the full document model and is not limited by the current RAG Builder contract.

It may contain:

- `document_boundaries`
- `table_of_contents`
- `nested_documents`
- `sections`
- `tables`
- `images`
- `formulas`
- `cross_references`
- `quality_report`
- `correction_proposals`

Tables may preserve nested cell content through table cells with embedded images and formulas.

The original raw artifacts are still preserved in `artifacts`.
The normalized `document_structure` exists alongside raw artifacts to provide a stable full-document structure for downstream validators, adapters, and future services.

## Document package boundary

`rich_document_package.json` is the full logical document container produced by the parser/validator pipeline.

It is the source of truth for the parsed document structure.

It must preserve document entities even when the current RAG Builder version cannot consume them directly, including:

- table of contents
- nested documents
- document boundaries
- sections
- tables
- images
- images inside table cells
- formulas
- cross_references
- validation reports
- correction proposals
- raw parser/extractor artifacts

The RAG Builder adapter/export layer is allowed to transform this full structure into a payload suitable for the current RAG Builder contract.

When the current RAG Builder cannot represent part of the full document structure, the adapter should either preserve it in raw content fields or return explicit warnings.

As RAG Builder evolves, the adapter/downcast layer may change.
The full `rich_document_package.json` contract should remain richer than any single downstream consumer.

## RAG Builder payload export scope

`POST /rag-builder-payload` exports an adapter payload for the current RAG Builder version from an already assembled `rich_document_package.json` structure.

This endpoint is an adapter/exporter for the orchestrator.
It is not the canonical document model.
The canonical document model is `rich_document_package.json`.

It does:

- accept `RichDocumentPackage`
- map document metadata
- map sections
- map tables
- map images
- map formulas
- map cross_references
- return `RagBuilderDowncastResult`
- return warnings for missing optional source artifacts

It does not:

- call RAG Builder
- call LlamaCloud
- run OCR
- run LlamaParse
- run LlamaExtract
- write to the knowledge DB
- create embeddings
- run indexing

RAG Builder execution is owned by the orchestrator.

The adapter may be changed when the RAG Builder contract changes.
The full document package should not be simplified to match only the current RAG Builder capabilities.

## Dry-run scope

Dry-run endpoints build contracts and payload previews only.

They do not call LlamaParse or LlamaExtract over the network.

The service uses a LlamaCloud network boundary for REST integration:

- validates that `LAMA_CLOUD_API_KEY` exists before real network calls
- builds authorization headers
- keeps request-preview helpers for dry-run/debug flows

## Local usage

Install dependencies:

```powershell
.\venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Run tests:

```powershell
.\venv\Scripts\python.exe -m pytest
```

Run API locally:

```powershell
.\venv\Scripts\python.exe -m uvicorn convertor_validator_service_lama.api.app:app --reload
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

## Tests

Current local status:

- 101 passed
- 1 warning from FastAPI/TestClient dependency stack
