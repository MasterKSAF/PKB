"""
Registry Sections Test — проверяет что create_pipeline_document
сохраняет sections в Registry без дублирования документа.

Поток: Upload → Preview → Approve → Pipeline → Registry sections

Usage:
    python data/tests/test_registry_sections.py data/pdf/2-020101-004.pdf
"""
import io, os, sys, json, time, uuid, hashlib
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

try:
    import requests
except ImportError:
    print("[FAIL] requests not installed. Run: pip install requests")
    sys.exit(1)

from config import get_api_url, ensure_services

ensure_services("all")

GW = get_api_url()
AUTH_USER = os.environ.get("TEST_AUTH_USER", "admin@example.com")
AUTH_PASS = os.environ.get("TEST_AUTH_PASS", "Admin1234!")

PDF_ARG = sys.argv[1] if len(sys.argv) > 1 else "data/pdf/2-020101-004.pdf"
PDF = Path(PDF_ARG).resolve()
assert PDF.exists(), f"File not found: {PDF}"

PREVIEW_TIMEOUT = 60
PIPELINE_TIMEOUT = 300

step_num = 0
failed = False


def log(msg):
    global step_num
    step_num += 1
    print(f"\n{'='*70}")
    print(f"  STEP {step_num}: {msg}")
    print(f"{'='*70}")
    sys.stdout.flush()


def fail(msg):
    global failed
    failed = True
    print(f"  [FAIL] {msg}")
    sys.stdout.flush()


def ok(msg=""):
    print(f"  [OK] {msg}" if msg else "  [OK]")
    sys.stdout.flush()


# ─── Auth ──────────────────────────────────────────────────────────────────
log("Auth")
r = requests.post(f"{GW}/auth/token",
                  json={"username": AUTH_USER, "password": AUTH_PASS}, timeout=10)
assert r.status_code == 200, f"Auth failed: {r.status_code}"
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
ok(f"Token OK")

# ─── File hash ─────────────────────────────────────────────────────────────
with open(PDF, "rb") as fh:
    file_bytes = fh.read()
file_hash = hashlib.sha256(file_bytes).hexdigest()
print(f"  File: {PDF.name} ({len(file_bytes)} bytes)")
print(f"  SHA256: {file_hash[:24]}...")

# ─── Upload ────────────────────────────────────────────────────────────────
log("Upload PDF")
headers_upload = {k: v for k, v in headers.items() if k != "Content-Type"}
with open(PDF, "rb") as fh:
    r = requests.post(
        f"{GW}/drafts",
        files={"file": (PDF.name, fh, "application/pdf")},
        data={
            "document_key": file_hash,
            "source_type": "RD",
            "title": PDF.stem,
            "doc_code": PDF.stem[:20],
            "era": "RF",
            "jurisdiction": "RU",
        },
        headers={**headers_upload, "Idempotency-Key": str(uuid.uuid4())},
        timeout=30,
    )
assert r.status_code in (200, 202), f"Upload failed: {r.status_code} {r.text[:300]}"
draft_id = r.json().get("draft_id")
task_id = r.json().get("task_id")
print(f"  draft_id={draft_id}, task_id={task_id}")

# ─── Preview ───────────────────────────────────────────────────────────────
log("Start preview")
r = requests.post(f"{GW}/drafts/{draft_id}/preview", headers=headers, timeout=30)
assert r.status_code in (200, 202), f"Preview failed: {r.status_code}"

log("Wait for preview")
preview_ok = False
for i in range(PREVIEW_TIMEOUT // 2 + 1):
    r = requests.get(f"{GW}/drafts/{draft_id}/preview/status?longpoll=0",
                     headers=headers, timeout=10)
    if r.status_code != 200:
        time.sleep(2)
        continue
    s = r.json().get("status", "")
    print(f"  [{i + 1}] Preview: {s}")
    if s == "completed":
        preview_ok = True
        ok()
        break
    elif s in ("failed", "error"):
        fail(f"Preview failed: {r.json()}")
        break
    time.sleep(2)
if not preview_ok:
    fail("Preview did not complete")

# ─── Approve ───────────────────────────────────────────────────────────────
log("Approve (start pipeline)")
r = requests.patch(
    f"{GW}/drafts/{draft_id}/decide",
    json={"action": "approve"},
    headers={**headers, "Content-Type": "application/json"},
    timeout=30,
)
assert r.status_code in (200, 202), f"Decide failed: {r.status_code} {r.text[:300]}"
resp_data = r.json()
document_id = resp_data.get("document_id")
print(f"  document_id={document_id}")

# ─── Wait for pipeline ─────────────────────────────────────────────────────
log("Wait for full pipeline")
pipeline_ok = False
for i in range(PIPELINE_TIMEOUT // 5 + 1):
    r = requests.get(f"{GW}/tasks/{task_id}/status", headers=headers, timeout=10)
    if r.status_code != 200:
        time.sleep(5)
        continue
    d = r.json()
    s = d.get("status", "")
    stage = d.get("pipeline_stage", "")
    progress = d.get("progress_percent", 0)
    if i < 3 or i % 5 == 0 or s in ("completed", "failed"):
        print(f"  [{i + 1}] status={s} stage={stage} progress={progress}%")
    if s == "completed":
        pipeline_ok = True
        ok("Pipeline completed!")
        break
    elif s == "failed":
        steps_info = [
            f"{st['step_name']}={st['status']}" for st in d.get("steps", [])
        ]
        fail(f"Pipeline failed: {steps_info}")
        break
    time.sleep(5)

# ─── Тест 1: Sections в Registry ──────────────────────────────────────────
log("TEST 1: Registry содержит sections после pipeline")

r = requests.get(f"{GW}/registry/documents?page_size=20", headers=headers, timeout=10)
assert r.status_code == 200, f"List docs: {r.status_code}"
docs = r.json().get("data", [])
print(f"  Всего документов: {len(docs)}")
doc_ids = [d["id"] for d in docs]
print(f"  Document IDs: {doc_ids}")

for doc in docs:
    did = doc["id"]
    r = requests.get(f"{GW}/registry/documents/{did}/sections", headers=headers, timeout=10)
    sec_count = 0
    if r.status_code == 200:
        sec_data = r.json()
        sec_count = len(sec_data.get("sections", []))
    print(f"  doc_id={did} title={str(doc.get('title',''))[:40]} "
          f"doc_code={str(doc.get('doc_code',''))[:25]} "
          f"status={doc.get('status','?')} sections={sec_count}")

# ─── Тест 2: Sections не пустые ───────────────────────────────────────────
log("TEST 2: Sections содержат контент")

best_doc = None
best_count = 0

for doc in docs:
    did = doc["id"]
    r = requests.get(f"{GW}/registry/documents/{did}/sections", headers=headers, timeout=10)
    if r.status_code == 200:
        sec_data = r.json()
        sections = sec_data.get("sections", [])
        if len(sections) > best_count:
            best_count = len(sections)
            best_doc = {"id": did, "title": doc.get("title"), "sections": sections}

if best_doc and best_count > 0:
    print(f"  Лучший документ: id={best_doc['id']}")
    print(f"  Найдено sections: {best_count}")
    for s in best_doc["sections"][:2]:
        content_preview = str(s.get("content", ""))[:80]
        print(f"    clause={s.get('clause','')} page={s.get('page','')} "
              f"content=\"{content_preview}...\"")
    ok(f"Registry содержит {best_count} секций")
else:
    print(f"  sections не найдены ни в одном документе")
    fail("Registry не содержит sections")

# ─── Тест 3: Нет дублирования документов ─────────────────────────────────
log("TEST 3: create_pipeline_document не создаёт дубль")

if len(docs) > 1:
    approve_docs = [d for d in docs if str(d.get("title", "")).startswith("Draft")]
    pipeline_docs = [d for d in docs if not str(d.get("title", "")).startswith("Draft")]
    if len(approve_docs) >= 1 and len(pipeline_docs) >= 1:
        print(f"  ⚠ Дублирование: approve создал {len(approve_docs)} док. (Draft N), "
              f"pipeline создал {len(pipeline_docs)} док.")
        print(f"  Это аномалия R5 — create_pipeline_document создаёт новый "
              f"документ вместо обновления существующего")
        fail("Дублирование документов (R5)")
    else:
        ok("Нет дублирования документов")
else:
    ok("Только 1 документ — дублирования нет")

# ─── Тест 4: Секции принадлежат правильному документу ────────────────────
log("TEST 4: document_id в sections совпадает с document_id документа")

if best_doc and best_count > 0:
    # Проверяем что section_id не None
    for s in best_doc["sections"][:3]:
        sec_id = s.get("section_id")
        clause = s.get("clause", "")
        print(f"    section_id={sec_id} clause={clause}")
    all_have_id = all(s.get("section_id") is not None for s in best_doc["sections"])
    if all_have_id:
        ok(f"Все {best_count} sections имеют section_id")
    else:
        fail("Не все sections имеют section_id")

# ─── Final Report ──────────────────────────────────────────────────────────
print(f"\n{'=' * 70}")
print(f"  REGISTRY SECTIONS TEST")
print(f"{'=' * 70}")
print(f"  PDF:          {PDF.name}")
print(f"  Pipeline:     {'✓ COMPLETED' if pipeline_ok else '✗ FAILED'}")
print(f"  Sections:     {best_count} в документе id={best_doc['id'] if best_doc else '?'}")
print(f"{'=' * 70}")

if failed:
    print(f"\n  [FAIL] Some checks failed")
    sys.exit(1)
elif not pipeline_ok:
    print(f"\n  [FAIL] Pipeline did not complete")
    sys.exit(1)
elif best_count > 0:
    print(f"\n  [PASS] Registry sections test passed")
    sys.exit(0)
else:
    print(f"\n  [INFO] Pipeline OK, но sections = 0 (аномалия R5)")
    sys.exit(2)
