import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_e2e_build_status_delete(app: FastAPI) -> None:
    doc_id = 420000
    payload = {
        "document_id": doc_id,
        "sections": [
            {
                "section_id": 1,
                "document_id": doc_id,
                "clause": "1",
                "title": None,
                "level": 1,
                "path": "1",
                "page": 1,
                "type": "text",
                "content": {"text": "test text"},
            }
        ],
        "protected_spans": [],
        "options": {"strategy": "semantic_1024"},
    }
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        build = await client.post("/api/v1/rag/build", json=payload)
        assert build.status_code == 202
        assert build.json()["status"] == "indexed"

        status = await client.get(f"/api/v1/rag/build/{doc_id}/status?longpoll=1")
        assert status.status_code == 200
        assert status.json()["status"] in {"indexed", "pending"}

        delete = await client.delete(f"/api/v1/rag/build/{doc_id}")
        assert delete.status_code == 200
        assert delete.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_e2e_health_endpoints(app: FastAPI) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        health = await client.get("/api/v1/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"
        assert health.json()["service"] == "rag-builder"
        assert health.json()["version"] == "1.0.0"
        assert isinstance(health.json()["uptime_seconds"], int)
