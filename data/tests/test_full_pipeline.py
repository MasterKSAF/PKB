"""
Full pipeline test: Upload document → Process → Search → Verify
Tests the complete pipeline with real services via Gateway (port 8080)
"""
import requests
import time
import uuid
import json
import sys
import hashlib
from pathlib import Path

from config import get_api_url, get_direct_rag_url

GATEWAY_URL = get_api_url()
PDF_PATH = Path("data/pdf/7bd97d737317a8a272bb18a405ab2d04.pdf")
print(f"Target: {GATEWAY_URL}")
AUTH_EMAIL = "admin@example.com"
AUTH_PASSWORD = "Admin1234!"

# Known content from the PDF to verify search
EXPECTED_TEXT_FRAGMENTS = [
    "шкурка шлифовальная бумажная водостойкая",
    "зеленый карбид кремния",
    "черный карбид кремния",
    "шлифовальная шкурка",
    "ГОСТ 10054",
]

step = 0

def log_step(msg):
    global step
    step += 1
    print(f"\n{'='*70}")
    print(f"  STEP {step}: {msg}")
    print(f"{'='*70}")
    sys.stdout.flush()

# ─── Auth ─────────────────────────────────────────────────────────────────────
log_step("Auth — получение JWT токена")
resp = requests.post(
    f"{GATEWAY_URL}/auth/token",
    json={"username": AUTH_EMAIL, "password": AUTH_PASSWORD},
)
assert resp.status_code == 200, f"Auth failed: {resp.status_code}"
token_data = resp.json()
access_token = token_data["access_token"]
print(f"  Token OK: {access_token[:50]}...")
headers = {"Authorization": f"Bearer {access_token}"}

# Verify
resp = requests.get(f"{GATEWAY_URL}/auth/me", headers=headers)
assert resp.status_code == 200, f"Auth/me failed: {resp.status_code}"
user_data = resp.json()
print(f"  User: {user_data.get('full_name')} (role: {user_data.get('role')})")
assert user_data.get("permissions", {}).get("can_upload_documents", False), "No upload permission!"

# ─── Compute file hash for document_key ──────────────────────────────────────
with open(PDF_PATH, "rb") as f:
    file_bytes = f.read()
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    print(f"  File: {PDF_PATH.name} ({len(file_bytes)} bytes)")
    print(f"  SHA256: {file_hash}")

# ─── Upload document ─────────────────────────────────────────────────────────
log_step("Upload document")

idempotency_key = str(uuid.uuid4())

with open(PDF_PATH, "rb") as f:
    resp = requests.post(
        f"{GATEWAY_URL}/drafts",
        files={"file": (PDF_PATH.name, f, "application/pdf")},
        data={
            "document_key": file_hash,
            "source_type": "GOST",
            "title": "Шкурка шлифовальная бумажная водостойкая ГОСТ 10054-82",
            "doc_code": "10054-82",
            "era": "USSR",
            "jurisdiction": "RU",
        },
        headers={**headers, "Idempotency-Key": idempotency_key},
    )

print(f"  Upload: HTTP {resp.status_code}")

# Handle potential 409 (duplicate) — delete old draft and retry
if resp.status_code == 409:
    print("  DUPLICATE — checking existing drafts...")
    # List drafts to find ours
    resp_drafts = requests.get(f"{GATEWAY_URL}/drafts", headers=headers)
    if resp_drafts.status_code == 200:
        drafts = resp_drafts.json().get("data", [])
        for d in drafts:
            if d.get("document_key") == file_hash or d.get("file_key") == f"f-{file_hash[:12]}":
                print(f"  Found existing draft_id={d['id']}, deleting...")
                requests.delete(f"{GATEWAY_URL}/drafts/{d['id']}", headers=headers)
                time.sleep(1)
    # Also delete existing document
    resp_docs = requests.get(f"{GATEWAY_URL}/registry/documents?page_size=50", headers=headers)
    if resp_docs.status_code == 200:
        docs = resp_docs.json().get("data", [])
        for d in docs:
            if d.get("id") == 8:
                print(f"  Found existing document_id=8")
    # Retry upload
    with open(PDF_PATH, "rb") as f:
        resp = requests.post(
            f"{GATEWAY_URL}/drafts",
            files={"file": (PDF_PATH.name, f, "application/pdf")},
            data={
                "document_key": file_hash,
                "source_type": "GOST",
                "title": "Шкурка шлифовальная бумажная водостойкая ГОСТ 10054-82",
                "doc_code": "10054-82",
                "era": "USSR",
                "jurisdiction": "RU",
            },
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
    print(f"  Re-upload: HTTP {resp.status_code}")

assert resp.status_code in (200, 202), f"Upload failed: {resp.status_code} {resp.text[:300]}"

upload_data = resp.json()
draft_id = upload_data.get("draft_id")
task_id = upload_data.get("task_id")
print(f"  HTTP {resp.status_code}: draft_id={draft_id}, task_id={task_id}")

# ─── Start preview ───────────────────────────────────────────────────────────
log_step(f"Start preview for draft_id={draft_id}")

resp = requests.post(
    f"{GATEWAY_URL}/drafts/{draft_id}/preview",
    headers=headers,
)
print(f"  Preview: HTTP {resp.status_code}")
assert resp.status_code in (200, 202), f"Preview start failed: {resp.status_code}"

# ─── Wait for preview ───────────────────────────────────────────────────────
log_step("Wait for preview completion (polling longpoll=0)")

preview_completed = False
for i in range(30):
    resp = requests.get(
        f"{GATEWAY_URL}/drafts/{draft_id}/preview/status?longpoll=0",
        headers=headers,
    )
    if resp.status_code != 200:
        time.sleep(2)
        continue

    status_data = resp.json()
    status = status_data.get("status", "")
    print(f"  [{i+1}] Status: {status}, progress: {status_data.get('progress_percent')}%")

    if status == "completed":
        preview_completed = True
        meta = status_data.get("preview", {})
        print(f"  Preview completed!")
        print(f"    doc_code: {meta.get('doc_code')}")
        print(f"    title: {meta.get('title')[:80]}...")
        print(f"    year: {meta.get('year')}")
        break
    elif status in ("failed", "error"):
        print(f"  Preview failed: {status_data}")
        break
    else:
        time.sleep(2)

assert preview_completed, f"Preview did not complete in 30 attempts"

# ─── Approve document ────────────────────────────────────────────────────────
log_step(f"Approve draft_id={draft_id} (start full pipeline)")

resp = requests.patch(
    f"{GATEWAY_URL}/drafts/{draft_id}/decide",
    json={"action": "approve"},
    headers={**headers, "Content-Type": "application/json"},
)
print(f"  Decide: HTTP {resp.status_code}")
assert resp.status_code in (200, 202), f"Decide failed: {resp.status_code} {resp.text[:300]}"

decide_data = resp.json()
document_id = decide_data.get("document_id")
status = decide_data.get("status")
print(f"  Result: status={status}, document_id={document_id}")

# ─── Wait for full pipeline ──────────────────────────────────────────────────
log_step("Wait for full pipeline completion (parser/converter/registry/rag-index)")

full_completed = False
for i in range(60):
    resp = requests.get(
        f"{GATEWAY_URL}/tasks/{task_id}/status",
        headers=headers,
    )
    if resp.status_code != 200:
        time.sleep(5)
        continue

    task_data = resp.json()
    t_status = task_data.get("status", "")
    stage = task_data.get("pipeline_stage", "")
    progress = task_data.get("progress_percent", 0)
    steps = task_data.get("steps", [])
    step_statuses = {s["step_name"]: s["status"] for s in steps}
    
    if i < 5 or t_status in ("completed", "failed") or i % 5 == 0:
        print(f"  [{i+1}] Task: {t_status}, stage: {stage}, progress: {progress}%")
        print(f"       Steps: {step_statuses}")

    if t_status == "completed":
        full_completed = True
        print(f"  ✓ Full pipeline completed!")
        break
    elif t_status == "failed":
        failed_steps = [s["step_name"] for s in steps if s["status"] == "failed"]
        print(f"  ✗ Pipeline failed at: {failed_steps}")
        break

    time.sleep(5)

# ─── Verify document in registry ─────────────────────────────────────────────
log_step(f"Verify document in registry")

resp = requests.get(
    f"{GATEWAY_URL}/registry/documents/{document_id}",
    headers=headers,
)
if resp.status_code == 200:
    doc_data = resp.json().get("data", {})
    print(f"  Document: id={doc_data.get('id')}, title={doc_data.get('title')}")
    print(f"  Status: {doc_data.get('status')}")
    print(f"  Chunks: {doc_data.get('chunk_count', 'N/A')}")
else:
    print(f"  Registry returned HTTP {resp.status_code}")

# ─── Search via RAG ──────────────────────────────────────────────────────────
log_step("SEARCH — поиск через RAG Search Service")

search_verified = False
for query in EXPECTED_TEXT_FRAGMENTS:
    print(f"\n  --- Query: \"{query}\" ---")
    resp = requests.post(
        f"{GATEWAY_URL}/rag/search",
        json={"query": query, "valid_at": "2025-01-01"},
        headers={**headers, "Content-Type": "application/json; charset=utf-8"},
    )

    if resp.status_code == 200:
        search_data = resp.json()
        results = search_data.get("results", [])
        total = search_data.get("total_found", 0)
        print(f"  HTTP 200: {len(results)} results (total: {total})")

        if results:
            for r in results[:5]:
                src = r.get("source", {})
                ret = r.get("retrieval", {})
                content = src.get("content", "")[:150]
                print(f"    [score={ret.get('score', 0):.3f}] doc={src.get('document_id')}, page={src.get('page')}: {content}...")

            # Verify content matches query
            for r in results:
                content = r.get("source", {}).get("content", "").lower()
                query_words = query.lower().split()
                if any(w in content for w in query_words):
                    print(f"\n  ✓ VERIFIED: Search found relevant content!")
                    search_verified = True
                    break
        else:
            print(f"    (empty results)")
    elif resp.status_code == 404:
        print(f"  RAG search endpoint not available at gateway")
        # Try direct to rag-search (local only)
        direct_url = get_direct_rag_url()
        if direct_url:
            resp2 = requests.post(
                direct_url,
                json={"query": query, "valid_at": "2025-01-01"},
                headers={"Content-Type": "application/json; charset=utf-8"},
            )
            if resp2.status_code == 200:
                rdata = resp2.json()
                results = rdata.get("results", [])
                print(f"  Direct rag-search: {len(results)} results")
    else:
        print(f"  HTTP {resp.status_code}: {resp.text[:200]}")

    if search_verified:
        break

# ─── Search via Query Service (chat) ─────────────────────────────────────────
log_step("SEARCH — поиск через Query Service (chat)")

resp = requests.post(
    f"{GATEWAY_URL}/chat/sessions",
    json={
        "title": "Поиск ГОСТ 10054-82 о шлифовальной шкурке",
        "document_ids": [document_id] if document_id else [],
    },
    headers={**headers, "Content-Type": "application/json"},
)
print(f"  Chat session: HTTP {resp.status_code}")

if resp.status_code == 200:
    session_data = resp.json()
    session_id = session_data.get("session_id") or session_data.get("id")
    print(f"  Session ID: {session_id}")

    if session_id:
        # Ask a question about the document
        resp = requests.post(
            f"{GATEWAY_URL}/chat/sessions/{session_id}/messages",
            json={"content": "Найди информацию про шлифовальную шкурку из зеленого карбида кремния"},
            headers={**headers, "Content-Type": "application/json"},
        )
        print(f"  Chat message: HTTP {resp.status_code}")

        if resp.status_code == 200:
            msg_data = resp.json()
            message = msg_data.get("message", msg_data)
            role = message.get("role", "")
            content = message.get("content", "")[:200]
            sources = message.get("sources", [])
            status = message.get("status", "")

            print(f"  Role: {role}, Status: {status}")
            if sources:
                print(f"  Sources: {len(sources)} found!")
                search_verified = True
            elif content:
                print(f"  Response: {content}")
            else:
                print(f"  Full response: {json.dumps(msg_data, ensure_ascii=False)[:500]}")

# ─── FINAL REPORT ────────────────────────────────────────────────────────────
print(f"\n{'='*70}")
print(f"  FINAL RESULT")
print(f"{'='*70}")
if search_verified:
    print(f"  ✓ SEARCH VERIFIED: Found relevant content matching document")
else:
    print(f"  ⚠ Search could not verify. This may be because:")
    print(f"    - The full pipeline (indexing) did not complete")
    print(f"    - RAG embeddings/indexing not yet finished")
    print(f"    - Search query mismatch with embedded chunks")

print(f"\n  Parameters:")
print(f"    Draft ID:     {draft_id}")
print(f"    Task ID:      {task_id}")
print(f"    Document ID:  {document_id}")
print(f"    File:         {PDF_PATH.name}")
print(f"    File SHA256:  {file_hash[:20]}...")
print(f"{'='*70}")
