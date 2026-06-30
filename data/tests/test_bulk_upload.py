"""
Bulk Upload Test — tests upload of ALL PDFs from data/pdf/ directory.

For each PDF:
  1. Upload (POST /drafts)
  2. Parse HTTP status code and response
  3. Delete draft afterwards (cleanup)

Проверяет что все PDF принимаются API без ошибок.
Не запускает полный pipeline (только upload).
Только корневой docker-compose (порт 8080), без service_checker.

Usage:
    python data/tests/test_bulk_upload.py
    python data/tests/test_bulk_upload.py data/pdf/  # all PDFs in directory
"""
import io, os, sys, json, time, uuid, hashlib, re
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

try:
    import requests
except ImportError:
    print("[FAIL] requests not installed. Run: pip install requests")
    sys.exit(1)

from config import get_api_url

GW = get_api_url()
PDF_DIR = Path("data/pdf")

# Results tracking
results = {
    "total": 0,
    "success": 0,
    "failed": 0,
    "errors": [],
    "warnings": [],
}


def auth():
    for creds in [
        {"username": "admin@example.com", "password": "Admin1234!"},
        {"username": "admin", "password": "admin"},
    ]:
        r = requests.post(f"{GW}/auth/token", json=creds, timeout=10)
        if r.status_code == 200:
            token = r.json()["access_token"]
            return {"Authorization": f"Bearer {token}"}
    print("[FAIL] Auth failed")
    sys.exit(1)


def upload_and_cleanup(pdf_path: Path, headers: dict):
    """Upload a PDF and immediately delete the created draft."""
    with open(pdf_path, "rb") as f:
        file_bytes = f.read()
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    file_size = len(file_bytes)

    # Upload
    h = {k: v for k, v in headers.items() if k != "Content-Type"}
    try:
        with open(pdf_path, "rb") as f:
            r = requests.post(
                f"{GW}/drafts",
                files={"file": (pdf_path.name, f, "application/pdf")},
                data={
                    "document_key": file_hash,
                    "source_type": "RD",
                    "title": pdf_path.stem,
                    "doc_code": pdf_path.stem[:20],
                    "era": "RF",
                    "jurisdiction": "RU",
                },
                headers={**h, "Idempotency-Key": str(uuid.uuid4())},
                timeout=30,
            )
    except requests.Timeout:
        return "TIMEOUT", None, file_size
    except Exception as e:
        return f"ERROR: {e}", None, file_size

    draft_id = None
    try:
        resp = r.json()
        draft_id = resp.get("draft_id")
    except Exception:
        resp = {"raw": r.text[:200]}

    # Cleanup
    if draft_id:
        try:
            requests.delete(f"{GW}/drafts/{draft_id}", headers=h, timeout=10)
        except Exception:
            pass

    return r.status_code, draft_id, file_size


def main():
    # Collect all PDFs
    pdfs = sorted(PDF_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"[FAIL] No PDF files found in {PDF_DIR}")
        sys.exit(1)

    print(f"\n{'#'*70}")
    print(f"  BULK UPLOAD TEST — all PDFs in {PDF_DIR}")
    print(f"  Target: {GW}")
    print(f"  Total:  {len(pdfs)} files")
    print(f"{'#'*70}\n")

    headers = auth()

    # Summary tracking by file patterns
    patterns = {
        "plain": {"files": [], "ok": 0, "fail": 0},
        "with_001": {"files": [], "ok": 0, "fail": 0},  # split parts
        "with_-E": {"files": [], "ok": 0, "fail": 0},    # edition variants
        "hash_name": {"files": [], "ok": 0, "fail": 0},  # uuid/md5 filenames
    }

    for pdf_path in pdfs:
        name = pdf_path.name
        status_code, draft_id, file_size = upload_and_cleanup(pdf_path, headers)
        results["total"] += 1

        # Classify
        if "_001" in name:
            cat = "with_001"
        elif "-E" in name:
            cat = "with_-E"
        elif re.match(r'^[0-9a-f]{32}\.', name) or re.match(r'^[0-9A-F-]{36}', name):
            cat = "hash_name"
        else:
            cat = "plain"

        patterns[cat]["files"].append(name)

        if status_code == 202:
            results["success"] += 1
            patterns[cat]["ok"] += 1
            status_str = "✓"
        elif status_code == 200:
            results["success"] += 1
            patterns[cat]["ok"] += 1
            status_str = "✓(200)"
        else:
            results["failed"] += 1
            patterns[cat]["fail"] += 1
            status_str = "✗"
            err = f"HTTP {status_code} | {name} | draft_id={draft_id}"
            results["errors"].append(err)

        size_kb = file_size // 1024
        print(f"  {status_str} HTTP {status_code:3d} | {size_kb:6d} KB | draft={str(draft_id or '-'):5s} | {name}")

    # ─── Summary ────────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  BULK UPLOAD SUMMARY")
    print(f"{'='*70}")
    print(f"  Total PDFs:  {results['total']}")
    print(f"  Upload OK:   {results['success']}")
    print(f"  Upload FAIL: {results['failed']}")
    print(f"")

    for cat_name, cat_data in patterns.items():
        total_cat = cat_data["ok"] + cat_data["fail"]
        if total_cat == 0:
            continue
        ok_pct = cat_data["ok"] / total_cat * 100
        print(f"  {cat_name:15s}: {total_cat:3d} files | ✓{cat_data['ok']:3d} ✗{cat_data['fail']:d} ({ok_pct:.0f}%)")

    if results["errors"]:
        print(f"\n  ERRORS ({len(results['errors'])}):")
        for err in results["errors"][:10]:
            print(f"    {err}")

    if results["failed"] > 0:
        print(f"\n  [FAIL] {results['failed']} uploads failed")
        sys.exit(1)
    else:
        print(f"\n  [PASS] All {results['total']} PDFs uploaded successfully")
        sys.exit(0)


if __name__ == "__main__":
    main()
