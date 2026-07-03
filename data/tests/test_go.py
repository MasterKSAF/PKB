"""Quick test for rate limiting and concurrent upload"""
import requests, uuid, glob, sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from config import ensure_services
ensure_services("all")

GW = "http://localhost:8080/api/v1"
r = requests.post(f"{GW}/auth/token", json={"username":"admin@example.com","password":"Admin1234!"})
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Upload 7 different files SEQUENTIALLY (not concurrent) to test Gateway rate limiting
for fpath in sorted(glob.glob("data/pdf_tests/*.pdf")):
    fname = os.path.basename(fpath)
    doc_key = f"test-{uuid.uuid4().hex[:8]}"
    with open(fpath, "rb") as f:
        fb = f.read()
    r = requests.post(f"{GW}/drafts", files={"file": (fname, fb, "application/pdf")},
        data={"document_key": doc_key, "source_type": "RD", "title": fname,
              "doc_code": "test", "era": "RF", "jurisdiction": "RU"},
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())})
    print(f"  {fname:40s} HTTP {r.status_code:3d}  {r.text[:150]}")
