"""Wait for existing task and save result."""
import httpx, time, json, sys

BASE = "http://localhost:5001"
OUT = r"H:\Projects\PKB_neuroassistant_develop\data\tests\result_formula.json"
task_id = "c5ffb62b-4473-4c82-a2a1-83368f60de08"

for i in range(60):
    time.sleep(10)
    try:
        poll = httpx.get(f"{BASE}/v1/status/poll/{task_id}", timeout=30)
        pd = poll.json()
        st = pd.get("task_status", "?")
        pos = pd.get("task_position", "")
        msg = f"pos={pos}" if pos else f"status={st}"
        print(f"[{i*10}s] {msg}", flush=True)
        if st in ("completed", "success"):
            rr = httpx.get(f"{BASE}/v1/result/{task_id}", timeout=30)
            rd = rr.json()
            doc = rd.get("result", {}).get("document", {})
            text = json.dumps(doc)
            print(f"formula refs: {text.count('formula')}", flush=True)
            items = doc.get("items", [])
            fi = [i for i in items if i.get("label") == "formula"]
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

print("TIMEOUT", flush=True)
