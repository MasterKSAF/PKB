"""Fast target: upload -> approve -> wait -> search"""
import requests, time, uuid, hashlib, sys
from pathlib import Path

from config import get_api_url

GW = get_api_url()
PDF = Path("data/pdf/7bd97d737317a8a272bb18a405ab2d04.pdf")
print(f"Target: {GW}")

# Auth
r = requests.post(f"{GW}/auth/token", json={"username":"admin@example.com","password":"Admin1234!"})
t = r.json()["access_token"]; h = {"Authorization": f"Bearer {t}"}
print(f"Auth OK")

# Clean
file_hash = hashlib.sha256(open(PDF,"rb").read()).hexdigest()
for id in [13,14,15]: requests.delete(f"{GW}/drafts/{id}", headers=h); requests.delete(f"{GW}/documents/{id}", headers=h)

# Upload (skip preview - go straight)
with open(PDF,"rb") as f:
    r = requests.post(f"{GW}/drafts", files={"file":(PDF.name,f,"application/pdf")},
        data={"document_key":file_hash,"source_type":"GOST","title":"GOST 10054-82","doc_code":"10054-82","era":"USSR"},
        headers={**h,"Idempotency-Key":str(uuid.uuid4())})
draft = r.json()["draft_id"]
print(f"Upload: draft={draft}")

# Start preview + immediately approve (no wait)
requests.post(f"{GW}/drafts/{draft}/preview", headers=h)
time.sleep(3)
r = requests.patch(f"{GW}/drafts/{draft}/decide", json={"action":"approve"}, headers=h)
print(f"Approve: HTTP {r.status_code}")
task_id = r.json().get("task_id")
doc_id = r.json().get("document_id")
if not task_id:
    r2 = requests.get(f"{GW}/drafts/{draft}/tasks", headers=h)
    task_id = r2.json()["tasks"][0]["task_id"]
print(f"  task_id={task_id}, doc_id={doc_id}")

# Wait for pipeline (fast poll)
for i in range(30):
    r = requests.get(f"{GW}/tasks/{task_id}/status", headers=h)
    d = r.json()
    s, pct = d.get("status",""), d.get("progress_percent",0)
    steps = {s["step_name"]: s["status"] for s in d.get("steps",[])}
    if s in ("completed","failed") or i % 5 == 0:
        print(f"  [{i+1}] {s} {pct}% {steps}")
    if s in ("completed","failed"): break
    time.sleep(3)

# Search
print(f"\n=== SEARCH ===")
queries = ["шкурка шлифовальная", "зеленый карбид кремния", "шлифовальная шкурка", "ГОСТ 10054"]
for q in queries:
    r = requests.post(f"{GW}/rag/search", json={"query":q,"valid_at":"2025-01-01"},
        headers={**h,"Content-Type":"application/json; charset=utf-8"})
    if r.status_code == 200:
        results = r.json().get("results",[])
        if results:
            found = False
            for rr in results:
                c = rr["source"].get("content","").lower()
                if any(w in c for w in q.lower().split()):
                    found = True
            print(f"  [{r.status_code}] '{q[:30]}' -> {len(results)} results {'✓' if found else '⚠ no relevant'}")
            if found:
                print(f"    First: {results[0]['source']['content'][:150]}")
        else:
            print(f"  [{r.status_code}] '{q[:30]}' -> 0 results")
    else:
        print(f"  [{r.status_code}] '{q[:30]}' -> {r.text[:100]}")
