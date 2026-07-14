"""Тест formula enrichment — 1 страница."""
import httpx, time, json, sys, os
from pathlib import Path

PDF = Path(__file__).parent.parent / "pdf_check" / "2-020101-174-3.pdf"
BASE = "http://localhost:5001"
OUT = Path(__file__).parent / "result_formula.json"

for i in range(30):
    try:
        if httpx.get(f"{BASE}/health", timeout=5).status_code == 200: break
    except: pass
    time.sleep(3)
else:
    print("Server not ready", flush=True); sys.exit(1)

boundary = "----DoclingTest"
parts = [
    f"--{boundary}\r\nContent-Disposition: form-data; name=\"to_formats\"\r\n\r\njson\r\n".encode(),
    f"--{boundary}\r\nContent-Disposition: form-data; name=\"do_formula_enrichment\"\r\n\r\ntrue\r\n".encode(),
    f"--{boundary}\r\nContent-Disposition: form-data; name=\"do_ocr\"\r\n\r\ntrue\r\n".encode(),
    f"--{boundary}\r\nContent-Disposition: form-data; name=\"do_table_structure\"\r\n\r\ntrue\r\n".encode(),
    f"--{boundary}\r\nContent-Disposition: form-data; name=\"include_images\"\r\n\r\nfalse\r\n".encode(),
    f"--{boundary}\r\nContent-Disposition: form-data; name=\"page_range\"\r\n\r\n18\r\n".encode(),
    f"--{boundary}\r\nContent-Disposition: form-data; name=\"page_range\"\r\n\r\n18\r\n".encode(),
    f"--{boundary}\r\nContent-Disposition: form-data; name=\"files\"; filename=\"{PDF.name}\"\r\nContent-Type: application/pdf\r\n\r\n".encode(),
    PDF.read_bytes(), b"\r\n",
    f"--{boundary}--\r\n".encode(),
]
r = httpx.post(f"{BASE}/v1/convert/file/async", content=b"".join(parts),
               headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}, timeout=60)
data = r.json()
task_id = data.get("task_id")
print(f"Task: {task_id}", flush=True)
if not task_id: print(f"Error: {data}", flush=True); sys.exit(1)

for i in range(120):
    time.sleep(10)
    try:
        poll = httpx.get(f"{BASE}/v1/status/poll/{task_id}", timeout=30)
        pd = poll.json()
        st = pd.get("task_status", "?")
        print(f"[{i*10}s] task_status={st}", flush=True)
        if st in ("completed", "success"):
            rr = httpx.get(f"{BASE}/v1/result/{task_id}", timeout=30)
            rd = rr.json()
            doc = rd.get("result", {}).get("document", {})
            text = json.dumps(doc)
            print(f"formula refs: {text.count('formula')}", flush=True)
            print(f"figure.formula: {text.count('class=\"formula\"')}", flush=True)
            items = doc.get("items", [])
            fi = [i for i in items if isinstance(i, dict) and i.get("label") == "formula"]
            print(f"formula items: {len(fi)}", flush=True)
            if fi:
                for f in fi[:5]:
                    print(json.dumps(f, indent=2, ensure_ascii=False)[:500], flush=True)
            else:
                labels = {}
                for i in items[:200]:
                    labels[i.get("label", "?")] = labels.get(i.get("label", "?"), 0) + 1
                print(f"labels: {labels}", flush=True)
            with open(OUT, "w", encoding="utf-8") as f:
                json.dump(rd, f, indent=2, ensure_ascii=False)
            print(f"Saved: {OUT}", flush=True)
            sys.exit(0)
        elif st in ("failed", "error", "failure"):
            print(f"ERROR: {pd.get('error_message','')[:500]}", flush=True)
            sys.exit(1)
    except Exception as e:
        print(f"[{i*10}s] error: {e}", flush=True)

print("TIMEOUT", flush=True); sys.exit(1)
