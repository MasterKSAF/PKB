"""
Dup Check — Duplicate PDF Upload Detection Test.

Загружает один и тот же PDF дважды и проверяет, детектирует ли система дубликат.
Не требует полного pipeline (только upload).

Использует только корневой docker-compose (порт 8080), без service_checker.

Usage:
    python data/tests/test_dup_check.py data/pdf/2-020101-004.pdf
    python data/tests/test_dup_check.py data/pdf/2-020101-004.pdf data/pdf/2-020101-006.pdf
"""
import io, os, sys, json, time, uuid, hashlib
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

try:
    import requests
except ImportError:
    print("[FAIL] requests not installed. Run: pip install requests")
    sys.exit(1)

from config import get_api_url

GW = get_api_url()

# ─── Configuration ────────────────────────────────────────────────────
AUTH_USER = os.environ.get("TEST_AUTH_USER", "admin@example.com")
AUTH_PASS = os.environ.get("TEST_AUTH_PASS", "Admin1234!")

# Default PDFs if none provided
DEFAULT_PDFS = [
    "data/pdf/2-020101-004.pdf",
    "data/pdf/2-020101-006.pdf",
    "data/pdf/2-020101-063.pdf",
]


def auth(headers_only=False):
    """Auth and return headers dict."""
    for creds in [
        {"username": AUTH_USER, "password": AUTH_PASS},
        {"username": "admin", "password": "admin"},
    ]:
        r = requests.post(f"{GW}/auth/token", json=creds, timeout=10)
        if r.status_code == 200:
            token = r.json()["access_token"]
            h = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            print(f"  Auth OK: {creds['username']}")
            return h
    print("[FAIL] Auth failed")
    sys.exit(1)


def upload(pdf_path: Path, headers: dict, idempotency_key: str = None) -> tuple:
    """
    Upload a PDF. Returns (status_code, response_json, draft_id).
    Does NOT clean up stale drafts — we want to test what the system does.
    """
    with open(pdf_path, "rb") as f:
        file_bytes = f.read()
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    meta = {
        "document_key": file_hash,
        "source_type": "RD",
        "title": pdf_path.stem,
        "doc_code": pdf_path.stem[:20],
        "era": "RF",
        "jurisdiction": "RU",
    }
    headers_upload = {k: v for k, v in headers.items() if k != "Content-Type"}
    ik = idempotency_key or str(uuid.uuid4())

    with open(pdf_path, "rb") as f:
        r = requests.post(
            f"{GW}/drafts",
            files={"file": (pdf_path.name, f, "application/pdf")},
            data=meta,
            headers={**headers_upload, "Idempotency-Key": ik},
            timeout=30,
        )

    draft_id = None
    resp = {}
    try:
        resp = r.json()
        draft_id = resp.get("draft_id")
    except Exception:
        resp = {"raw": r.text[:200]}

    return r.status_code, resp, draft_id


def cleanup_draft(draft_id: str, headers: dict):
    """Delete draft by ID."""
    h = {k: v for k, v in headers.items()}
    h.pop("Content-Type", None)
    try:
        r = requests.delete(f"{GW}/drafts/{draft_id}", headers=h, timeout=10)
        print(f"  Cleanup draft {draft_id}: HTTP {r.status_code}")
    except Exception as e:
        print(f"  Cleanup error: {e}")


def list_drafts(headers: dict) -> list:
    """List all drafts."""
    try:
        r = requests.get(f"{GW}/drafts", headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json().get("data", [])
    except Exception:
        pass
    return []


def test_single_dup(pdf_path: Path, headers: dict) -> dict:
    """Test duplicate detection for a single PDF. Returns result dict."""
    print(f"\n{'='*60}")
    print(f"  TEST DUP: {pdf_path.name}")
    print(f"{'='*60}")

    result = {
        "pdf": pdf_path.name,
        "size": pdf_path.stat().st_size,
        "first_status": None,
        "second_status": None,
        "first_draft_id": None,
        "second_draft_id": None,
        "dup_detected": False,  # True if system returned 409 or same doc
        "same_draft": False,    # True if both uploads returned same draft_id
    }

    # Upload #1
    print("\n  --- Upload #1 ---")
    status1, resp1, draft1 = upload(pdf_path, headers)
    result["first_status"] = status1
    result["first_draft_id"] = draft1
    print(f"  HTTP {status1}, draft_id={draft1}")
    if resp1:
        for k in ["message", "detail"]:
            if k in resp1:
                print(f"  Response: {resp1[k]}")

    # If first upload failed, nothing more to test
    if status1 not in (200, 201, 202) or not draft1:
        print(f"  [WARN] First upload failed, skipping duplicate test")
        return result

    # Upload #2 — same file, same document_key
    print("\n  --- Upload #2 (same file, expected duplicate) ---")
    status2, resp2, draft2 = upload(pdf_path, headers)
    result["second_status"] = status2
    result["second_draft_id"] = draft2
    print(f"  HTTP {status2}, draft_id={draft2}")
    if resp2:
        for k in ["message", "detail"]:
            if k in resp2:
                print(f"  Response: {resp2[k]}")

    # Analyze
    if status2 == 409:
        result["dup_detected"] = True
        print("  ✓ DUPLICATE DETECTED (HTTP 409)")
    elif draft2 == draft1:
        result["same_draft"] = True
        result["dup_detected"] = True
        print("  ✓ DUPLICATE DETECTED (same draft_id returned)")
    elif status2 in (200, 201, 202) and draft2 != draft1:
        print("  ✗ DUPLICATE NOT DETECTED — second upload created a new draft")
        # List drafts to show both exist
        drafts = list_drafts(headers)
        matching = [d for d in drafts if d.get("document_key") == resp1.get("document_key")]
        print(f"  Drafts with same document_key: {len(matching)}")
        for d in matching:
            print(f"    id={d['id']}, status={d.get('status')}")
    else:
        print(f"  ? Unexpected status: {status2}")

    # Cleanup both drafts
    if draft1:
        cleanup_draft(draft1, headers)
    if draft2 and draft2 != draft1:
        cleanup_draft(draft2, headers)

    return result


def main():
    # Collect PDFs to test
    pdf_args = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_PDFS
    pdfs = [Path(p).resolve() for p in pdf_args]

    for p in pdfs:
        if not p.exists():
            print(f"[FAIL] File not found: {p}")
            sys.exit(1)

    print(f"\n{'#'*60}")
    print(f"  DUP CHECK — дублирующая загрузка PDF")
    print(f"  Target: {GW}")
    print(f"  PDFs:   {len(pdfs)} files")
    print(f"{'#'*60}")

    headers = auth()

    all_results = []
    for pdf in pdfs:
        # Get a fresh auth token for each test
        r = test_single_dup(pdf, headers)
        all_results.append(r)
        time.sleep(1)  # brief pause between tests

    # ─── Summary ────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    total = len(pdfs)
    detected = sum(1 for r in all_results if r["dup_detected"])
    not_detected = total - detected

    print(f"  Total PDFs tested: {total}")
    print(f"  Duplicates detected: {detected}")
    print(f"  Duplicates NOT detected: {not_detected}")

    for r in all_results:
        status = "✓ DETECTED" if r["dup_detected"] else "✗ NOT DETECTED"
        print(f"    {r['pdf']:40s} | HTTP 1st={r['first_status']} 2nd={r['second_status']} | {status}")

    if not_detected > 0:
        print(f"\n  [FAIL] System does not block duplicate uploads for {not_detected}/{total} files")
        sys.exit(1)
    else:
        print(f"\n  [PASS] Duplicate detection works correctly")
        sys.exit(0)


if __name__ == "__main__":
    main()
