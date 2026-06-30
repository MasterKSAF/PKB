"""
Universal PDF Loader + Search Verification Test.

Загружает любой PDF, проходит полный pipeline (Upload → Preview → Approve → Wait),
после pipeline получает текст распарсенного документа из Registry (sections),
извлекает из него фрагменты и проверяет их через RAG Search.

Использует только корневой docker-compose (порт 8080), без service_checker.

Usage:
    # По умолчанию — локальный сервер
    python data/tests/test_universal_pdf_loader.py

    # Указать конкретный PDF
    python data/tests/test_universal_pdf_loader.py data/pdf/2-020101-004.pdf

    # Внешний сервер
    set TEST_API_URL=http://195.70.195.203:8080/api/v1 && python data/tests/test_universal_pdf_loader.py data/pdf/...pdf

    # Настроить количество фрагментов для проверки
    set EXTRACT_FRAGMENTS=10 && python data/tests/test_universal_pdf_loader.py data/pdf/...pdf

Requires:
    - docker services up (gateway, orchestrator, celery-worker, rag-search, etc.)
    - pip install requests
"""
import io, os, sys, re, json, time, uuid, hashlib, datetime
from pathlib import Path
from collections import Counter

# ─── UTF-8 stdout ────────────────────────────────────────────────────────
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ─── Imports ─────────────────────────────────────────────────────────────
try:
    import requests
except ImportError:
    print("[FAIL] requests not installed. Run: pip install requests")
    sys.exit(1)

from config import get_api_url, ensure_services

ensure_services("all")

# ─── Config ──────────────────────────────────────────────────────────────
GW = get_api_url()

# Определяем PDF из аргумента или используем целевой по умолчанию
if len(sys.argv) > 1:
    pdf_arg = sys.argv[1]
else:
    pdf_arg = "data/pdf/2-020101-004.pdf"

PDF = Path(pdf_arg).resolve()
if not PDF.exists():
    print(f"[FAIL] File not found: {PDF}")
    sys.exit(1)

# Количество фрагментов для извлечения и проверки
EXTRACT_FRAGMENTS = int(os.environ.get("EXTRACT_FRAGMENTS", "8"))

# Настройки документа (можно переопределить через переменные окружения)
DOC_META = {
    "source_type": os.environ.get("DOC_SOURCE_TYPE", "RD"),
    "title": os.environ.get("DOC_TITLE", PDF.stem),
    "doc_code": os.environ.get("DOC_CODE", PDF.stem[:20]),
    "era": os.environ.get("DOC_ERA", "RF"),
    "jurisdiction": os.environ.get("DOC_JURISDICTION", "RU"),
}

# Пороги ожидания (сек)
PREVIEW_TIMEOUT = 60
PIPELINE_TIMEOUT = 300

# ─── Helpers ─────────────────────────────────────────────────────────────
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


# ─── STEP: Extract fragments from Registry sections ─────────────────────
def extract_fragments_from_sections(sections: list, max_fragments: int = 8) -> list:
    """
    Извлекает осмысленные текстовые фрагменты из массива секций документа,
    полученных от Registry (уже распарсено конвертером/OCR).
    """
    fragments = []
    seen = set()

    # Стоп-слова для фильтрации мусора
    stop_patterns = [
        r'^\d+$',                           # только номер страницы
        r'^с\.?\s*$', r'^стр\.?\s*\d*$',   # с., стр.
        r'^содержание$', r'^оглавление$',   # заголовки разделов
        r'^приложение\s*\d*$',              # приложение N
        r'^\s*$',                            # пустые
    ]
    stop_re = re.compile('|'.join(stop_patterns), re.IGNORECASE)

    for section in sections:
        content = section.get("content", "") or ""
        if len(content) < 30:
            continue

        # Разбиваем на строки и чистим
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            line = re.sub(r'\s+', ' ', line).strip()
            if len(line) < 20:
                continue
            if len(line) > 300:
                line = line[:250]
            if stop_re.match(line):
                continue
            # Нет смысла брать строки без букв
            if not any(c.isalpha() for c in line):
                continue

            key = line[:50]
            if key in seen:
                continue
            seen.add(key)
            fragments.append(line)

        if len(fragments) >= max_fragments * 3:
            break

    if not fragments:
        print(f"  [WARN] No meaningful fragments extracted from sections")
        return []

    # Сортируем по длине + буквенному содержанию
    scored = []
    for f in fragments:
        alpha_ratio = sum(1 for c in f if c.isalpha()) / max(len(f), 1)
        digit_ratio = sum(1 for c in f if c.isdigit()) / max(len(f), 1)
        score = len(f) * alpha_ratio - len(f) * digit_ratio * 0.5
        scored.append((score, f))

    scored.sort(key=lambda x: -x[0])
    top = [f for _, f in scored[:max_fragments]]

    print(f"  Extracted {len(top)} fragments from {len(fragments)} candidates (from {len(sections)} sections):")
    for i, frag in enumerate(top):
        print(f"    [{i+1}] ({len(frag)} chars) {frag[:120]}...")

    return top


# ─── Main ────────────────────────────────────────────────────────────────
def main():
    global failed

    print(f"\n{'#'*70}")
    print(f"  UNIVERSAL PDF LOADER (sections-based verification)")
    print(f"  Target: {GW}")
    print(f"  PDF:    {PDF.name}")
    print(f"{'#'*70}\n")

    # ─── Auth ────────────────────────────────────────────────────────────
    log("Auth — get JWT token")
    try:
        r = requests.post(
            f"{GW}/auth/token",
            json={"username": "admin@example.com", "password": "Admin1234!"},
            timeout=10,
        )
        assert r.status_code == 200, f"HTTP {r.status_code}"
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        ok(f"Token: {token[:40]}...")
    except Exception as e:
        fail(f"Auth: {e}")
        try:
            r = requests.post(
                f"{GW}/auth/token",
                json={"username": "admin", "password": "admin"},
                timeout=10,
            )
            assert r.status_code == 200
            token = r.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            ok(f"Auth with admin/admin, token: {token[:40]}...")
        except Exception as e2:
            fail(f"Auth also failed: {e2}")
            sys.exit(1)

    # ─── Compute hash + cleanup ──────────────────────────────────────────
    log("Compute file hash")
    with open(PDF, "rb") as f:
        file_bytes = f.read()
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    print(f"  SHA256: {file_hash[:24]}...")
    print(f"  Size:   {len(file_bytes)} bytes")

    # Cleanup stale drafts with same hash
    log("Cleanup stale drafts")
    try:
        r = requests.get(f"{GW}/drafts", headers=headers, timeout=10)
        if r.status_code == 200:
            drafts = r.json().get("data", [])
            for d in drafts:
                if d.get("document_key") == file_hash or (
                    d.get("file_key", "").startswith(f"f-{file_hash[:12]}")
                ):
                    print(f"  Delete stale draft_id={d['id']}")
                    requests.delete(f"{GW}/drafts/{d['id']}", headers=headers, timeout=10)
                    time.sleep(0.5)
    except Exception as e:
        print(f"  [WARN] Cleanup error (non-fatal): {e}")

    # ─── Upload ──────────────────────────────────────────────────────────
    log("Upload PDF")
    upload_success = False
    for attempt in range(2):
        try:
            with open(PDF, "rb") as f:
                r = requests.post(
                    f"{GW}/drafts",
                    files={"file": (PDF.name, f, "application/pdf")},
                    data={
                        "document_key": file_hash,
                        "source_type": DOC_META["source_type"],
                        "title": DOC_META["title"],
                        "doc_code": DOC_META["doc_code"],
                        "era": DOC_META["era"],
                        "jurisdiction": DOC_META["jurisdiction"],
                    },
                    headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
                    timeout=30,
                )
        except requests.Timeout:
            fail(f"Upload timeout (attempt {attempt + 1})")
            continue
        except Exception as e:
            fail(f"Upload error: {e}")
            continue

        print(f"  HTTP {r.status_code}")

        if r.status_code == 409 and attempt == 0:
            print("  409 DUPLICATE — trying to delete and retry...")
            try:
                resp = requests.get(f"{GW}/drafts", headers=headers, timeout=10)
                if resp.status_code == 200:
                    for d in resp.json().get("data", []):
                        if d.get("document_key") == file_hash:
                            print(f"  Delete draft_id={d['id']}")
                            requests.delete(f"{GW}/drafts/{d['id']}", headers=headers, timeout=10)
                            time.sleep(1)
            except Exception:
                pass
            continue

        if r.status_code in (200, 202):
            upload_success = True
            break

        fail(f"Unexpected status: {r.status_code} {r.text[:200]}")
        break

    if not upload_success:
        fail("Upload failed after retries")
        sys.exit(1)

    data = r.json()
    draft_id = data.get("draft_id")
    task_id = data.get("task_id")
    print(f"  draft_id={draft_id}, task_id={task_id}")
    assert draft_id, f"No draft_id in response: {data}"

    # ─── Start Preview ───────────────────────────────────────────────────
    log("Start preview")
    try:
        r = requests.post(f"{GW}/drafts/{draft_id}/preview", headers=headers, timeout=30)
        assert r.status_code in (200, 202), f"HTTP {r.status_code}"
        print(f"  Preview started: HTTP {r.status_code}")
    except Exception as e:
        fail(f"Preview start failed: {e}")

    # ─── Wait for Preview (polling) ──────────────────────────────────────
    log(f"Wait for preview completion (timeout: {PREVIEW_TIMEOUT}s)")
    preview_ok = False
    for i in range(PREVIEW_TIMEOUT // 2 + 1):
        try:
            r = requests.get(
                f"{GW}/drafts/{draft_id}/preview/status?longpoll=0",
                headers=headers,
                timeout=10,
            )
            if r.status_code != 200:
                time.sleep(2)
                continue
            data = r.json()
            s = data.get("status", "")
            pp = data.get("progress_percent", 0)
            preview_steps = data.get("preview_steps", data.get("steps", []))
            step_statuses = {st.get("step_name","?"): st.get("status","?") for st in preview_steps}
            print(f"  [{i+1}] Preview: {s}, {pp}%  steps={step_statuses}")
            if s == "completed":
                preview_ok = True
                meta = data.get("preview", {})
                print(f"    doc_code: {meta.get('doc_code')}")
                print(f"    title:   {str(meta.get('title', ''))[:80]}")
                print(f"    year:    {meta.get('year')}")
                print(f"    pages:   {meta.get('pages')}")
                break
            elif s in ("failed", "error"):
                print(f"    Preview failed: {r.json()}")
                break
        except Exception as e:
            print(f"  [{i+1}] Poll error: {e}")
        time.sleep(2)

    if not preview_ok:
        print(f"  [WARN] Preview did not complete, continuing anyway...")

    # ─── Approve ─────────────────────────────────────────────────────────
    log("Approve draft (start full pipeline)")
    try:
        r = requests.patch(
            f"{GW}/drafts/{draft_id}/decide",
            json={"action": "approve"},
            headers={**headers, "Content-Type": "application/json"},
            timeout=30,
        )
        print(f"  Decide: HTTP {r.status_code}")
        assert r.status_code in (200, 202), f"Decide failed: {r.status_code} {r.text[:300]}"

        resp_data = r.json()
        document_id = resp_data.get("document_id")
        task_id = resp_data.get("task_id") or task_id
        print(f"  document_id={document_id}, task_id={task_id}")
    except Exception as e:
        fail(f"Approve failed: {e}")
        sys.exit(1)

    # Если task_id нет — получить из списка задач draft
    if not task_id:
        try:
            r2 = requests.get(f"{GW}/drafts/{draft_id}/tasks", headers=headers, timeout=10)
            tasks = r2.json().get("tasks", [])
            task_id = tasks[0]["task_id"] if tasks else None
            print(f"  Fetched task_id={task_id}")
        except Exception as e:
            print(f"  [WARN] Cannot fetch tasks: {e}")

    if not task_id:
        fail("No task_id available")
        sys.exit(1)

    # ─── Wait for Full Pipeline ──────────────────────────────────────────
    log(f"Wait for full pipeline completion (timeout: {PIPELINE_TIMEOUT}s)")
    pipeline_ok = False

    def print_step_summary(steps_list, title=""):
        if title:
            print(f"  --- {title} ---")
        groups = {}
        for st in steps_list:
            name = st["step_name"]
            if name not in groups:
                groups[name] = {"count": 0, "statuses": Counter(), "items": []}
            groups[name]["count"] += 1
            groups[name]["statuses"][st["status"]] += 1
            groups[name]["items"].append(st)

        def sort_key(item):
            name, g = item
            has_pending = g["statuses"].get("pending", 0) > 0
            has_failed = g["statuses"].get("failed", 0) > 0
            return (0 if has_failed else (1 if has_pending else 2), name)

        for name, g in sorted(groups.items(), key=sort_key):
            status_str = ", ".join(f"{s}={c}" for s, c in sorted(g["statuses"].items()))
            marker = ""
            if g["statuses"].get("failed", 0):
                marker = " !!FAILED!!"
            elif g["statuses"].get("pending", 0):
                marker = " ⏳ PENDING"
            elif g["count"] > 1:
                marker = f" 🔄 DUPLICATE x{g['count']}"
            print(f"    {name:30s} | {status_str:30s}{marker}")

            for si in g["items"]:
                if si["status"] in ("pending", "failed"):
                    started = si.get("started_at", "")[:19] if si.get("started_at") else "-"
                    duration = ""
                    if si.get("started_at") and si.get("completed_at"):
                        try:
                            t1 = datetime.datetime.fromisoformat(si["started_at"].replace("Z", "+00:00"))
                            t2 = datetime.datetime.fromisoformat(si["completed_at"].replace("Z", "+00:00"))
                            duration = f" (dur: {(t2-t1).total_seconds():.0f}s)"
                        except: pass
                    print(f"      service={si.get('service_name','?')} started_at={started}{duration}")

        total = len(steps_list)
        unique = len(groups)
        completed = sum(1 for s in steps_list if s["status"] == "completed")
        pend = sum(1 for s in steps_list if s["status"] == "pending")
        failed_count = sum(1 for s in steps_list if s["status"] == "failed")
        print(f"    ── Total: {total} steps ({unique} unique) | completed={completed} pending={pend} failed={failed_count} ──")

    for i in range(PIPELINE_TIMEOUT // 5 + 1):
        try:
            r = requests.get(f"{GW}/tasks/{task_id}/status", headers=headers, timeout=10)
            if r.status_code != 200:
                time.sleep(5)
                continue
            d = r.json()
            s = d.get("status", "")
            stage = d.get("pipeline_stage", "")
            progress = d.get("progress_percent", 0)
            steps_list = d.get("steps", [])

            if i < 3 or i % 5 == 0 or s in ("completed", "failed"):
                print(f"\n  >>> Poll [{i+1}] status={s} stage={stage} progress={progress}%")
                print_step_summary(steps_list)

            if s == "completed":
                pipeline_ok = True
                ok(f"Pipeline completed!")
                print_step_summary(steps_list, "FINAL")
                break
            elif s == "failed":
                fail("Pipeline failed")
                print_step_summary(steps_list, "FAILURE DETAILS")
                break
        except Exception as e:
            print(f"  [{i+1}] Poll error: {e}")
        time.sleep(5)
    else:
        fail(f"Pipeline did not complete in {PIPELINE_TIMEOUT}s")
        try:
            r = requests.get(f"{GW}/tasks/{task_id}/status", headers=headers, timeout=10)
            if r.status_code == 200:
                print_step_summary(r.json().get("steps", []), "FINAL TIMEOUT STATE")
        except:
            pass

    # ─── Get fragments from Registry sections ───────────────────────────
    log("Fetch parsed text from Registry (document sections)")
    fragments = []
    if document_id and pipeline_ok:
        try:
            r = requests.get(
                f"{GW}/registry/documents/{document_id}/sections",
                headers=headers,
                timeout=15,
            )
            if r.status_code == 200:
                bundle = r.json().get("data", {})
                sections = bundle.get("sections", [])
                print(f"  Got {len(sections)} sections from Registry")

                # Извлекаем фрагменты из секций
                fragments = extract_fragments_from_sections(sections, EXTRACT_FRAGMENTS)
                if not fragments:
                    print(f"  [WARN] No fragments from sections, trying fallback")
                    # Fallback: собрать сырой текст из всех секций
                    all_text = " ".join(s.get("content", "") or "" for s in sections)
                    words = [w for w in all_text.split() if len(w) > 3 and w.isalpha()]
                    unique = list(dict.fromkeys(words))
                    fragments = [" ".join(unique[i:i+5]) for i in range(0, min(len(unique), 40), 5)][:EXTRACT_FRAGMENTS]
                    print(f"  Fallback: {len(fragments)} word-group fragments")
            elif r.status_code == 404:
                print(f"  [WARN] Document sections not found yet (HTTP 404)")
            else:
                print(f"  [WARN] Registry sections: HTTP {r.status_code}")
        except Exception as e:
            print(f"  [WARN] Cannot fetch sections: {e}")
    else:
        print(f"  [SKIP] No document_id or pipeline failed")

    # ─── Verify in Registry ──────────────────────────────────────────────
    log("Verify document in registry")
    if document_id:
        try:
            r = requests.get(f"{GW}/registry/documents/{document_id}", headers=headers, timeout=10)
            if r.status_code == 200:
                doc = r.json().get("data", {})
                print(f"  ID: {doc.get('id')}, Status: {doc.get('status')}")
                print(f"  Title: {str(doc.get('title', ''))[:80]}")
                print(f"  Chunks: {doc.get('chunk_count', 'N/A')}")
            else:
                print(f"  HTTP {r.status_code}")
        except Exception as e:
            print(f"  [WARN] Registry query: {e}")

    # ─── Search & Verify Fragments ───────────────────────────────────────
    log("SEARCH & VERIFY — проверка фрагментов через RAG Search")
    verified_count = 0

    if not fragments:
        print(f"  [SKIP] No fragments to search")
    else:
        for idx, fragment in enumerate(fragments):
            print(f"\n  --- Fragment [{idx + 1}/{len(fragments)}]: \"{fragment[:80]}...\" ---")
            try:
                r = requests.post(
                    f"{GW}/rag/search",
                    json={"query": fragment, "valid_at": "2025-01-01"},
                    headers={**headers, "Content-Type": "application/json; charset=utf-8"},
                    timeout=120,
                )
            except requests.Timeout:
                print(f"  [WARN] Gateway timeout, trying direct rag-search...")
                try:
                    direct_url = f"http://localhost:8091/api/v1/rag/search"
                    r = requests.post(
                        direct_url,
                        json={"query": fragment, "valid_at": "2025-01-01"},
                        headers={"Content-Type": "application/json; charset=utf-8"},
                        timeout=120,
                    )
                    if r.status_code == 200:
                        print(f"  Direct rag-search: OK")
                    else:
                        print(f"  Direct rag-search: HTTP {r.status_code}")
                        continue
                except Exception:
                    print(f"  Direct rag-search also failed")
                    continue
            except Exception as e:
                print(f"  [WARN] Search error: {e}")
                continue

            if r.status_code in (404, 422):
                print(f"  HTTP {r.status_code} — пробую напрямую rag-search")
                try:
                    direct_url = f"http://localhost:8091/api/v1/rag/search"
                    r = requests.post(
                        direct_url,
                        json={"query": fragment, "valid_at": "2025-01-01"},
                        headers={"Content-Type": "application/json; charset=utf-8"},
                        timeout=120,
                    )
                    if r.status_code == 200:
                        print(f"  Direct rag-search: OK")
                    else:
                        print(f"  Direct rag-search: HTTP {r.status_code}")
                        continue
                except Exception:
                    print(f"  Direct rag-search also failed")
                    continue

            if r.status_code != 200:
                print(f"  HTTP {r.status_code}: {r.text[:200]}")
                continue

            data = r.json()
            results = data.get("results", [])
            total = data.get("total_found", 0)

            fragment_lower = fragment.lower()
            fragment_words = set(fragment_lower.split()[:5])

            found_in_results = False
            docs_found = set()
            if results:
                print(f"  total_found={total}, results_in_page={len(results)}")
                for rr in results[:5]:
                    content = rr["source"].get("content", "")
                    score = rr["retrieval"].get("score", 0)
                    doc_id = rr["source"].get("document_id", "?")
                    docs_found.add(doc_id)
                    print(f"    [score={score:.3f}] doc_id={doc_id} len={len(content)}")
                    print(f"      {content[:150]}...")
                    if fragment_lower in content.lower():
                        found_in_results = True
                    if not found_in_results:
                        content_words = set(content.lower().split())
                        overlap = len(fragment_words & content_words)
                        if overlap >= 2 and len(fragment_words) >= 3:
                            found_in_results = True

                if document_id and str(document_id) in docs_found:
                    print(f"  ✓ OUR DOCUMENT (id={document_id}) is in results!")
                elif docs_found:
                    print(f"  ⚠ Only OTHER docs found: {docs_found}, ours={document_id}")
            elif total > 0:
                print(f"  total_found={total} but no results in response")
            else:
                print(f"  No results")

            if found_in_results:
                verified_count += 1
                print(f"  ✓ VERIFIED")
            else:
                print(f"  ✗ NOT VERIFIED (fragment not found in search results)")

    # ─── Final Report ────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  FINAL REPORT")
    print(f"{'='*70}")
    print(f"  PDF:            {PDF.name}")
    print(f"  Pipeline:       {'✓ COMPLETED' if pipeline_ok else '✗ FAILED / TIMEOUT'}")
    print(f"  Sections:       {'✓ Fetched' if fragments else '✗ Not available'}")
    print(f"  Fragments:      {verified_count}/{len(fragments)} verified via search")
    print(f"")
    print(f"  Draft ID:       {draft_id}")
    print(f"  Task ID:        {task_id}")
    print(f"  Document ID:    {document_id}")
    print(f"{'='*70}")

    if failed:
        print(f"\n  [FAIL] Some checks failed")
        sys.exit(1)
    elif pipeline_ok and fragments and verified_count >= max(1, len(fragments) // 2):
        print(f"\n  [PASS] All critical checks passed")
        sys.exit(0)
    elif pipeline_ok:
        print(f"\n  [INFO] Pipeline completed, but fragment verification low")
        sys.exit(2)
    else:
        print(f"\n  [FAIL] Pipeline did not complete")
        sys.exit(1)


if __name__ == "__main__":
    main()
