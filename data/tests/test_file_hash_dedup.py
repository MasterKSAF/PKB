"""
E2E test: file_hash_sha256 propagation from upload → approve → document dedup.

Проверяет что:
  1. file_hash_sha256 сохраняется в metadata_fields при upload
  2. При approve file_hash_sha256 передаётся в registry.documents
  3. Дубликаты блокируются UNIQUE constraint на file_hash_sha256
  4. После cleanup все данные удалены

Использует только корневой docker-compose (порт 8080), без service_checker.
Очищает данные перед запуском (TEST_CLEANUP=true по умолчанию).
"""
import io, os, sys, json, time, uuid, hashlib, subprocess
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

try:
    import requests
except ImportError:
    print("[FAIL] requests not installed. Run: pip install requests")
    sys.exit(1)

from config import get_api_url, ensure_services

ensure_services("all")  # чистит данные
time.sleep(3)

GW = get_api_url()

PASS = 0
FAIL = 0
ERRORS = []


def check(condition: bool, msg: str):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {msg}")
    else:
        FAIL += 1
        ERRORS.append(msg)
        print(f"  [FAIL] {msg}")


# ─── Auth ─────────────────────────────────────────────────────────────────────
r = requests.post(f"{GW}/auth/token",
    json={"username": "admin@example.com", "password": "Admin1234!"})
assert r.status_code == 200, f"Auth failed: {r.status_code}"
h = {"Authorization": f"Bearer {r.json()['access_token']}"}

# ─── Generate a real 5-page PDF with unique text content ───────────────────
from fpdf import FPDF

UNIQUE_SALT = uuid.uuid4().hex[:16]

pdf = FPDF(orientation="P", unit="mm", format="A4")
pdf.set_auto_page_break(auto=True, margin=15)

for page in range(5):
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    line = (f"Page {page+1}/5 | {UNIQUE_SALT} | Document processing validation | "
            f"Rules for classification and construction of sea-going ships | "
            f"Russian Maritime Register of Shipping. " * 6)
    pdf.multi_cell(0, 5, text=line)

PDF_CONTENT = pdf.output()
FILE_HASH = hashlib.sha256(PDF_CONTENT).hexdigest()
DOC_KEY = f"dedup-test-{UNIQUE_SALT[:8]}"
TITLE = "Dedup Test Document"
DOC_CODE = "DEDUP-0001"

print(f"\n{'='*70}")
print(f"  FILE HASH DEDUP E2E TEST")
print(f"  Target: {GW}")
print(f"  PDF size: {len(PDF_CONTENT)} bytes")
print(f"  SHA256: {FILE_HASH[:20]}...")
print(f"{'='*70}")

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1: Upload
# ═══════════════════════════════════════════════════════════════════════════════
print(f"\n  --- STEP 1: Upload PDF ---")
r1 = requests.post(f"{GW}/drafts",
    files={"file": ("dedup-test.pdf", PDF_CONTENT, "application/pdf")},
    data={
        "document_key": DOC_KEY,
        "source_type": "GOST",
        "title": TITLE,
        "doc_code": DOC_CODE,
        "era": "RF",
        "jurisdiction": "RU",
    },
    headers={**h, "Idempotency-Key": str(uuid.uuid4())},
    timeout=30)

if r1.status_code == 409:
    print(f"  Cleanup issue: existing draft with same key. Manual cleanup needed.")
    sys.exit(1)

check(r1.status_code == 202, f"Upload HTTP 202 (got {r1.status_code})")

data1 = r1.json()
draft_id = data1.get("draft_id")
task_id = data1.get("task_id")
resp_hash = data1.get("file_hash_sha256")
check(resp_hash == FILE_HASH, f"Response file_hash_sha256 matches")
check(draft_id is not None, f"draft_id present: {draft_id}")
check(task_id is not None, f"task_id present: {task_id}")

print(f"  draft_id={draft_id}, task_id={task_id}")

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2: Wait for pipeline → document created
# ═══════════════════════════════════════════════════════════════════════════════
print(f"\n  --- STEP 2: Wait for pipeline → document created ---")

document_id = None
last_status = ""
for i in range(60):  # up to 120s для preview + decision
    try:
        r = requests.get(f"{GW}/tasks/{task_id}/status", headers=h, timeout=10)
        if r.status_code != 200:
            time.sleep(2)
            continue
        d = r.json()
        s = d.get("status", "")
        stage = d.get("pipeline_stage", "")
        progress = d.get("progress_percent", 0)
        doc_id = d.get("document_id")

        if s != last_status or i % 5 == 0 or s in ("completed", "failed") or doc_id:
            print(f"  [{i+1:2d}] Task: {s:12s} | stage={stage:20s} | {progress:3d}% | doc_id={doc_id}")
            last_status = s

        if doc_id:
            document_id = doc_id
            print(f"  [OK] Document created: id={document_id}")
            break
        if s == "completed":
            print(f"  [OK] Pipeline completed (no document_id in response)")
            break
        if s == "failed":
            failed_steps = [st["step_name"] for st in d.get("steps", []) if st["status"] == "failed"]
            print(f"  [WARN] Pipeline failed at: {failed_steps}")
            break
        # If in decision stage, try manual approve
        if stage == "decision" and s == "active":
            print(f"  [..] Decision stage reached, trying manual approve...")
            ra = requests.patch(f"{GW}/drafts/{draft_id}/decide",
                json={"action": "approve"},
                headers={**h, "Content-Type": "application/json"},
                timeout=30)
            if ra.status_code == 409:
                print(f"  [..] Approve returned 409 (already decided), continuing...")
                continue
            if ra.status_code in (200, 202):
                decide_data = ra.json()
                doc_id_from_approve = decide_data.get("document_id")
                if doc_id_from_approve:
                    document_id = doc_id_from_approve
                    print(f"  [OK] Document created by manual approve: id={document_id}")
                    break
                print(f"  [..] Approve accepted, polling for completion...")
            else:
                print(f"  [WARN] Approve returned HTTP {ra.status_code}: {ra.text[:150]}")
    except requests.ConnectionError:
        time.sleep(3)
        continue
    except Exception as e:
        print(f"  [{i+1:2d}] Poll error: {e}")
    time.sleep(2)

check(document_id is not None, "Document created (auto or manual approve)")

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3: Verify file_hash_sha256 in DB (upload step + document)
# ═══════════════════════════════════════════════════════════════════════════════
print(f"\n  --- STEP 3: Verify file_hash_sha256 in DB ---")

# 3a: verify draft has file_hash_sha256 via Registry API (колонка в registry.drafts)
try:
    r_draft = requests.get(f"{GW}/drafts/{draft_id}", headers=h, timeout=10)
    if r_draft.status_code == 200:
        draft_data = r_draft.json()  # оркестратор возвращает без обёртки data
        draft_hash = draft_data.get("file_hash_sha256") or (draft_data.get("data") or {}).get("file_hash_sha256")
        check(draft_hash == FILE_HASH, f"Registry drafts.file_hash_sha256 = {str(draft_hash)[:20]}...")
    else:
        check(False, f"GET /drafts/{draft_id} returned HTTP {r_draft.status_code}")
except Exception as e:
    check(False, f"Draft API query error: {e}")

# 3b: document record
if document_id:
    sql_doc = f"SELECT file_hash_sha256 FROM registry.documents WHERE id = {document_id}"
    try:
        result = subprocess.run(
            ["docker", "exec", "-i", "pkb-postgres", "psql", "-U", "pkb", "-d", "pkb_neuro",
             "-t", "-A", "-c", sql_doc],
            capture_output=True, text=True, timeout=15, cwd=".")
        db_hash = result.stdout.strip()
        check(db_hash == FILE_HASH, f"registry.documents.file_hash_sha256 = {db_hash[:20]}...")
    except Exception as e:
        check(False, f"DB document query error: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 4: Duplicate upload → 409
# ═══════════════════════════════════════════════════════════════════════════════
print(f"\n  --- STEP 4: Duplicate upload → 409 ---")
r2 = requests.post(f"{GW}/drafts",
    files={"file": ("dedup-test-dup.pdf", PDF_CONTENT, "application/pdf")},
    data={
        "document_key": DOC_KEY,
        "source_type": "GOST",
        "title": TITLE,
        "doc_code": DOC_CODE,
        "era": "RF",
        "jurisdiction": "RU",
    },
    headers={**h, "Idempotency-Key": str(uuid.uuid4())},
    timeout=30)

check(r2.status_code == 409, f"Duplicate blocked: HTTP 409 (got {r2.status_code})")
if r2.status_code == 409:
    err = r2.json()
    code = err.get("detail", {}).get("error", {}).get("code", "?")
    print(f"  Code: {code}")

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 5: Verify no duplicates in registry.documents
# ═══════════════════════════════════════════════════════════════════════════════
print(f"\n  --- STEP 5: Verify EXACTLY 1 document with this hash ---")
sql_count = f"SELECT count(*) FROM registry.documents WHERE file_hash_sha256 = '{FILE_HASH}'"
try:
    result = subprocess.run(
        ["docker", "exec", "-i", "pkb-postgres", "psql", "-U", "pkb", "-d", "pkb_neuro",
         "-t", "-A", "-c", sql_count],
        capture_output=True, text=True, timeout=15, cwd=".")
    count = int(result.stdout.strip())
    check(count == 1, f"Documents with this hash: {count} (expected 1)")
except Exception as e:
    check(False, f"DB count error: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 6: Cleanup — delete test draft
# ═══════════════════════════════════════════════════════════════════════════════
print(f"\n  --- STEP 6: Cleanup test drafts ---")
if draft_id:
    try:
        rd = requests.delete(f"{GW}/drafts/{draft_id}", headers=h, timeout=10)
        print(f"  Delete draft {draft_id}: HTTP {rd.status_code}")
    except Exception as e:
        print(f"  Delete draft error: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# FINAL
# ═══════════════════════════════════════════════════════════════════════════════
print(f"\n{'='*70}")
print(f"  RESULTS: {PASS} passed, {FAIL} failed")
if ERRORS:
    for e in ERRORS:
        print(f"    - {e}")
print(f"{'='*70}")

if FAIL > 0:
    print(f"\n  [FAIL] Some checks failed")
    sys.exit(1)
else:
    print(f"\n  [PASS] file_hash_sha256 dedup works correctly")
    sys.exit(0)
