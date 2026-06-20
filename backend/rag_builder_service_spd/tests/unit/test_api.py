# tests/unit/test_api.py

import json
from pathlib import Path

from fastapi.testclient import TestClient

from rag_builder.api.app import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["service"] == "rag_builder_service_spd"
    assert data["database"] == "ok"


def test_index_endpoint():
    json_path = Path("examples/gost_20868_81.json")

    with open(json_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    response = client.post("/index", json=payload)

    assert response.status_code == 202

    data = response.json()

    assert data["status"] == "indexing"
    assert data["document_id"] == payload["metadata"]["document_id"]
    assert data["indexing_txn_id"]
    assert "task_id" in data

    status_response = client.get(
        f"/index/status/{data['indexing_txn_id']}"
    )

    assert status_response.status_code == 200

    status_data = status_response.json()

    assert status_data["document_id"] == payload["metadata"]["document_id"]
    assert status_data["indexing_txn_id"] == data["indexing_txn_id"]
    assert status_data["status"] in {
        "pending_index",
        "indexing",
        "indexed",
        "failed",
    }
