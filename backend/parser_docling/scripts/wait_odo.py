"""
Ждёт завершения задачи ODO парсера и сохраняет результат.
Запуск: python wait_odo.py <task_id> [-o output.json]
"""
import httpx, json, sys, time
from pathlib import Path

TASK_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 42001
OUT_PATH = sys.argv[sys.argv.index('-o')+1] if '-o' in sys.argv else 'odo_full.json'
API = "http://localhost:8087/api/v1/parser"

print(f"Waiting for task {TASK_ID}...", flush=True)

while True:
    with httpx.Client(timeout=10) as c:
        r = c.get(f"{API}/process/{TASK_ID}/status?timeout=2")
        data = r.json()
        status = data.get('status')
        progress = data.get('progress_percent', 0)
        pages = data.get('pages_processed', 0)
        print(f"  Status: {status}, progress: {progress}%, pages: {pages}", flush=True)
        
        if status == 'completed':
            rr = c.get(f"{API}/process/{TASK_ID}/result", timeout=30)
            if rr.status_code == 200:
                Path(OUT_PATH).write_text(json.dumps(rr.json(), indent=2, ensure_ascii=False), encoding='utf-8')
                print(f"Saved to {OUT_PATH}", flush=True)
            else:
                print(f"Result error: {rr.status_code} {rr.text}", flush=True)
            break
        elif status == 'failed':
            print(f"Task failed: {data}", flush=True)
            break
        
        time.sleep(10)
