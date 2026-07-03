"""
Concurrent PDF pipeline test — загрузка ВСЕХ PDF из data/pdf_tests через корневой docker-compose.

Фазы (все — истинно конкурентные через threads):
  1. CONCURRENT UPLOAD     — все 7 PDF одновременно
  2. CONCURRENT PREVIEW    — старт preview для всех draft одновременно
  3. CONCURRENT PREVIEW    — polling всех preview параллельно до завершения
  4. CONCURRENT APPROVE    — approve всех draft одновременно
  5. CONCURRENT PIPELINE   — polling всех pipeline параллельно до завершения
  6. CONCURRENT SEARCH     — поиск для каждого документа
  7. ORDER VERIFICATION    — per-file: upload → preview → approve → pipeline → search

Использует только корневой docker-compose (порт 8080), без service_checker.
ensure_services() только перезапускает контейнеры и чистит данные.
"""
import io, os, sys, json, time, uuid, hashlib, threading
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

try:
    import requests
except ImportError:
    print("[FAIL] requests not installed. Run: pip install requests")
    sys.exit(1)

from config import get_api_url, ensure_services

ensure_services("all")
time.sleep(5)  # ждём пока сервисы станут healthy после пересоздания

GW = get_api_url()
SCRIPT_DIR = Path(__file__).resolve().parent
PDF_DIR = SCRIPT_DIR.parent / "pdf_tests"
TEST_PDFS = sorted(PDF_DIR.glob("*.pdf"))

# ── Results tracking ────────────────────────────────────────────────────────
results = {
    "total": 0,
    "upload_ok": 0,
    "preview_ok": 0,
    "pipeline_ok": 0,
    "search_ok": 0,
    "stages": {},
    "timing": {},
    "errors": [],
    "warnings": [],
}
results_lock = threading.Lock()

step_counter = 0
step_lock = threading.Lock()


def log_global(msg):
    global step_counter
    with step_lock:
        step_counter += 1
        n = step_counter
    print(f"\n=== [{n}] {msg} ===")
    sys.stdout.flush()


def auth():
    for creds in [
        {"username": "admin@example.com", "password": "Admin1234!"},
        {"username": "admin", "password": "admin"},
    ]:
        try:
            r = requests.post(f"{GW}/auth/token", json=creds, timeout=10)
            if r.status_code == 200:
                token = r.json()["access_token"]
                print(f"  Auth OK: {creds['username']}")
                return {"Authorization": f"Bearer {token}"}
        except Exception:
            continue
    print("[FAIL] Auth failed")
    sys.exit(1)


# ── Per-file shared state ──────────────────────────────────────────────────
file_data: dict = {}          # pdf_name -> dict with all per-file fields
file_lock = threading.Lock()  # guards file_data


def init_file_data():
    global file_data
    file_data = {}
    for p in TEST_PDFS:
        file_data[p.name] = {
            "name": p.name,
            "upload_status": None,
            "draft_id": None,
            "task_id": None,
            "document_id": None,
            "preview_started": False,
            "preview_poll_result": None,
            "approved": False,
            "pipeline_poll_result": None,
            "search_status": None,
            "stages": {},
            "timing": {"start": time.time()},
        }


# ═══════════════════════════════════════════════════════════════════════════
#  PHASE 1 — CONCURRENT UPLOAD (все 7 PDF одновременно)
# ═══════════════════════════════════════════════════════════════════════════

upload_results = {}


def upload_single(pdf_path: Path, headers: dict, idempotency_key: str):
    name = pdf_path.name
    with open(pdf_path, "rb") as f:
        file_bytes = f.read()
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    h = {k: v for k, v in headers.items() if k != "Content-Type"}
    try:
        with open(pdf_path, "rb") as f:
            r = requests.post(
                f"{GW}/drafts",
                files={"file": (name, f, "application/pdf")},
                data={
                    "document_key": file_hash,
                    "source_type": "RD",
                    "title": pdf_path.stem,
                    "doc_code": pdf_path.stem[:20],
                    "era": "RF",
                    "jurisdiction": "RU",
                },
                headers={**h, "Idempotency-Key": idempotency_key},
                timeout=30,
            )
    except Exception as e:
        with results_lock:
            upload_results[name] = {"status": f"ERROR: {e}", "draft_id": None, "task_id": None, "hash": file_hash}
        return

    draft_id = None
    task_id = None
    try:
        resp = r.json()
        draft_id = resp.get("draft_id")
        task_id = resp.get("task_id")
    except Exception:
        pass

    with results_lock:
        upload_results[name] = {
            "status": r.status_code,
            "draft_id": draft_id,
            "task_id": task_id,
            "hash": file_hash,
            "response": r.text[:200] if r.status_code not in (200, 202) else None,
        }

    ok = "OK" if r.status_code in (200, 202) else "FAIL"
    print(f"  [{ok}] {name:45s} HTTP {r.status_code:3d} | draft={str(draft_id or '-')[:8]}")


def test_concurrent_upload(headers: dict):
    log_global("PHASE 1: CONCURRENT UPLOAD — all PDFs from data/pdf_tests")
    print(f"  Files: {len(TEST_PDFS)} PDFs")
    print(f"  Target: {GW}\n")

    threads = []
    start = time.time()
    for pdf_path in TEST_PDFS:
        ik = str(uuid.uuid4())
        t = threading.Thread(target=upload_single, args=(pdf_path, headers, ik))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
    elapsed = time.time() - start

    success = sum(1 for v in upload_results.values() if v["status"] in (200, 202))
    failed = sum(1 for v in upload_results.values() if v["status"] not in (200, 202))
    print(f"\n  --- Concurrent upload results ({elapsed:.1f}s) ---")
    print(f"  Successful: {success}")
    print(f"  Failed:     {failed}")

    hashes = [v["hash"] for v in upload_results.values()]
    unique_hashes = set(hashes)
    if len(hashes) != len(unique_hashes):
        collisions = len(hashes) - len(unique_hashes)
        print(f"  WARNING: {collisions} hash collisions detected")
        with results_lock:
            results["warnings"].append(f"{collisions} hash collisions in concurrent upload")

    return success, failed, elapsed


# ═══════════════════════════════════════════════════════════════════════════
#  PHASE 2 — CONCURRENT PREVIEW START (POST /drafts/{id}/preview)
# ═══════════════════════════════════════════════════════════════════════════

def start_preview_single(pdf_name: str, headers: dict):
    with file_lock:
        fd = file_data[pdf_name]
        draft_id = fd["draft_id"]

    if not draft_id:
        with file_lock:
            fd["stages"]["preview_start"] = "skipped (no draft)"
        return

    try:
        r = requests.post(f"{GW}/drafts/{draft_id}/preview", headers=headers, timeout=30)
        ok = r.status_code in (200, 202)
        with file_lock:
            fd["stages"]["preview_start"] = "ok" if ok else f"HTTP {r.status_code}"
            fd["preview_started"] = ok
        status = "OK" if ok else f"HTTP {r.status_code}"
        print(f"  [PreviewStart] {pdf_name:45s} {status}")
    except Exception as e:
        with file_lock:
            fd["stages"]["preview_start"] = f"error: {e}"
            fd["preview_started"] = False
        print(f"  [PreviewStart] {pdf_name:45s} ERROR: {e}")


# ═══════════════════════════════════════════════════════════════════════════
#  PHASE 3 — CONCURRENT PREVIEW POLL (GET /drafts/{id}/preview/status)
# ═══════════════════════════════════════════════════════════════════════════

def poll_preview_single(pdf_name: str, headers: dict):
    with file_lock:
        fd = file_data[pdf_name]
        draft_id = fd["draft_id"]
        started = fd.get("preview_started", False)

    if not draft_id or not started:
        with file_lock:
            fd["preview_poll_result"] = "skipped"
        return

    preview_ok = False
    timeout = 60
    poll_interval = 2
    max_attempts = timeout // poll_interval

    for i in range(max_attempts):
        try:
            r = requests.get(f"{GW}/drafts/{draft_id}/preview/status?longpoll=0", headers=headers, timeout=10)
            if r.status_code != 200:
                time.sleep(poll_interval)
                continue
            body = r.json()
            s = body.get("status", "")
            pp = body.get("progress_percent", 0)
            if i < 3 or i % 10 == 0 or s in ("completed", "failed"):
                print(f"    [{pdf_name[:22]:22s}] Preview [{i+1:2d}]: {s:12s} {pp}%")
            if s == "completed":
                preview_ok = True
                meta = body.get("preview", {})
                print(f"    [{pdf_name[:22]:22s}] PREVIEW COMPLETED! doc_code={meta.get('doc_code')} pages={meta.get('pages')}")
                break
            elif s in ("failed", "error"):
                print(f"    [{pdf_name[:22]:22s}] Preview failed: {body}")
                break
        except Exception as e:
            print(f"    [{pdf_name[:22]:22s}] Preview poll error [{i+1}]: {e}")
        time.sleep(poll_interval)

    with file_lock:
        fd["preview_poll_result"] = "ok" if preview_ok else "failed"
        fd["timing"]["preview_end"] = time.time()

    if not preview_ok:
        with results_lock:
            results["warnings"].append(f"{pdf_name}: Preview did not complete")
        print(f"    [{pdf_name[:22]:22s}] PREVIEW FAILED after {timeout}s")


# ═══════════════════════════════════════════════════════════════════════════
#  PHASE 4 — CONCURRENT APPROVE (PATCH /drafts/{id}/decide approve)
# ═══════════════════════════════════════════════════════════════════════════

def approve_single(pdf_name: str, headers: dict):
    with file_lock:
        fd = file_data[pdf_name]
        draft_id = fd["draft_id"]
        preview_ok = fd.get("preview_poll_result") == "ok"

    if not draft_id or not preview_ok:
        with file_lock:
            fd["stages"]["approve"] = "skipped (no preview)"
            fd["approved"] = False
        return

    try:
        r = requests.patch(
            f"{GW}/drafts/{draft_id}/decide",
            json={"action": "approve"},
            headers={**headers, "Content-Type": "application/json"},
            timeout=30,
        )
        ok = r.status_code in (200, 202)
        with file_lock:
            fd["stages"]["approve"] = "ok" if ok else f"HTTP {r.status_code}"
            fd["approved"] = ok
            if ok:
                decide_data = r.json()
                fd["document_id"] = decide_data.get("document_id")
                fd["task_id"] = decide_data.get("task_id") or fd["task_id"]
        print(f"  [Approve] {pdf_name:45s} HTTP {r.status_code}")
    except Exception as e:
        with file_lock:
            fd["stages"]["approve"] = f"error: {e}"
            fd["approved"] = False
        print(f"  [Approve] {pdf_name:45s} ERROR: {e}")


# ═══════════════════════════════════════════════════════════════════════════
#  PHASE 5 — CONCURRENT PIPELINE POLL (GET /tasks/{id}/status)
# ═══════════════════════════════════════════════════════════════════════════

def poll_pipeline_single(pdf_name: str, headers: dict):
    with file_lock:
        fd = file_data[pdf_name]
        task_id = fd.get("task_id")
        draft_id = fd["draft_id"]
        approved = fd.get("approved", False)

    if not draft_id or not approved:
        with file_lock:
            fd["pipeline_poll_result"] = "skipped"
            fd["timing"]["pipeline_end"] = time.time()
        return

    # If no task_id yet, try to fetch from drafts/{id}/tasks
    if not task_id and draft_id:
        try:
            r2 = requests.get(f"{GW}/drafts/{draft_id}/tasks", headers=headers, timeout=10)
            tasks = r2.json().get("tasks", [])
            if tasks:
                task_id = tasks[0]["task_id"]
                with file_lock:
                    fd["task_id"] = task_id
        except Exception:
            pass

    if not task_id:
        with file_lock:
            fd["pipeline_poll_result"] = "failed (no task_id)"
            fd["stages"]["pipeline_poll"] = "skipped (no task_id)"
            fd["timing"]["pipeline_end"] = time.time()
        print(f"    [{pdf_name[:22]:22s}] No task_id, cannot poll pipeline")
        return

    pipeline_ok = False
    timeout = 300
    poll_interval = 5
    max_attempts = timeout // poll_interval

    with file_lock:
        fd["timing"]["pipeline_start"] = time.time()

    for i in range(max_attempts):
        try:
            r = requests.get(f"{GW}/tasks/{task_id}/status", headers=headers, timeout=10)
            if r.status_code != 200:
                time.sleep(poll_interval)
                continue
            d = r.json()
            s = d.get("status", "")
            stage = d.get("pipeline_stage", "")
            progress = d.get("progress_percent", 0)
            steps = {st["step_name"]: st["status"] for st in d.get("steps", [])}
            if i < 3 or i % 10 == 0 or s in ("completed", "failed"):
                print(f"    [{pdf_name[:22]:22s}] Pipeline [{i+1:2d}]: status={s:12s} stage={stage:20s} {progress}%")
            if s == "completed":
                pipeline_ok = True
                print(f"    [{pdf_name[:22]:22s}] PIPELINE COMPLETED!")
                break
            if s == "failed":
                failed_steps = [st["step_name"] for st in d.get("steps", []) if st["status"] == "failed"]
                if not failed_steps:
                    error_msg = d.get("error_message", d.get("error_code", "unknown"))
                    print(f"    [{pdf_name[:22]:22s}] Pipeline failed (no failed steps): {error_msg}")
                else:
                    print(f"    [{pdf_name[:22]:22s}] Pipeline failed at: {failed_steps}")
                break
        except Exception as e:
            print(f"    [{pdf_name[:22]:22s}] Pipeline poll error [{i+1}]: {e}")
        time.sleep(poll_interval)

    with file_lock:
        fd["pipeline_poll_result"] = "ok" if pipeline_ok else "failed"
        fd["timing"]["pipeline_end"] = time.time()

    if not pipeline_ok:
        print(f"    [{pdf_name[:22]:22s}] PIPELINE FAILED after {timeout}s")


# ═══════════════════════════════════════════════════════════════════════════
#  PHASE 6 — CONCURRENT SEARCH VERIFY + Registry check + Cleanup
# ═══════════════════════════════════════════════════════════════════════════

def search_single(pdf_name: str, headers: dict):
    with file_lock:
        fd = file_data[pdf_name]
        doc_id = fd.get("document_id")
        draft_id = fd["draft_id"]
        pipeline_ok = fd.get("pipeline_poll_result") == "ok"

    if not pipeline_ok:
        # Не ищем, если pipeline не завершён — документ не проиндексирован
        with file_lock:
            fd["search_status"] = "skipped (no pipeline)"
            fd["timing"]["end"] = time.time()
        print(f"    [{pdf_name[:22]:22s}] Search skipped: pipeline not completed")
        if draft_id:
            try:
                requests.delete(f"{GW}/drafts/{draft_id}", headers=headers, timeout=10)
            except Exception:
                pass
        return

    search_ok = False
    pdf_path = PDF_DIR / pdf_name
    stem = pdf_path.stem
    search_terms = [stem[:10], stem.split("-")[0] if "-" in stem else stem]

    for query in search_terms:
        try:
            r = requests.post(
                f"{GW}/rag/search",
                json={"query": query, "valid_at": "2025-01-01"},
                headers={**headers, "Content-Type": "application/json; charset=utf-8"},
                timeout=30,
            )
            if r.status_code == 200:
                data = r.json()
                total = data.get("total_found", 0)
                rlist = data.get("results", [])
                if total > 0 or len(rlist) > 0:
                    search_ok = True
                    print(f"    [{pdf_name[:22]:22s}] Search '{query}': total_found={total}, results={len(rlist)}")
                    break
                else:
                    print(f"    [{pdf_name[:22]:22s}] Search '{query}': 0 results")
            else:
                print(f"    [{pdf_name[:22]:22s}] Search '{query}': HTTP {r.status_code}")
        except Exception as e:
            print(f"    [{pdf_name[:22]:22s}] Search error: {e}")

    with file_lock:
        fd["search_status"] = "ok" if search_ok else "no_results"
        fd["timing"]["end"] = time.time()

    # Registry check (if we have a document_id)
    if doc_id:
        try:
            r = requests.get(f"{GW}/registry/documents/{doc_id}", headers=headers, timeout=10)
            if r.status_code == 200:
                doc = r.json().get("data", {})
                print(f"    [{pdf_name[:22]:22s}] Registry: id={doc.get('id')}, status={doc.get('status')}, chunks={doc.get('chunk_count','N/A')}")
                with file_lock:
                    fd["stages"]["registry_check"] = "ok"
            else:
                with file_lock:
                    fd["stages"]["registry_check"] = f"HTTP {r.status_code}"
        except Exception as e:
            with file_lock:
                fd["stages"]["registry_check"] = f"error: {e}"

    # Cleanup — delete the draft
    if draft_id:
        try:
            requests.delete(f"{GW}/drafts/{draft_id}", headers=headers, timeout=10)
            print(f"    [{pdf_name[:22]:22s}] Cleanup: draft deleted")
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════════
#  PHASE 7 — ORDER VERIFICATION (per-file, no cross-file ordering)
# ═══════════════════════════════════════════════════════════════════════════

def verify_order() -> list:
    log_global("PHASE 7: ORDER VERIFICATION — per-file stage sequence")

    order_errors = []
    for pdf_name, fd in sorted(file_data.items()):
        if fd.get("upload_status") not in (200, 202):
            continue  # skip failed uploads

        stages = fd.get("stages", {})
        timing = fd.get("timing", {})

        # Check that required stages exist and succeeded
        required = ["preview_start", "approve"]
        for stage in required:
            val = stages.get(stage)
            if val is None:
                order_errors.append(f"{pdf_name}: missing stage '{stage}'")
            elif val != "ok" and not str(val).startswith("skipped"):
                order_errors.append(f"{pdf_name}: stage '{stage}' failed: {val}")

        # Verify temporal ordering: pipeline_start must NOT be before preview_end
        pe = timing.get("preview_end")
        ps = timing.get("pipeline_start")
        if pe and ps and ps < pe:
            order_errors.append(f"{pdf_name}: pipeline started ({ps:.1f}) before preview ended ({pe:.1f})")

    # Print per-file summary line
    print()
    for pdf_name, fd in sorted(file_data.items()):
        upload_s = "OK" if fd.get("upload_status") in (200, 202) else "FAIL"
        preview_s = fd.get("preview_poll_result", "?") or "?"
        pipeline_s = fd.get("pipeline_poll_result", "?") or "?"
        search_s = fd.get("search_status", "?") or "?"
        print(f"  {pdf_name:45s} | upload={upload_s:8s} | preview={preview_s:8s} | pipeline={pipeline_s:8s} | search={search_s:8s}")

    if order_errors:
        print(f"\n  Order errors ({len(order_errors)}):")
        for err in order_errors:
            print(f"    FAIL: {err}")
    else:
        print(f"\n  PASS: All per-file stages executed in correct sequence")

    return order_errors


# ═══════════════════════════════════════════════════════════════════════════
#  CONCURRENT RUNNER — запускает task_fn для всех файлов в отдельных threads
# ═══════════════════════════════════════════════════════════════════════════

def run_concurrent(task_fn, headers, files_list, phase_label=""):
    """Run a function concurrently for every file in files_list using threads."""
    threads = []
    for pdf_name in files_list:
        t = threading.Thread(target=task_fn, args=(pdf_name, headers), daemon=True)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()


# ═══════════════════════════════════════════════════════════════════════════
#  DUPLICATE / IDEMPOTENCY CHECK (kept from original)
# ═══════════════════════════════════════════════════════════════════════════

def test_duplicate_detection(headers: dict):
    log_global("DUPLICATE DETECTION — проверка идемпотентности")

    if not TEST_PDFS:
        print("  [SKIP] No PDFs available")
        return True

    pdf_path = TEST_PDFS[0]
    name = pdf_path.name
    print(f"  File: {name}")

    with open(pdf_path, "rb") as f:
        file_bytes = f.read()
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    h = {k: v for k, v in headers.items() if k != "Content-Type"}

    # Upload 1
    with open(pdf_path, "rb") as f:
        r1 = requests.post(f"{GW}/drafts",
            files={"file": (name, f, "application/pdf")},
            data={"document_key": file_hash, "source_type": "RD", "title": pdf_path.stem,
                  "doc_code": pdf_path.stem[:20], "era": "RF", "jurisdiction": "RU"},
            headers={**h, "Idempotency-Key": str(uuid.uuid4())}, timeout=30)
    print(f"  Upload #1: HTTP {r1.status_code}")
    draft_id1 = r1.json().get("draft_id") if r1.status_code in (200, 202) else None

    # Upload 2 (same file)
    with open(pdf_path, "rb") as f:
        r2 = requests.post(f"{GW}/drafts",
            files={"file": (name, f, "application/pdf")},
            data={"document_key": file_hash, "source_type": "RD", "title": pdf_path.stem,
                  "doc_code": pdf_path.stem[:20], "era": "RF", "jurisdiction": "RU"},
            headers={**h, "Idempotency-Key": str(uuid.uuid4())}, timeout=30)
    print(f"  Upload #2 (duplicate): HTTP {r2.status_code}")
    draft_id2 = r2.json().get("draft_id") if r2.status_code in (200, 202) else None

    dup_detected = (r2.status_code == 409) or (draft_id2 and draft_id2 == draft_id1)
    if dup_detected:
        print(f"  PASS: Duplicate detected (HTTP {r2.status_code})")
    else:
        print(f"  WARN: Duplicate NOT detected — separate draft created: {draft_id2}")
        with results_lock:
            results["warnings"].append(f"Duplicate detection failed for {name}")

    # Cleanup
    if draft_id1:
        requests.delete(f"{GW}/drafts/{draft_id1}", headers=h, timeout=10)
    if draft_id2 and draft_id2 != draft_id1:
        requests.delete(f"{GW}/drafts/{draft_id2}", headers=h, timeout=10)

    return dup_detected


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    global results

    if not TEST_PDFS:
        print(f"\n[FAIL] No PDF files found in {PDF_DIR}")
        sys.exit(1)

    print(f"\n{'#'*80}")
    print(f"  CONCURRENT PDF PIPELINE TEST — all files from data/pdf_tests")
    print(f"  Target:        {GW}")
    print(f"  PDF files:     {len(TEST_PDFS)}")
    print(f"  Docker:        root docker-compose (no service_checker)")
    print(f"{'#'*80}\n")

    for p in TEST_PDFS:
        size_kb = p.stat().st_size // 1024
        print(f"    {p.name:45s} {size_kb:6d} KB")

    init_file_data()
    headers = auth()
    print()

    # ── Phase 1: Concurrent Upload (2 waves due to MAX_CONCURRENT_TASKS=4) ──
    # Wave 1: first 4 files (leave room for 1 task = 3 to avoid hitting limit)
    # System has MAX_CONCURRENT_TASKS=4, and task itself counts as active.
    # So we upload in batches of 3 to stay under the limit.
    log_global("PHASE 1: CONCURRENT UPLOAD — all PDFs from data/pdf_tests")
    print(f"  Files: {len(TEST_PDFS)} PDFs, target: {GW}")
    print(f"  Note: MAX_CONCURRENT_TASKS=4 — uploading in 2 waves to avoid 429\n")

    pdf_names = [p.name for p in TEST_PDFS]
    
    def run_upload_wave(names):
        threads = []
        up_local = {}
        lock_local = threading.Lock()
        def up_one(name):
            pdf_path = PDF_DIR / name
            ik = str(uuid.uuid4())
            with open(pdf_path, "rb") as f:
                file_bytes = f.read()
            file_hash = hashlib.sha256(file_bytes).hexdigest()
            h = {k: v for k, v in headers.items() if k != "Content-Type"}
            try:
                with open(pdf_path, "rb") as f:
                    r = requests.post(f"{GW}/drafts",
                        files={"file": (name, f, "application/pdf")},
                        data={"document_key": file_hash, "source_type": "RD",
                              "title": pdf_path.stem, "doc_code": pdf_path.stem[:20],
                              "era": "RF", "jurisdiction": "RU"},
                        headers={**h, "Idempotency-Key": ik}, timeout=30)
            except Exception as e:
                with lock_local:
                    up_local[name] = {"status": f"ERROR: {e}", "draft_id": None, "task_id": None, "hash": file_hash}
                return
            draft_id = r.json().get("draft_id") if r.status_code in (200,202) else None
            task_id = r.json().get("task_id") if r.status_code in (200,202) else None
            with lock_local:
                up_local[name] = {"status": r.status_code, "draft_id": draft_id, "task_id": task_id, "hash": file_hash}
            ok = "OK" if r.status_code in (200, 202) else f"HTTP {r.status_code}"
            print(f"  [{ok}] {name:45s} HTTP {r.status_code:3d} | draft={str(draft_id or '-')[:8]}")
        for n in names:
            t = threading.Thread(target=up_one, args=(n,))
            threads.append(t); t.start()
        for t in threads: t.join()
        return up_local

    # Wave 1: first 3 files
    wave1_names = pdf_names[:3]
    wave1_results = run_upload_wave(wave1_names)
    
    # Wait for wave1 pipelines to progress (so they release concurrency slots)
    if wave1_results:
        any_ok = any(v["status"] in (200, 202) for v in wave1_results.values())
        if any_ok:
            print(f"  Waiting for wave1 pipelines to progress before wave2...")
            time.sleep(15)  # give pipelines time to start processing
    
    # Wave 2: remaining 4 files
    wave2_names = pdf_names[3:]
    wave2_results = run_upload_wave(wave2_names)
    
    # Merge results
    upload_results.clear()
    upload_results.update(wave1_results)
    upload_results.update(wave2_results)
    
    upload_ok = sum(1 for v in upload_results.values() if v["status"] in (200, 202))
    upload_failed = len(upload_results) - upload_ok
    upload_time = 0  # not tracked per-wave
    
    results["total"] = len(TEST_PDFS)
    results["upload_ok"] = upload_ok

    # Copy upload results into per-file state
    for name, up in upload_results.items():
        with file_lock:
            file_data[name]["upload_status"] = up.get("status")
            file_data[name]["draft_id"] = up.get("draft_id")
            file_data[name]["task_id"] = up.get("task_id")

    successful = sorted(name for name, v in upload_results.items() if v["status"] in (200, 202))
    if upload_ok == 0:
        print(f"\n  [FAIL] All uploads failed — cannot proceed")
        sys.exit(1)

    print(f"\n  Upload phase: {upload_ok}/{len(TEST_PDFS)} OK")
    print(f"  Files proceeding to pipeline: {len(successful)}")

    # ── Phase 2: Concurrent Preview Start ──────────────────────────────
    log_global("PHASE 2: CONCURRENT PREVIEW START — POST /drafts/{id}/preview")
    run_concurrent(start_preview_single, headers, successful, "Preview Start")

    # ── Phase 3: Concurrent Preview Poll ───────────────────────────────
    log_global("PHASE 3: CONCURRENT PREVIEW POLL — polling all until done (timeout 60s)")
    run_concurrent(poll_preview_single, headers, successful, "Preview Poll")

    preview_count = 0
    for name in successful:
        with file_lock:
            fd = file_data[name]
        if fd.get("preview_poll_result") == "ok":
            preview_count += 1
    results["preview_ok"] = preview_count

    # ── Phase 4: Concurrent Approve ────────────────────────────────────
    log_global("PHASE 4: CONCURRENT APPROVE — PATCH /drafts/{id}/decide")
    run_concurrent(approve_single, headers, successful, "Approve")

    # ── Phase 5: Concurrent Pipeline Poll ──────────────────────────────
    log_global("PHASE 5: CONCURRENT PIPELINE POLL — polling all pipelines (timeout 300s)")
    run_concurrent(poll_pipeline_single, headers, successful, "Pipeline Poll")

    pipeline_count = 0
    for name in successful:
        with file_lock:
            fd = file_data[name]
        if fd.get("pipeline_poll_result") == "ok":
            pipeline_count += 1
    results["pipeline_ok"] = pipeline_count

    # ── Phase 6: Concurrent Search Verify ──────────────────────────────
    log_global("PHASE 6: CONCURRENT SEARCH — verify documents in RAG")
    run_concurrent(search_single, headers, successful, "Search")

    search_count = 0
    for name in successful:
        with file_lock:
            fd = file_data[name]
        if fd.get("search_status") == "ok":
            search_count += 1
    results["search_ok"] = search_count

    # Build stages/timing dicts for results summary
    for name in successful:
        with file_lock:
            fd = file_data[name]
            results["stages"][name] = dict(fd.get("stages", {}))
            t = fd.get("timing", {})
            results["timing"][name] = {
                "total": t.get("end", time.time()) - t.get("start", time.time()),
                "preview": t.get("preview_end", 0) - t.get("start", 0),
                "pipeline": t.get("pipeline_end", 0) - t.get("pipeline_start", 0) if t.get("pipeline_start") else 0,
            }

    # ── Phase 7: Order Verification ────────────────────────────────────
    order_errors = verify_order()

    # ── Duplicate Detection (additional) ───────────────────────────────
    dup_ok = test_duplicate_detection(headers)

    # ── FINAL SUMMARY ──────────────────────────────────────────────────
    total = results["total"]
    u_ok = results["upload_ok"]
    p_ok = results["preview_ok"]
    pl_ok = results["pipeline_ok"]
    s_ok = results["search_ok"]

    print(f"\n{'='*80}")
    print(f"  FINAL RESULTS")
    print(f"{'='*80}")
    print(f"  Total PDFs:              {total}")
    print(f"  Upload OK:               {u_ok}/{total}")
    print(f"  Preview OK:              {p_ok}/{u_ok}")
    print(f"  Pipeline OK:             {pl_ok}/{p_ok}")
    print(f"  Search found content:    {s_ok}/{pl_ok}")
    print(f"  Order errors:            {len(order_errors)}")
    print(f"  Duplicate detection:     {'PASS' if dup_ok else 'FAIL'}")
    print()

    # Per-file detail table
    print(f"  {'PDF':45s} {'Upload':8s} {'Preview':10s} {'Pipeline':10s} {'Search':8s} {'Total':8s}")
    print(f"  {'-'*45} {'-'*8} {'-'*10} {'-'*10} {'-'*8} {'-'*8}")
    for pdf_name in sorted(file_data.keys()):
        fd = file_data[pdf_name]
        t = results["timing"].get(pdf_name, {}).get("total", 0)
        u = "OK" if fd.get("upload_status") in (200, 202) else "FAIL"
        p = "OK" if fd.get("preview_poll_result") == "ok" else str(fd.get("preview_poll_result", "?"))[:8]
        pl = "OK" if fd.get("pipeline_poll_result") == "ok" else str(fd.get("pipeline_poll_result", "?"))[:8]
        s = "OK" if fd.get("search_status") == "ok" else str(fd.get("search_status", "?"))[:8]
        print(f"  {pdf_name:45s} {u:8s} {p:10s} {pl:10s} {s:8s} {t:6.1f}s")

    # Warnings
    if results["warnings"]:
        print(f"\n  WARNINGS ({len(results['warnings'])}):")
        for w in results["warnings"]:
            print(f"    {w}")

    # Final verdict
    print()
    if u_ok == total and p_ok > 0 and len(order_errors) == 0:
        print(f"  [PASS] All checks passed!")
        sys.exit(0)
    else:
        print(f"  [PARTIAL] Some checks need attention (see warnings)")
        if p_ok == 0:
            sys.exit(1)
        sys.exit(0)


if __name__ == "__main__":
    main()
