"""FastAPI application for ingestion MVP."""

from __future__ import annotations

from pathlib import Path

import json

from fastapi import BackgroundTasks
from fastapi import FastAPI
from fastapi import File
from fastapi import Form
from fastapi import HTTPException
from fastapi import UploadFile
from fastapi.responses import HTMLResponse
from fastapi.responses import FileResponse

from neuroassistant.api.dataset import DatasetConfig
from neuroassistant.api.dataset import list_drive_unzipped_files
from neuroassistant.api.dataset import read_xlsx_preview
from neuroassistant.api.deps import get_pipeline
from neuroassistant.api.deps import get_repo
from neuroassistant.api.deps import get_storage
from neuroassistant.db import Base
from neuroassistant.api.deps import get_engine
from neuroassistant.api.metrics import metrics_response
from neuroassistant.api.reports import build_usage_report
from neuroassistant.api.reports import build_usage_report_from_artifacts
from neuroassistant.api.reports import render_usage_html
from neuroassistant.api.schemas import DocumentResponse
from neuroassistant.api.schemas import RunResponse
from neuroassistant.api.schemas import UploadResponse
from neuroassistant.domain import CorpusLevel
from neuroassistant.domain import DocumentMetadata
from neuroassistant.indexing.extract_text import extract_text
from neuroassistant.indexing.faiss_index import Chunk
from neuroassistant.indexing.faiss_index import build_faiss_index


app = FastAPI(title="PKB Neuroassistant Ingestion MVP")


@app.on_event("startup")
def _startup() -> None:
    # Keep startup non-blocking: DB init is exposed as an explicit endpoint.
    return


@app.post("/api/db:init")
def db_init() -> dict:
    try:
        engine = get_engine()
        Base.metadata.create_all(engine)
        return {"ok": True}
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/", response_class=FileResponse)
def root() -> FileResponse:
    frontend_path = (
        Path(__file__).resolve().parents[2] / "frontend" / "index.html"
    )
    if not frontend_path.exists():
        raise HTTPException(status_code=404, detail="frontend not found")
    return FileResponse(frontend_path)


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True}


@app.post("/api/documents:upload", response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    source: str | None = Form(default=None),
    corpus_level: str | None = Form(default=None),
    project_code: str | None = Form(default=None),
    discipline: str | None = Form(default=None),
    doc_type_hint: str | None = Form(default=None),
    version_date: str | None = Form(default=None),
    tags: str | None = Form(default=None),
) -> UploadResponse:
    data = await file.read()
    meta = DocumentMetadata(
        source=source,
        corpus_level=_parse_corpus_level(corpus_level),
        project_code=project_code,
        discipline=discipline,
        doc_type_hint=doc_type_hint,
        version_date=version_date,
        tags=[t.strip() for t in (tags or "").split(",") if t.strip()],
    )
    pipeline = get_pipeline()
    result = pipeline.register_bytes(
        filename=file.filename or "upload.bin",
        content_type=file.content_type,
        data=data,
        metadata=meta,
    )
    background_tasks.add_task(pipeline.run_existing, result.run.ingestion_id)

    return UploadResponse(
        document_id=result.document.document_id,
        ingestion_id=result.run.ingestion_id,
        status_url=f"/api/ingestions/{result.run.ingestion_id}",
        report_url=f"/api/ingestions/{result.run.ingestion_id}/report",
    )


@app.get("/api/documents/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str) -> DocumentResponse:
    repo = get_repo()
    doc = repo.get_document(document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="document not found")
    return DocumentResponse(**doc.model_dump())


@app.get("/api/documents/{document_id}/runs", response_model=list[RunResponse])
def list_document_runs(document_id: str) -> list[RunResponse]:
    repo = get_repo()
    runs = repo.list_runs_for_document(document_id)
    return [RunResponse(**r.model_dump()) for r in runs]


@app.get("/api/ingestions/{ingestion_id}", response_model=RunResponse)
def get_ingestion(ingestion_id: str) -> RunResponse:
    repo = get_repo()
    run = repo.get_run(ingestion_id)
    if run is None:
        raise HTTPException(status_code=404, detail="ingestion not found")
    return RunResponse(**run.model_dump())


@app.get("/api/ingestions/{ingestion_id}/report", response_model=dict)
def get_ingestion_report(ingestion_id: str) -> dict:
    repo = get_repo()
    run = repo.get_run(ingestion_id)
    if run is None:
        raise HTTPException(status_code=404, detail="ingestion not found")

    return {
        "ingestion_id": run.ingestion_id,
        "document_id": run.document_id,
        "status": run.status,
        "classification": run.classification.model_dump(mode="json")
        if run.classification
        else None,
        "errors": [e.model_dump(mode="json") for e in run.errors],
        "metrics": run.metrics,
    }


@app.get("/api/reports/usage")
def usage_report() -> dict:
    repo = get_repo()
    # Prefer artifact-based report so script ingestions show up.
    report = build_usage_report_from_artifacts(get_storage())
    if report.runs_total == 0:
        report = build_usage_report(repo)
    return report.model_dump(mode="json")


@app.get("/api/reports")
def reports_index() -> dict:
    return {
        "reports": [
            {
                "name": "usage",
                "json": "/api/reports/usage",
                "html": "/api/reports/usage.html",
            }
            ,
            {
                "name": "load_detail",
                "json": "/api/reports/load",
            },
            {
                "name": "load_summary",
                "json": "/api/reports/load/summary",
            },
            {
                "name": "load_errors",
                "json": "/api/reports/load/errors",
            },
        ]
    }


@app.get("/api/reports/usage.html", response_class=HTMLResponse)
def usage_report_html() -> str:
    repo = get_repo()
    report = build_usage_report_from_artifacts(get_storage())
    if report.runs_total == 0:
        report = build_usage_report(repo)
    return render_usage_html(report)


@app.get("/api/reports/load")
def load_report_detail() -> dict:
    path = Path("data_raw") / "drive_ingestion_report.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="load report not found")
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/api/reports/load/summary")
def load_report_summary() -> dict:
    report = load_report_detail()
    results = report.get("results") or []
    ok = [r for r in results if r.get("ok") is True]
    failed = [r for r in results if r.get("ok") is False]
    return {
        "ok": report.get("ok"),
        "folder_id": report.get("folder_id"),
        "zip_path": report.get("zip_path"),
        "unzip_dir": report.get("unzip_dir"),
        "files_total": report.get("files_total", len(results)),
        "files_ok": report.get("files_ok", len(ok)),
        "files_failed": report.get("files_failed", len(failed)),
    }


@app.get("/api/reports/load/errors")
def load_report_errors() -> dict:
    report = load_report_detail()
    results = report.get("results") or []
    failed = [r for r in results if r.get("ok") is False]
    return {
        "files_failed": len(failed),
        "errors": failed,
    }


@app.get("/metrics")
def metrics():
    return metrics_response()


@app.get("/api/data/drive/files")
def drive_files() -> dict:
    cfg = DatasetConfig.from_env()
    files = list_drive_unzipped_files(cfg)
    return {"count": len(files), "files": [str(p) for p in files]}


@app.get("/api/data/drive/xlsx")
def drive_xlsx_preview(filename: str, max_rows: int = 200) -> dict:
    cfg = DatasetConfig.from_env()
    base = (cfg.raw_root / "drive_dataset_unzipped").resolve()
    target = (base / filename).resolve()
    if not str(target).startswith(str(base)):
        raise HTTPException(status_code=400, detail="invalid filename")
    if not target.exists():
        raise HTTPException(status_code=404, detail="file not found")
    if target.suffix.lower() != ".xlsx":
        raise HTTPException(status_code=400, detail="only .xlsx supported here")
    max_rows = max(1, min(2000, max_rows))
    return read_xlsx_preview(target, max_rows=max_rows)


@app.get("/api/data/drive.html", response_class=HTMLResponse)
def drive_dataset_html() -> str:
    cfg = DatasetConfig.from_env()
    files = [p for p in list_drive_unzipped_files(cfg) if p.suffix.lower() == ".xlsx"]
    items = "".join(
        f'<li><a href="/api/data/drive/xlsx?filename={p.name}">{p.name}</a></li>'
        for p in files
    )
    return (
        "<!doctype html><html><head><meta charset='utf-8' />"
        "<title>Drive dataset</title></head><body>"
        "<h2>Drive dataset (unzipped)</h2>"
        "<p>Click a file to view JSON preview (first rows per sheet).</p>"
        f"<ul>{items}</ul>"
        "</body></html>"
    )


@app.post("/api/index/faiss:build")
def build_faiss_for_all_ingested() -> dict:
    storage = get_storage()
    root = storage.root().resolve()
    chunks: list[Chunk] = []
    for raw_path in root.glob("*/*/raw/*"):
        # raw_path: <root>/<doc>/<ing>/raw/<filename>
        parts = raw_path.parts
        if len(parts) < 4:
            continue
        document_id = raw_path.parents[2].name
        ingestion_id = raw_path.parents[1].name
        text = extract_text(raw_path)
        if not text.strip():
            continue
        # naive chunking
        for idx, piece in enumerate(_chunk_text(text, max_len=1200), start=1):
            chunks.append(
                Chunk(
                    chunk_id=f"{document_id}:{ingestion_id}:{idx}",
                    document_id=document_id,
                    ingestion_id=ingestion_id,
                    text=piece,
                )
            )
    out_dir = root / "_faiss"
    return build_faiss_index(chunks, out_dir=out_dir)


def _parse_corpus_level(value: str | None) -> CorpusLevel | None:
    if value is None:
        return None
    value = value.strip().upper()
    if value in {"A", "B", "C"}:
        return CorpusLevel(value)
    raise HTTPException(status_code=400, detail="invalid corpus_level")


def _chunk_text(text: str, max_len: int = 1200) -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    size = 0
    for line in text.splitlines():
        if not line.strip():
            continue
        if size + len(line) + 1 > max_len and buf:
            parts.append("\n".join(buf))
            buf = []
            size = 0
        buf.append(line)
        size += len(line) + 1
    if buf:
        parts.append("\n".join(buf))
    return parts

