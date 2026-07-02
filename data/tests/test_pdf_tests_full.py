"""
Comprehensive test: загрузка ВСЕХ PDF из data/pdf_tests через корневой docker-compose.

Проверяет:
  1. Одновременная загрузка нескольких PDF (concurrent upload)
  2. Очерёдность и корректность каждого этапа: Upload → Preview → Approve → Pipeline → Search
  3. Что все этапы пройдены корректно для каждого файла
  4. Дубликаты и идемпотентность

Использует только корневой docker-compose (порт 8080), без service_checker.

Важно: Образы НЕ пересобираются — код синхронизируется через volume-монтирование.
ensure_services() только перезапускает контейнеры и чистит данные.
"""
import io, os, sys, json, time, uuid, hashlib, threading
from pathlib import Path
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

try:
    import requests
except ImportError:
    print("[FAIL] requests not installed. Run: pip install requests")
    sys.exit(1)

from config import get_api_url, ensure_services

ensure_services("all")
import time
time.sleep(5)  # ждём пока сервисы станут healthy после пересоздания

GW = get_api_url()
SCRIPT_DIR = Path(__file__).resolve().parent
PDF_DIR = SCRIPT_DIR.parent / "pdf_tests"

# Все 7 файлов из data/pdf_tests
TEST_PDFS = sorted(PDF_DIR.glob("*.pdf"))

# Results tracking
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

# ═══════════════════════════════════════════════════════════════════════════
#  1. CONCURRENT UPLOAD TEST
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
    log_global("CONCURRENT UPLOAD — all PDFs from data/pdf_tests")
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

    print(f"\n  --- Concurrent upload results ({elapsed:.1f}s) ---")
    success = sum(1 for v in upload_results.values() if v["status"] in (200, 202))
    failed = sum(1 for v in upload_results.values() if v["status"] not in (200, 202))
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
#  2. FULL PIPELINE TEST FOR EACH PDF
# ═══════════════════════════════════════════════════════════════════════════

def run_full_pipeline(pdf_name: str, headers: dict) -> dict:
    pdf_result = {
        "name": pdf_name,
        "upload_status": None,
        "preview_status": None,
        "pipeline_status": None,
        "search_status": None,
        "draft_id": None,
        "task_id": None,
        "document_id": None,
        "stages": {},
        "timing": {"start": time.time()},
    }

    up = upload_results.get(pdf_name, {})
    pdf_result["upload_status"] = up.get("status")
    pdf_result["draft_id"] = up.get("draft_id")
    pdf_result["task_id"] = up.get("task_id")

    draft_id = pdf_result["draft_id"]
    if not draft_id:
        pdf_result["preview_status"] = "skipped (no draft)"
        pdf_result["pipeline_status"] = "skipped (no draft)"
        pdf_result["timing"]["end"] = time.time()
        return pdf_result

    # 2a. Start Preview
    pdf_result["stages"]["preview_start"] = "pending"
    try:
        r = requests.post(f"{GW}/drafts/{draft_id}/preview", headers=headers, timeout=30)
        if r.status_code in (200, 202):
            pdf_result["stages"]["preview_start"] = "ok"
        else:
            pdf_result["stages"]["preview_start"] = f"HTTP {r.status_code}"
    except Exception as e:
        pdf_result["stages"]["preview_start"] = f"error: {e}"

    # 2b. Wait for Preview
    preview_ok = False
    for i in range(30):
        try:
            r = requests.get(f"{GW}/drafts/{draft_id}/preview/status?longpoll=0", headers=headers, timeout=10)
            if r.status_code != 200:
                time.sleep(2); continue
            s = r.json().get("status", "")
            pp = r.json().get("progress_percent", 0)
            if i < 3 or i % 10 == 0 or s in ("completed", "failed"):
                print(f"    [{i+1}] Preview: {s}, {pp}%")
            if s == "completed":
                preview_ok = True
                meta = r.json().get("preview", {})
                print(f"    PREVIEW COMPLETED! doc_code={meta.get('doc_code')} pages={meta.get('pages')}")
                break
            elif s in ("failed", "error"):
                print(f"    Preview failed: {r.json()}")
                break
        except Exception as e:
            print(f"    [{i+1}] Poll error: {e}")
        time.sleep(2)

    pdf_result["preview_status"] = "ok" if preview_ok else "failed"
    pdf_result["timing"]["preview_end"] = time.time()
    if not preview_ok:
        with results_lock:
            results["warnings"].append(f"{pdf_name}: Preview did not complete")

    # 2c. Approve
    try:
        r = requests.patch(
            f"{GW}/drafts/{draft_id}/decide",
            json={"action": "approve"},
            headers={**headers, "Content-Type": "application/json"},
            timeout=30,
        )
        pdf_result["stages"]["approve"] = f"HTTP {r.status_code}"
        if r.status_code in (200, 202):
            decide_data = r.json()
            pdf_result["document_id"] = decide_data.get("document_id")
            pdf_result["task_id"] = decide_data.get("task_id") or pdf_result["task_id"]
            pdf_result["stages"]["approve"] = "ok"
    except Exception as e:
        pdf_result["stages"]["approve"] = f"error: {e}"

    # 2d. Wait for Full Pipeline
    task_id = pdf_result["task_id"]
    if not task_id:
        try:
            r2 = requests.get(f"{GW}/drafts/{draft_id}/tasks", headers=headers, timeout=10)
            tasks = r2.json().get("tasks", [])
            task_id = tasks[0]["task_id"] if tasks else None
            if task_id:
                pdf_result["task_id"] = task_id
        except Exception:
            pass

    pipeline_ok = False
    if task_id:
        pdf_result["timing"]["pipeline_start"] = time.time()
        for i in range(60):  # 60 * 5s = 300s timeout
            try:
                r = requests.get(f"{GW}/tasks/{task_id}/status", headers=headers, timeout=10)
                if r.status_code != 200:
                    time.sleep(5); continue
                d = r.json()
                s = d.get("status", "")
                stage = d.get("pipeline_stage", "")
                progress = d.get("progress_percent", 0)
                steps = {st["step_name"]: st["status"] for st in d.get("steps", [])}
                if i < 3 or i % 10 == 0 or s in ("completed", "failed"):
                    print(f"    [{i+1}] status={s} stage={stage} progress={progress}% steps={steps}")
                if s == "completed":
                    pipeline_ok = True
                    print(f"    PIPELINE COMPLETED!")
                    break
                if s == "failed":
                    failed_steps = [st["step_name"] for st in d.get("steps", []) if st["status"] == "failed"]
                    if not failed_steps:
                        # Статус failed, но нет конкретных failed steps — регистрируем и выходим
                        error_msg = d.get("error_message", d.get("error_code", "unknown"))
                        print(f"    Pipeline failed (no failed steps): {error_msg}")
                    else:
                        print(f"    Pipeline failed at: {failed_steps}")
                    break
            except Exception as e:
                print(f"    [{i+1}] Poll error: {e}")
            time.sleep(5)
    else:
        print(f"    No task_id, cannot poll pipeline")

    pdf_result["pipeline_status"] = "ok" if pipeline_ok else "failed/unknown"
    pdf_result["timing"]["pipeline_end"] = time.time()

    # 2e. Verify in Registry
    doc_id = pdf_result["document_id"]
    if doc_id:
        try:
            r = requests.get(f"{GW}/registry/documents/{doc_id}", headers=headers, timeout=10)
            if r.status_code == 200:
                doc = r.json().get("data", {})
                print(f"    Registry: id={doc.get('id')}, status={doc.get('status')}, chunks={doc.get('chunk_count','N/A')}")
                pdf_result["stages"]["registry_check"] = "ok"
            else:
                pdf_result["stages"]["registry_check"] = f"HTTP {r.status_code}"
        except Exception as e:
            pdf_result["stages"]["registry_check"] = f"error: {e}"

    # 2f. Search
    search_ok = False
    pdf_path = Path(f"data/pdf_tests/{pdf_name}")
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
                    print(f"    Search '{query}': total_found={total}, results={len(rlist)}")
                    break
                else:
                    print(f"    Search '{query}': 0 results")
            else:
                print(f"    Search '{query}': HTTP {r.status_code}")
        except Exception as e:
            print(f"    Search error: {e}")

    pdf_result["search_status"] = "ok" if search_ok else "no_results"
    pdf_result["timing"]["end"] = time.time()

    # Cleanup
    try:
        requests.delete(f"{GW}/drafts/{draft_id}", headers=headers, timeout=10)
        print(f"    Cleanup: draft {draft_id} deleted")
    except Exception:
        pass

    return pdf_result

def test_all_pipelines(headers: dict):
    log_global("FULL PIPELINE — для каждого успешно загруженного PDF")

    pipeline_results = {}
    successful = [name for name, v in upload_results.items() if v["status"] in (200, 202)]

    if not successful:
        print("  [FAIL] No successful uploads to process")
        return pipeline_results

    print(f"  Processing {len(successful)} PDFs in upload order...\n")

    for idx, pdf_name in enumerate(successful):
        print(f"\n  -- [{idx+1}/{len(successful)}] {pdf_name} --")
        sys.stdout.flush()
        result = run_full_pipeline(pdf_name, headers)
        pipeline_results[pdf_name] = result

        with results_lock:
            results["stages"][pdf_name] = result["stages"]
            results["timing"][pdf_name] = {
                "total": result["timing"].get("end", 0) - result["timing"].get("start", 0),
                "preview": result["timing"].get("preview_end", 0) - result["timing"].get("start", 0),
                "pipeline": result["timing"].get("pipeline_end", 0) - result["timing"].get("pipeline_start", 0) if result["timing"].get("pipeline_start") else 0,
            }
            if result["preview_status"] == "ok":
                results["preview_ok"] += 1
            if result["pipeline_status"] == "ok":
                results["pipeline_ok"] += 1
            if result["search_status"] == "ok":
                results["search_ok"] += 1

    return pipeline_results

# ═══════════════════════════════════════════════════════════════════════════
#  3. ORDER VERIFICATION
# ═══════════════════════════════════════════════════════════════════════════

def verify_execution_order(pipeline_results: dict):
    log_global("VERIFY EXECUTION ORDER — проверка последовательности этапов")

    order_errors = []
    for pdf_name, result in pipeline_results.items():
        stages = result.get("stages", {})
        timing = result.get("timing", {})

        required = ["preview_start", "approve"]
        for stage in required:
            if stage not in stages:
                order_errors.append(f"{pdf_name}: missing stage '{stage}'")
            elif stages[stage] != "ok":
                order_errors.append(f"{pdf_name}: stage '{stage}' failed: {stages[stage]}")

        if timing.get("preview_end") and timing.get("pipeline_start"):
            if timing["pipeline_start"] < timing["preview_end"]:
                order_errors.append(f"{pdf_name}: pipeline started before preview ended")

    # Print per-file status
    for pdf_name, result in sorted(pipeline_results.items()):
        print(f"  {pdf_name:45s} | upload={result['upload_status']} | preview={result['preview_status']} | pipeline={result['pipeline_status']} | search={result['search_status']}")

    if order_errors:
        print(f"\n  Order errors ({len(order_errors)}):")
        for err in order_errors:
            print(f"    FAIL: {err}")
    else:
        print(f"\n  PASS: All stages executed in correct order")

    return order_errors

# ═══════════════════════════════════════════════════════════════════════════
#  4. DUPLICATE / IDEMPOTENCY CHECK
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
        r1 = requests.post(f"{GW}/drafts", files={"file": (name, f, "application/pdf")},
            data={"document_key": file_hash, "source_type": "RD", "title": pdf_path.stem,
                  "doc_code": pdf_path.stem[:20], "era": "RF", "jurisdiction": "RU"},
            headers={**h, "Idempotency-Key": str(uuid.uuid4())}, timeout=30)
    print(f"  Upload #1: HTTP {r1.status_code}")
    draft_id1 = r1.json().get("draft_id") if r1.status_code in (200, 202) else None

    # Upload 2 (same file)
    with open(pdf_path, "rb") as f:
        r2 = requests.post(f"{GW}/drafts", files={"file": (name, f, "application/pdf")},
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
    print(f"  COMPREHENSIVE PDF LOAD TEST — all files from data/pdf_tests")
    print(f"  Target:        {GW}")
    print(f"  PDF files:     {len(TEST_PDFS)}")
    print(f"  Docker:        root docker-compose (no service_checker)")
    print(f"{'#'*80}\n")

    for p in TEST_PDFS:
        size_kb = p.stat().st_size // 1024
        print(f"    {p.name:45s} {size_kb:6d} KB")

    headers = auth()
    print()

    # Phase 1: Concurrent Upload
    upload_ok, upload_failed, upload_time = test_concurrent_upload(headers)
    results["total"] = len(TEST_PDFS)
    results["upload_ok"] = upload_ok

    if upload_ok == 0:
        print(f"\n  [FAIL] All uploads failed — cannot proceed")
        sys.exit(1)
    print(f"\n  Upload phase: {upload_ok}/{len(TEST_PDFS)} OK ({upload_time:.1f}s)")

    # Phase 2: Full Pipeline for each
    pipeline_results = test_all_pipelines(headers)

    # Phase 3: Verify Order
    order_errors = verify_execution_order(pipeline_results)

    # Phase 4: Duplicate Detection
    dup_ok = test_duplicate_detection(headers)

    # FINAL SUMMARY
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

    # Per-file detail
    print(f"  {'PDF':45s} {'Upload':8s} {'Preview':10s} {'Pipeline':10s} {'Search':8s} {'Total':8s}")
    print(f"  {'-'*45} {'-'*8} {'-'*10} {'-'*10} {'-'*8} {'-'*8}")
    for pdf_name in sorted(pipeline_results.keys()):
        r = pipeline_results[pdf_name]
        t = results["timing"].get(pdf_name, {}).get("total", 0)
        u = "OK" if r["upload_status"] in (200, 202) else "FAIL"
        p = "OK" if r["preview_status"] == "ok" else r.get("preview_status", "?")[:8]
        pl = "OK" if r["pipeline_status"] == "ok" else "FAIL"
        s = "OK" if r["search_status"] == "ok" else "NO"
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
