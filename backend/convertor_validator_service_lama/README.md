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

Out of scope for this service:
- downcast to RAG Builder JSON
- RAG indexing
- search

## Configuration

Use `.env.example` as a template for local configuration:

- `LAMA_CLOUD_API_KEY`
- `LAMA_PARSE_BASE_URL`
- `LAMA_EXTRACT_BASE_URL`
- `LAMA_PARSE_RESULT_FORMAT`

## Current API

- GET /health
- GET /dry-run
- POST /parse-job
- POST /parse-job/dry-run
- POST /extract-pass/dry-run
- POST /extract-passes/dry-run
- GET /extract-passes/plan
- POST /rich-document-package/dry-run
- GET /rich-document-package/plan

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

- 34 passed
- 1 warning from FastAPI/TestClient dependency stack
