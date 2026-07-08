"""
Test: Upload ПКПС_Часть_VIII_ pdf → Preview → Approve → Pipeline → Search.

Usage:
    python data/tests/test_load_pkps_pdf.py

Requires: docker services up and running (gateway, orchestrator, etc.)
"""
import io, requests, time, uuid, hashlib, sys, json
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from config import get_api_url, ensure_services

ensure_services("all")

GW = get_api_url()
PDF = Path("data/pdf/gost_22786-77.pdf")

print(f"Target: {GW}")
print(f"PDF:    {PDF.name} ({PDF.stat().st_size} bytes)")
sys.stdout.flush()

step = 0
def log(msg):
    global step; step += 1
    print(f"\n=== STEP {step}: {msg} ===")
    sys.stdout.flush()

# ─── Auth ───────────────────────────────────────────────────────────────
log("Auth")
r = requests.post(f"{GW}/auth/token",
    json={"username":"admin@example.com","password":"Admin1234!"})
assert r.status_code == 200, f"Auth failed: {r.status_code}"
h = {"Authorization": f"Bearer {r.json()['access_token']}"}
print("  OK")

# ─── Compute hash and cleanup ──────────────────────────────────────────
log("Compute file hash")
file_hash = hashlib.sha256(open(PDF,"rb").read()).hexdigest()
print(f"  SHA256: {file_hash[:32]}...")

# Cleanup any stale drafts with same hash
log("Cleanup stale drafts")
r = requests.get(f"{GW}/drafts", headers=h)
if r.status_code == 200:
    drafts = r.json().get("data", [])
    for d in drafts:
        if d.get("document_key") == file_hash or d.get("file_key","").startswith(f"f-{file_hash[:12]}"):
            print(f"  Delete stale draft_id={d['id']}")
            requests.delete(f"{GW}/drafts/{d['id']}", headers=h)
            time.sleep(1)

# ─── Upload ─────────────────────────────────────────────────────────────
log("Upload PDF")
with open(PDF,"rb") as f:
    r = requests.post(f"{GW}/drafts",
        files={"file": (PDF.name, f, "application/pdf")},
        data={
            "document_key": file_hash,
            "source_type": "RD",
            "title": "ПКПС Часть VIII Системы и трубопроводы, изд 2018",
            "doc_code": "ПКПС-VIII-2018",
            "era": "RF",
            "jurisdiction": "RU",
        },
        headers={**h, "Idempotency-Key": str(uuid.uuid4())})

print(f"  Upload: HTTP {r.status_code}")
if r.status_code == 409:
    print("  DUPLICATE — checking existing drafts...")
    resp_drafts = requests.get(f"{GW}/drafts", headers=h)
    if resp_drafts.status_code == 200:
        drafts = resp_drafts.json().get("data", [])
        for d in drafts:
            if d.get("document_key") == file_hash:
                print(f"  Found existing draft_id={d['id']}, deleting...")
                requests.delete(f"{GW}/drafts/{d['id']}", headers=h)
                time.sleep(1)
    # Retry
    with open(PDF,"rb") as f:
        r = requests.post(f"{GW}/drafts",
            files={"file": (PDF.name, f, "application/pdf")},
            data={
                "document_key": file_hash,
                "source_type": "RD",
                "title": "ПКПС Часть VIII Системы и трубопроводы, изд 2018",
                "doc_code": "ПКПС-VIII-2018",
                "era": "RF",
                "jurisdiction": "RU",
            },
            headers={**h, "Idempotency-Key": str(uuid.uuid4())})
    print(f"  Re-upload: HTTP {r.status_code}")

assert r.status_code in (200, 202), f"Upload failed: {r.status_code} {r.text[:300]}"

draft_id = r.json()["draft_id"]
task_id = r.json().get("task_id")
print(f"  draft_id={draft_id}, task_id={task_id}")

# ─── Start Preview ──────────────────────────────────────────────────────
log("Start preview")
r = requests.post(f"{GW}/drafts/{draft_id}/preview", headers=h)
assert r.status_code in (200, 202), f"Preview start failed: {r.status_code}"

# ─── Wait for Preview ──────────────────────────────────────────────────
log("Wait for preview completion")
preview_ok = False
for i in range(30):
    r = requests.get(f"{GW}/drafts/{draft_id}/preview/status?longpoll=0", headers=h)
    if r.status_code != 200:
        time.sleep(2); continue
    s = r.json().get("status","")
    pp = r.json().get("progress_percent", 0)
    print(f"  [{i+1}] Preview: {s}, {pp}%")
    if s == "completed":
        preview_ok = True
        meta = r.json().get("preview", {})
        print(f"    doc_code: {meta.get('doc_code')}")
        print(f"    title:   {str(meta.get('title',''))[:80]}")
        print(f"    year:    {meta.get('year')}")
        print(f"    pages:   {meta.get('pages')}")
        break
    elif s in ("failed","error"):
        print(f"    Preview failed: {r.json()}")
        break
    time.sleep(2)

assert preview_ok, "Preview did not complete"

# ─── Approve (start full pipeline) ─────────────────────────────────────
log("Approve draft (start full pipeline)")
r = requests.patch(f"{GW}/drafts/{draft_id}/decide",
    json={"action":"approve"},
    headers={**h, "Content-Type": "application/json"})
print(f"  Decide: HTTP {r.status_code} {r.text[:300]}")
if r.status_code in (200, 202):
    decide_data = r.json()
    document_id = decide_data.get("document_id")
    task_id = decide_data.get("task_id") or task_id
    print(f"  document_id={document_id}, task_id={task_id}")
    print(f"  status={decide_data.get('status')}")
elif r.status_code == 409 and "INVALID_STAGE" in r.text:
    log("Draft already in full pipeline — skip approve")
else:
    assert False, f"Decide failed: {r.status_code} {r.text[:300]}"

if not task_id:
    r2 = requests.get(f"{GW}/drafts/{draft_id}/tasks", headers=h)
    tasks = r2.json().get("tasks", [])
    task_id = tasks[0]["task_id"] if tasks else None
    print(f"  fetched task_id={task_id}")
assert task_id, "No task_id available (decide did not return one, and /tasks returned empty)"

# ─── Wait for Full Pipeline ────────────────────────────────────────────
log("Wait for full pipeline completion (poll every 5s, timeout 600s)")
pipeline_ok = False
for i in range(120):
    r = requests.get(f"{GW}/tasks/{task_id}/status", headers=h)
    if r.status_code != 200:
        time.sleep(5); continue
    d = r.json()
    s = d.get("status","")
    stage = d.get("pipeline_stage","")
    progress = d.get("progress_percent", 0)
    steps = {st["step_name"]: st["status"] for st in d.get("steps",[])}
    if i < 3 or i % 10 == 0 or s in ("completed","failed"):
        print(f"  [{i+1}] status={s} stage={stage} progress={progress}% steps={steps}")
        sys.stdout.flush()
    if s == "completed":
        pipeline_ok = True
        print(f"  [OK] Pipeline completed!")
        break
    if s == "failed":
        failed_steps = [st["step_name"] for st in d.get("steps",[]) if st["status"]=="failed"]
        print(f"  [FAIL] Pipeline failed at: {failed_steps}")
        print(f"  Details: {json.dumps(d, ensure_ascii=False, indent=2)[:500]}")
        break
    time.sleep(5)

if not pipeline_ok:
    print(f"  [FAIL] Pipeline did not complete in time")
    # Don't exit, still try to search

# ─── Verify in Registry ────────────────────────────────────────────────
log("Verify document in registry")
if task_id:
    r2 = requests.get(f"{GW}/tasks/{task_id}/status", headers=h)
    if r2.status_code == 200:
        document_id = r2.json().get("document_id")
if document_id:
    r = requests.get(f"{GW}/registry/documents/{document_id}", headers=h)
    if r.status_code == 200:
        doc = r.json().get("data", {})
        print(f"  Document: id={doc.get('id')}, status={doc.get('status')}")
        print(f"  title: {str(doc.get('title',''))[:80]}")
        print(f"  chunks: {doc.get('chunk_count', 'N/A')}")
    else:
        print(f"  Registry: HTTP {r.status_code}")

# ─── Search ─────────────────────────────────────────────────────────────
log("Search for document text (basic queries)")
# Basic queries — these should match if the PDF was processed
queries = [
    "системы и трубопроводы",
    "ПКПС",
    "трубопровод",
    "система",
]

all_found = False
for q in queries:
    r = requests.post(f"{GW}/rag/search",
        json={"query": q, "valid_at": "2025-01-01"},
        headers={**h, "Content-Type": "application/json; charset=utf-8"})
    if r.status_code == 200:
        data = r.json()
        results = data.get("results", [])
        total = data.get("total_found", 0)
        print(f"  '{q}' — total_found={total}, results={len(results)}")
        if results:
            for rr in results[:2]:
                content = rr["source"].get("content","")[:150]
                score = rr["retrieval"].get("score","?")
                print(f"    [score={score}] {content}")
            all_found = True
        else:
            print(f"    (no results)")
    else:
        print(f"  '{q}' — HTTP {r.status_code}")

# ─── Result ─────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
if pipeline_ok:
    print(f"  [PASS] Pipeline completed successfully")
else:
    print(f"  [WARN] Pipeline did not complete, check logs")

if all_found:
    print(f"  [PASS] Search returned results")
else:
    print(f"  [WARN] Search returned no results (may need content-specific queries)")

print(f"\n  Draft ID:     {draft_id}")
print(f"  Task ID:      {task_id}")
print(f"  Document ID:  {document_id}")
print(f"  File:         {PDF.name}")
print(f"{'='*60}")

# Exit code: 0 if pipeline completed, 1 otherwise
sys.exit(0 if pipeline_ok else 1)
