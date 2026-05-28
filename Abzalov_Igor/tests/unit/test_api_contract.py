from uuid import uuid4

from fastapi.testclient import TestClient

from rag_builder.api.app import create_app


def test_openapi_and_contract_shape() -> None:
    client = TestClient(create_app())
    spec = client.get("/openapi.json")
    assert spec.status_code == 200
    paths = spec.json()["paths"]
    assert "/api/v1/rag/build" in paths
    assert "/api/v1/rag/build/{doc_id}" in paths
    assert "/api/v1/rag/build/{doc_id}/status" in paths


def test_build_minimal_payload_accepted() -> None:
    client = TestClient(create_app())
    payload = {"document_id": str(uuid4()), "sections": [], "protected_spans": [], "options": {}}
    resp = client.post("/api/v1/rag/build", json=payload)
    assert resp.status_code == 201
