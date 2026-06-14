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

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "indexed"
    assert data["document_id"] == 420000
    assert data["document_version_id"] == 420001
    assert data["chunks_count"] == 3

    assert data["embedding_tokens"] == 0
    assert data["embedding_cost_usd"] == 0.0