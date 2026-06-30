"""
E2E pipeline test: Upload → Preview → Approve → Full pipeline → Search.

Minimal test: starts preview, immediately approves (doesn't wait for preview),
then polls until full pipeline completes, searches for known text.

Usage:
    python data/tests/test_e2e.py

Requires: docker services up and running (gateway, orchestrator, celery-worker, etc.)
"""
import io, requests, time, uuid, hashlib, sys, json
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from config import get_api_url, get_direct_rag_url, ensure_services

ensure_services("all")

GW = get_api_url()
PDF = Path("data/pdf/7bd97d737317a8a272bb18a405ab2d04.pdf")
print(f"Target: {GW}")
EXPECTED_TEXTS = ["шкурка шлифовальная", "зеленого карбида кремния", "ГОСТ 10054"]
SEMANTIC_QUERIES = ["из какого карбида кремния"]

step = 0
def log(msg):
    global step; step += 1
    print(f"\n=== STEP {step}: {msg} ===")
    sys.stdout.flush()

# ─── Auth ───────────────────────────────────────────────────────────────
log("Auth")
r = requests.post(f"{GW}/auth/token", json={"username":"admin@example.com","password":"Admin1234!"})
assert r.status_code == 200, f"Auth failed: {r.status_code}"
h = {"Authorization": f"Bearer {r.json()['access_token']}"}
print("  OK")

# ─── Upload ─────────────────────────────────────────────────────────────
log("Upload PDF")
file_hash = hashlib.sha256(open(PDF,"rb").read()).hexdigest()
with open(PDF,"rb") as f:
    r = requests.post(f"{GW}/drafts",
        files={"file": (PDF.name, f, "application/pdf")},
        data={"document_key":file_hash,"source_type":"GOST","title":"GOST 10054-82","doc_code":"10054-82","era":"USSR"},
        headers={**h, "Idempotency-Key": str(uuid.uuid4())})
assert r.status_code in (200, 202), f"Upload failed: {r.status_code}"
draft_id = r.json()["draft_id"]
print(f"  draft_id={draft_id}")

# ─── Start Preview (don't wait) ─────────────────────────────────────────
log("Start preview")
r = requests.post(f"{GW}/drafts/{draft_id}/preview", headers=h)
assert r.status_code in (200, 202), f"Preview start failed: {r.status_code}"

# ─── Approve immediately ────────────────────────────────────────────────
log("Approve draft")
r = requests.patch(f"{GW}/drafts/{draft_id}/decide", json={"action":"approve"}, headers=h)
assert r.status_code == 200, f"Approve failed: {r.status_code}"
resp = r.json()
task_id = resp.get("task_id")
doc_id = resp.get("document_id")
if not task_id:
    r2 = requests.get(f"{GW}/drafts/{draft_id}/tasks", headers=h)
    tasks = r2.json().get("tasks", [])
    task_id = tasks[0]["task_id"] if tasks else None
assert task_id, "No task_id found"
print(f"  task_id={task_id}, document_id={doc_id}")

# ─── Wait for full pipeline ─────────────────────────────────────────────
log("Wait for pipeline completion (poll every 3s, timeout 90s)")
for i in range(30):
    r = requests.get(f"{GW}/tasks/{task_id}/status", headers=h)
    d = r.json()
    s = d.get("status","")
    steps = {s["step_name"]: s["status"] for s in d.get("steps",[])}
    if i < 3 or i % 5 == 0 or s in ("completed","failed"):
        print(f"  [{i+1}] status={s} steps={steps}")
    if s == "completed":
        print(f"  [OK] Pipeline completed!")
        break
    if s == "failed":
        print(f"  [FAIL] Pipeline failed: {d}")
        sys.exit(1)
    time.sleep(3)
else:
    print(f"  [FAIL] Timeout waiting for pipeline completion")
    sys.exit(1)

# ─── Search ─────────────────────────────────────────────────────────────
log("Search for document text")
all_found = True
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
        for i, rr in enumerate(results[:3]):
            content = rr["source"].get("content","")[:200]
            score = rr["retrieval"].get("score","?")
            print(f"    [{i+1}] score={score:.3f} content={content}")
    elif total > 0:
        print(f"    ⚠ total_found={total} but results=[] — check rag-search response")
        # Direct query to rag-search bypassing gateway (local only)
        direct_url = get_direct_rag_url()
        if direct_url:
            rs = requests.post(direct_url,
                json={"query":query,"valid_at":"2025-01-01"},
                headers={"Content-Type":"application/json; charset=utf-8"})
            print(f"    Direct rag-search: {rs.status_code} {rs.json() if rs.status_code==200 else rs.text[:200]}")
    # Check: substring match for exact phrases, semantic (total_found > 0) for free-form queries
    if query in SEMANTIC_QUERIES:
        found = total > 0
        if found:
            print(f"  [OK] '{query}' — semantic match (total_found={total})")
        else:
            print(f"  [FAIL] '{query}' — no semantic matches")
            all_found = False
    else:
        found = any(query.lower() in rr["source"].get("content","").lower() for rr in results) if results else False
        if found:
            print(f"  [OK] '{query}' found")
        else:
            print(f"  [FAIL] '{query}' NOT found in search results")
            all_found = False

if all_found:
    print(f"\n{'='*60}")
    print(f"  [PASS] ALL CHECKS PASSED")
    print(f"{'='*60}")
    sys.exit(0)
else:
    print(f"\n{'='*60}")
    print(f"  [FAIL] SOME CHECKS FAILED")
    print(f"{'='*60}")
    sys.exit(1)
