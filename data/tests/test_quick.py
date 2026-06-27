"""
Quick targeted test: upload -> preview -> approve -> wait for pipeline
"""
import requests, time, uuid, hashlib, sys, json
from pathlib import Path

from config import get_api_url

GW = get_api_url()
PDF = Path("data/pdf/7bd97d737317a8a272bb18a405ab2d04.pdf")
print(f"Target: {GW}")
print(f"Target: {GW}")

# Auth
r = requests.post(f"{GW}/auth/token", json={"username":"admin@example.com","password":"Admin1234!"})
t = r.json()["access_token"]
h = {"Authorization": f"Bearer {t}"}

# Compute hash
file_hash = hashlib.sha256(open(PDF,"rb").read()).hexdigest()

# Cleanup old
for id in list(range(8,20)):
    requests.delete(f"{GW}/drafts/{id}", headers=h)
    requests.delete(f"{GW}/documents/{id}", headers=h)

# Upload
with open(PDF, "rb") as f:
    r = requests.post(f"{GW}/drafts",
        files={"file": (PDF.name, f, "application/pdf")},
        data={"document_key": file_hash, "source_type":"GOST", "title":"GOST 10054-82","doc_code":"10054-82","era":"USSR"},
        headers={**h, "Idempotency-Key": str(uuid.uuid4())})
print(f"Upload: HTTP {r.status_code}, draft={r.json().get('draft_id')}")
draft_id = r.json()["draft_id"]

# Preview
requests.post(f"{GW}/drafts/{draft_id}/preview", headers=h)
for i in range(20):
    r = requests.get(f"{GW}/drafts/{draft_id}/preview/status?longpoll=0", headers=h)
    s = r.json().get("status","")
    print(f"  Preview: {s}")
    if s == "completed": break
    time.sleep(2)

# Approve
r = requests.patch(f"{GW}/drafts/{draft_id}/decide", json={"action":"approve"}, headers=h)
print(f"Approve: HTTP {r.status_code}")
doc_id = r.json().get("document_id")
print(f"  document_id={doc_id}")

# Poll task status
task_id = r.json().get("task_id")
if not task_id:
    r2 = requests.get(f"{GW}/drafts/{draft_id}/tasks", headers=h)
    task_id = r2.json().get("tasks",[{}])[0].get("task_id")
print(f"  task_id={task_id}")

for i in range(60):
    r = requests.get(f"{GW}/tasks/{task_id}/status", headers=h)
    d = r.json()
    s, stg, pct = d.get("status",""), d.get("pipeline_stage",""), d.get("progress_percent",0)
    steps = {s["step_name"]: s["status"] for s in d.get("steps",[])}
    if i < 3 or i%6==0 or s in ("completed","failed"):
        print(f"  [{i+1}] status={s} stage={stg} progress={pct}% steps={steps}")
    if s in ("completed","failed"): break
    time.sleep(5)

print(f"\nFinal: status={s}")
print(f"Steps: {json.dumps(steps, indent=2)}")
