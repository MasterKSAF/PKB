"""
E2E pipeline test: Upload -> Preview -> Approve -> Full pipeline -> Search.
Waits for preview before approve, measures timing, verifies document in search.

Usage:
    python data/tests/test_e2e.py

Requires: docker services up (gateway, orchestrator, celery-worker, etc.)
"""
import io, requests, time, uuid, hashlib, sys, json
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from config import get_api_url, ensure_services

ensure_services("all")

GW = get_api_url()
PDF = Path("data/pdf/7bd97d737317a8a272bb18a405ab2d04.pdf")
print(f"Target: {GW}")

EXPECTED_TEXTS = ["шкурка шлифовальная", "зеленого карбида кремния", "ГОСТ 10054"]
SEMANTIC_QUERIES = ["из какого карбида кремния"]

timings = {}

step = 0
def log(msg):
    global step; step += 1
    print(f"\n=== STEP {step}: {msg} ===")
    sys.stdout.flush()

def fail(msg):
    print(f"  [FAIL] {msg}")
    sys.stdout.flush()
    sys.exit(1)

# --- Auth ---------------------------------------------------------------
log("Auth")
r = requests.post(f"{GW}/auth/token", json={"username":"admin@example.com","password":"Admin1234!"})
assert r.status_code == 200, f"Auth failed: {r.status_code}"
h = {"Authorization": f"Bearer {r.json()['access_token']}"}
print("  OK")

# --- Upload -------------------------------------------------------------
log("Upload PDF")
t0 = time.time()
file_hash = hashlib.sha256(open(PDF,"rb").read()).hexdigest()
with open(PDF,"rb") as f:
    r = requests.post(f"{GW}/drafts",
        files={"file": (PDF.name, f, "application/pdf")},
        data={"document_key":file_hash,"source_type":"GOST","title":"GOST 10054-82","doc_code":"10054-82","era":"USSR"},
        headers={**h, "Idempotency-Key": str(uuid.uuid4())})
assert r.status_code in (200, 202), f"Upload failed: {r.status_code}"
draft_id = r.json()["draft_id"]
task_id = r.json().get("task_id")
timings["upload"] = time.time() - t0
print(f"  draft_id={draft_id}, task_id={task_id} ({timings['upload']:.1f}s)")

# --- Start Preview ------------------------------------------------------
log("Start preview")
t0 = time.time()
r = requests.post(f"{GW}/drafts/{draft_id}/preview", headers=h)
assert r.status_code in (200, 202), f"Preview start failed: {r.status_code}"
print("  OK")

# --- Wait for preview ---------------------------------------------------
log("Wait for preview completion")
for i in range(60):
    r = requests.get(f"{GW}/drafts/{draft_id}/preview/status?longpoll=0", headers=h)
    if r.status_code != 200:
        time.sleep(2); continue
    s = r.json().get("status","")
    pp = r.json().get("progress_percent", 0)
    if i < 3 or i % 5 == 0 or s in ("completed","failed"):
        print(f"  [{i+1}] status={s} progress={pp}%")
    if s == "completed":
        timings["preview"] = time.time() - t0
        meta = r.json().get("preview", {})
        print(f"  Preview completed ({timings['preview']:.1f}s)")
        print(f"    doc_code={meta.get('doc_code')}, pages={meta.get('pages')}")
        break
    if s in ("failed","error"):
        fail(f"Preview failed: {r.json()}")
    time.sleep(2)
else:
    fail("Preview timeout")

# --- Approve (with retry on 409) ----------------------------------------
log("Approve draft")
t0 = time.time()
for attempt in range(10):
    r = requests.patch(f"{GW}/drafts/{draft_id}/decide", json={"action":"approve"}, headers=h)
    if r.status_code in (200, 202):
        timings["approve"] = time.time() - t0
        resp = r.json()
        task_id = resp.get("task_id") or task_id
        doc_id = resp.get("document_id")
        print(f"  Approved: task_id={task_id}, document_id={doc_id} ({timings['approve']:.1f}s)")
        break
    if r.status_code == 409:
        print(f"  Attempt {attempt+1}: HTTP 409 (conflict), retrying in 3s...")
        time.sleep(3)
        continue
    fail(f"Approve failed: HTTP {r.status_code} {r.text[:200]}")
else:
    fail("Approve timeout after 10 attempts")

# Fetch task_id if not set
if not task_id:
    r2 = requests.get(f"{GW}/drafts/{draft_id}/tasks", headers=h)
    tasks = r2.json().get("tasks", [])
    task_id = tasks[0]["task_id"] if tasks else None
assert task_id, "No task_id found"
print(f"  Final task_id={task_id}")

# --- Wait for full pipeline ---------------------------------------------
log("Wait for full pipeline completion (poll every 5s, timeout 180s)")
t0 = time.time()
for i in range(36):
    r = requests.get(f"{GW}/tasks/{task_id}/status", headers=h)
    if r.status_code != 200:
        time.sleep(5); continue
    d = r.json()
    s = d.get("status","")
    stage = d.get("pipeline_stage","")
    progress = d.get("progress_percent", 0)
    steps = {st["step_name"]: st["status"] for st in d.get("steps",[])}
    if i < 3 or i % 5 == 0 or s in ("completed","failed"):
        print(f"  [{i+1}] status={s:12s} stage={stage:20s} {progress}% steps={steps}")
    if s == "completed":
        timings["pipeline"] = time.time() - t0
        print(f"  Pipeline completed ({timings['pipeline']:.1f}s)")
        break
    if s == "failed":
        fail(f"Pipeline failed: {d.get('error_message', '')}")
    time.sleep(5)
else:
    fail("Pipeline timeout")

# --- Verify document in registry ----------------------------------------
log("Verify document in registry")
if doc_id:
    r = requests.get(f"{GW}/registry/documents/{doc_id}", headers=h)
    if r.status_code == 200:
        doc = r.json().get("data", {})
        print(f"  Document id={doc.get('id')}, status={doc.get('status')}")
        print(f"  title={doc.get('title')}, doc_code={doc.get('doc_code')}")
        print(f"  chunks={doc.get('chunk_count', 'N/A')}")
        assert doc.get("status") in ("active", "validating"), f"Bad doc status: {doc.get('status')}"
else:
    # Find the document by hash
    r = requests.get(f"{GW}/registry/documents?page_size=20", headers=h)
    docs = r.json().get("data", [])
    for d in docs:
        if d.get("document_key") == file_hash or d.get("file_hash_sha256") == file_hash:
            doc_id = d["id"]
            print(f"  Found document id={doc_id}, status={d.get('status')}")
            break
    assert doc_id, "Document not found in registry"

# --- Search -------------------------------------------------------------
log("Search for document text")
all_found = True
total_time = sum(timings.values())
timings["total"] = total_time

for query in EXPECTED_TEXTS + SEMANTIC_QUERIES:
    r = requests.post(f"{GW}/rag/search", json={"query":query,"valid_at":"2025-01-01"},
        headers={**h,"Content-Type":"application/json; charset=utf-8"})
    if r.status_code != 200:
        print(f"  Search failed ({r.status_code}): {r.text[:200]}")
        all_found = False
        continue
    data = r.json()
    results = data.get("results", [])
    total = data.get("total_found", 0)
    print(f"  '{query}' — total_found={total}, results_in_response={len(results)}")
    if results:
        for i, rr in enumerate(results[:2]):
            content = rr["source"].get("content","")[:150]
            score = rr["retrieval"].get("score","?")
            print(f"    [{i+1}] score={score:.3f} content={content}")

    found = total > 0
    print(f"  {'[OK]' if found else '[FAIL]'} total_found={total}")
    if not found: all_found = False

# --- Final report -------------------------------------------------------
print(f"\n{'='*60}")
print(f"  E2E TEST RESULTS")
print(f"{'='*60}")
print(f"  Timings:")
for phase, sec in timings.items():
    print(f"    {phase:12s}: {sec:.1f}s")
print(f"  Document ID:   {doc_id}")
print(f"  Draft ID:      {draft_id}")
print(f"  Task ID:       {task_id}")
print(f"  File:          {PDF.name}")
print(f"  SHA256:        {file_hash[:20]}...")
print(f"{'='*60}")

if all_found:
    print(f"\n  [PASS] ALL CHECKS PASSED")
    sys.exit(0)
else:
    print(f"\n  [FAIL] SOME CHECKS FAILED")
    sys.exit(1)
