import urllib.request, json

req = urllib.request.Request(
    "http://127.0.0.1:8091/api/v1/rag/search",
    data=json.dumps({
        "query": "к чему применяется правила классификации и постройки прогулочных судов",
        "valid_at": "2026-07-09"
    }).encode(),
    headers={"Content-Type": "application/json"}
)
resp = urllib.request.urlopen(req)
data = json.loads(resp.read())

for i, r in enumerate(data["results"]):
    source = r["source"]
    meta = r["retrieval"]
    content_preview = (source.get("content") or "")[:80].replace("\n", " ")
    print(f'idx={i} chunk={meta["chunk_id"]} doc={source["document_id"]} section={source.get("section_id","?")} page={source.get("page","?")} score={meta["score"]:.4f}')
    print(f'     {content_preview}')
