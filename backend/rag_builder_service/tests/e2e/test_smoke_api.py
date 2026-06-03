from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_e2e_build_status_delete(app: FastAPI) -> None:
    doc_id = str(uuid4())
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
                "type": "section",
                "content": {"text": "test text"},
            }
        ],
        "protected_spans": [],
        "options": {"strategy": "semantic_512"},
    }
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        build = await client.post("/api/v1/rag/build", json=payload)
        assert build.status_code == 201
        assert build.json()["status"] == "completed"

        status = await client.get(f"/api/v1/rag/build/{doc_id}/status?longpoll=1")
        assert status.status_code == 200
        assert status.json()["status"] in {"indexed", "pending"}

        delete = await client.delete(f"/api/v1/rag/build/{doc_id}")
        assert delete.status_code == 200
        assert delete.json()["status"] == "completed"
