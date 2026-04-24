"""Load documents from a local folder via the running API.

Uploads files to POST /api/documents:upload and prints progress per file.

Usage:
  python scripts/load_folder_via_api.py --folder data_raw/drive_dataset_unzipped
  python scripts/load_folder_via_api.py --folder data_raw/drive_dataset_unzipped --max-files 50
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from dataclasses import asdict
from pathlib import Path
from typing import Any

import requests


@dataclass(frozen=True, slots=True)
class UploadResult:
    path: str
    ok: bool
    document_id: str | None = None
    ingestion_id: str | None = None
    status: str | None = None
    error: str | None = None


TERMINAL_STATUSES = {
    "completed",
    "completed_with_errors",
    "failed",
}


def main() -> int:
    args = _parse_args()
    folder = Path(args.folder).resolve()
    if not folder.exists():
        raise SystemExit(f"Folder not found: {folder}")

    files = [p for p in sorted(folder.rglob("*")) if p.is_file()]
    files = files[: args.max_files]
    if not files:
        print("No files found to upload.")
        return 0

    base = args.api_base.rstrip("/")
    results: list[UploadResult] = []

    print(f"Uploading {len(files)} file(s) to {base} ...")

    for idx, path in enumerate(files, start=1):
        print(f"[{idx}/{len(files)}] Uploading: {path.name}")
        try:
            res = _upload_file(base, path)
            ingestion_id = res["ingestion_id"]
            document_id = res["document_id"]
            status = _wait_for_status(
                base,
                ingestion_id,
                timeout_s=args.timeout_s,
                poll_s=args.poll_s,
            )
            print(
                f"  -> document_id={document_id} ingestion_id={ingestion_id} "
                f"status={status}"
            )
            results.append(
                UploadResult(
                    path=str(path),
                    ok=True,
                    document_id=document_id,
                    ingestion_id=ingestion_id,
                    status=status,
                )
            )
        except Exception as e:  # noqa: BLE001
            print(f"  !! failed: {e}")
            results.append(UploadResult(path=str(path), ok=False, error=str(e)))

    summary = {
        "folder": str(folder),
        "api_base": base,
        "max_files": args.max_files,
        "total": len(results),
        "ok": sum(1 for r in results if r.ok),
        "failed": sum(1 for r in results if not r.ok),
        "results": [asdict(r) for r in results],
    }
    out_path = Path(args.out).resolve()
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved report: {out_path}")
    return 0


def _upload_file(api_base: str, path: Path) -> dict[str, Any]:
    url = f"{api_base}/api/documents:upload"
    with path.open("rb") as f:
        resp = requests.post(url, files={"file": (path.name, f)})
    if resp.status_code >= 400:
        raise RuntimeError(f"upload failed: {resp.status_code} {resp.text}")
    return resp.json()


def _wait_for_status(
    api_base: str,
    ingestion_id: str,
    timeout_s: int,
    poll_s: float,
) -> str:
    url = f"{api_base}/api/ingestions/{ingestion_id}"
    deadline = time.time() + timeout_s
    last_status = "unknown"
    while time.time() < deadline:
        resp = requests.get(url)
        if resp.status_code >= 400:
            raise RuntimeError(f"status check failed: {resp.status_code} {resp.text}")
        payload = resp.json()
        last_status = str(payload.get("status") or "unknown")
        if last_status in TERMINAL_STATUSES:
            return last_status
        time.sleep(poll_s)
    return last_status


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--folder", required=True, help="Folder with files to upload")
    p.add_argument(
        "--max-files",
        type=int,
        default=10,
        help="Max number of files to upload (default: 10)",
    )
    p.add_argument(
        "--api-base",
        default="http://127.0.0.1:8000",
        help="API base URL (default: http://127.0.0.1:8000)",
    )
    p.add_argument(
        "--timeout-s",
        type=int,
        default=60,
        help="Max seconds to wait for each ingestion run to finish",
    )
    p.add_argument(
        "--poll-s",
        type=float,
        default=0.5,
        help="Polling interval in seconds (default: 0.5)",
    )
    p.add_argument(
        "--out",
        default="data_raw/folder_upload_report.json",
        help="Where to write JSON summary report",
    )
    args = p.parse_args()
    if args.max_files < 1:
        raise SystemExit("--max-files must be >= 1")
    return args


if __name__ == "__main__":
    raise SystemExit(main())

