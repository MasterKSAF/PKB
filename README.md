# PKB Neuroassistant — Ingestion MVP

This repo contains an MVP implementation of the **document loading & ingestion**
pipeline described in `Eugene_Rizov/*.md`.

## Quickstart

1) Create a virtualenv (recommended) and install deps:

```bash
python -m venv .venv
.venv\\Scripts\\activate
python -m pip install -r requirements.txt
```

2) Configure environment (optional):

- Copy `.env.example` to `.env` and adjust `ARTIFACT_ROOT`
- By default artifacts are stored in `./data_artifacts` (gitignored)
- Optional: set `RAW_ROOT` if your input data root is not `./data_raw`

3) Run API:

```bash
python -m uvicorn neuroassistant.api.app:app --reload
```

Open:
- `http://127.0.0.1:8000/` (default page with report links)
- `http://127.0.0.1:8000/docs` (OpenAPI)

## Reports (URLs)

- `GET /api/reports` (index)
- `GET /api/reports/usage` (JSON)
- `GET /api/reports/usage.html` (HTML)
- `GET /api/reports/load` (detail load report JSON from `data_raw/drive_ingestion_report.json`)
- `GET /api/reports/load/summary` (summary)
- `GET /api/reports/load/errors` (errors only)

## Browse loaded dataset (Drive unzip folder)

- `GET /api/data/drive.html` (HTML list of `.xlsx` files)
- `GET /api/data/drive/files` (JSON list)
- `GET /api/data/drive/xlsx?filename=<name>.xlsx&max_rows=200` (JSON preview)

## Dataset download + unzip + load

To download the provided public Drive folder, unzip and ingest all files while
tracking errors:

```bash
python scripts/download_unzip_load.py
```

Outputs:
- `data_raw/drive_ingestion_report.json` (summary report)
- `data_artifacts/<document_id>/<ingestion_id>/logs/events.jsonl` (per-run event log)

## Run with local PostgreSQL 17 + start web

This script creates the DB (if missing), applies `schema_postgres.sql`, sets
`DATABASE_URL`, and starts the API:

```powershell
.\scripts\run_with_postgres17.ps1 -DbPassword "admin"
```

## Load local folder via the running API

Uploads up to N files from a folder and prints progress after each file:

```bash
python scripts/load_folder_via_api.py --folder data_raw/drive_dataset_unzipped --max-files 10
```

