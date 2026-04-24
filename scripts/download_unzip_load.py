"""Download a public Google Drive folder, unzip, and ingest files.

This script is designed for the dataset folder shared in the project docs.
It keeps a structured error report in JSON and relies on the same artifact
storage + pipeline event logs as the API.
"""

from __future__ import annotations

import json
import shutil
import sys
import traceback
import zipfile
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path

import gdown

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from neuroassistant.document_loader.pipeline import IngestionPipeline
from neuroassistant.domain import DocumentMetadata
from neuroassistant.repositories import InMemoryRepository
from neuroassistant.storage.artifacts import LocalArtifactStorage


@dataclass(frozen=True, slots=True)
class FileLoadResult:
    path: str
    ok: bool
    document_id: str | None = None
    ingestion_id: str | None = None
    error_type: str | None = None
    message: str | None = None
    stacktrace: str | None = None


def main() -> int:
    folder_id = "1qBlnHuLlYRSD77FVN5U392wFtQBgUgWN"
    raw_dir = Path("data_raw").resolve()
    out_dir = raw_dir / "drive_dataset"
    unzip_dir = raw_dir / "drive_dataset_unzipped"
    report_path = raw_dir / "drive_ingestion_report.json"

    out_dir.mkdir(parents=True, exist_ok=True)
    unzip_dir.mkdir(parents=True, exist_ok=True)

    results: list[FileLoadResult] = []

    try:
        gdown.download_folder(
            id=folder_id,
            output=str(out_dir),
            quiet=False,
            use_cookies=False,
        )
    except Exception:  # noqa: BLE001
        report_path.write_text(
            json.dumps(
                {
                    "ok": False,
                    "stage": "download_folder",
                    "error": traceback.format_exc(),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return 2

    zips = sorted(out_dir.glob("**/*.zip"))
    if not zips:
        report_path.write_text(
            json.dumps(
                {"ok": False, "stage": "discover_zip", "error": "no zip found"},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return 3

    # For now we process the first ZIP (as per dataset listing)
    zip_path = zips[0]
    try:
        _safe_unzip(zip_path, unzip_dir)
    except Exception:  # noqa: BLE001
        report_path.write_text(
            json.dumps(
                {
                    "ok": False,
                    "stage": "unzip",
                    "zip_path": str(zip_path),
                    "error": traceback.format_exc(),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return 4

    repo = InMemoryRepository()
    storage = LocalArtifactStorage.from_env()
    pipeline = IngestionPipeline(repo=repo, storage=storage)

    files = [p for p in unzip_dir.rglob("*") if p.is_file()]
    for path in files:
        try:
            data = path.read_bytes()
            meta = DocumentMetadata(source="google_drive")
            res = pipeline.ingest_bytes(
                filename=path.name,
                content_type=None,
                data=data,
                metadata=meta,
            )
            results.append(
                FileLoadResult(
                    path=str(path),
                    ok=True,
                    document_id=res.document.document_id,
                    ingestion_id=res.run.ingestion_id,
                )
            )
        except Exception as e:  # noqa: BLE001
            results.append(
                FileLoadResult(
                    path=str(path),
                    ok=False,
                    error_type=type(e).__name__,
                    message=str(e),
                    stacktrace=traceback.format_exc(),
                )
            )

    report = {
        "ok": True,
        "folder_id": folder_id,
        "download_dir": str(out_dir),
        "zip_path": str(zip_path),
        "unzip_dir": str(unzip_dir),
        "files_total": len(files),
        "files_ok": sum(1 for r in results if r.ok),
        "files_failed": sum(1 for r in results if not r.ok),
        "results": [asdict(r) for r in results],
    }
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return 0


def _safe_unzip(zip_path: Path, out_dir: Path) -> None:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.infolist():
            if member.filename.endswith("/"):
                continue
            dest = (out_dir / member.filename).resolve()
            if not str(dest).startswith(str(out_dir.resolve())):
                raise ValueError("unsafe zip path traversal detected")
        zf.extractall(out_dir)


if __name__ == "__main__":
    raise SystemExit(main())

