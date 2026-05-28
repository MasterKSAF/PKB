from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from rag_builder.api.app import create_app
from rag_builder.models.contracts import BuildResponse


def test_openapi_and_contract_shape() -> None:
    client = TestClient(create_app())
    spec = client.get("/openapi.json")
    assert spec.status_code == 200
    paths = spec.json()["paths"]
    assert "/api/v1/rag/build" in paths
    assert "/api/v1/rag/build/{doc_id}" in paths
    assert "/api/v1/rag/build/{doc_id}/status" in paths


@pytest.mark.asyncio
async def test_build_minimal_payload_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_build(req, session):  # type: ignore[no-untyped-def]
        return BuildResponse(
            document_id=req.document_id,
            status="completed",
            indexed_at=datetime.now(timezone(timedelta(hours=3))),
            chunks_count=0,
            index_stats={"sections": 0, "chunks": 0, "embeddings": 0},
        )

    monkeypatch.setattr("rag_builder.api.v1.rag_routes.indexing_service.build", fake_build)
    client = TestClient(create_app())
    payload = {"document_id": str(uuid4()), "sections": [], "protected_spans": [], "options": {}}
    resp = client.post("/api/v1/rag/build", json=payload)
    assert resp.status_code == 201
