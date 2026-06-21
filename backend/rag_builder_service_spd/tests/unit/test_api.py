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
    assert status_data["status"] == "indexed"
    assert status_data["chunks_count"] == 3
    assert status_data["has_embeddings"] is True
    assert status_data["indexed_at"] is not None

    assert status_data["index_stats"]["sections"] == len(payload["sections"])
    assert status_data["index_stats"]["chunks"] == 3
    assert status_data["index_stats"]["embeddings"] == 3

    assert status_data["warnings"] == []
    assert status_data["errors"] == []

def test_index_endpoint_persists_no_indexable_content_warning():
    payload = {
        "metadata": {
            "schema": "schema_registry_for_rag_v2",
            "document_id": 990001,
        },
        "document": {
            "id": 990001,
            "pkb_code": "04",
            "doc_code": "SMOKE-EMPTY",
            "title": "Smoke empty document",
        },
        "sections": [
            {
                "section_id": 1,
                "parent_id": None,
                "clause": "1",
                "title": None,
                "level": 1,
                "path": "1",
                "page": 1,
                "bbox": None,
                "type": "text",
                "content": {
                    "text": "",
                },
                "references": [],
            }
        ],
        "terminology": [],
        "options": {},
    }

    response = client.post("/index", json=payload)

    assert response.status_code == 202

    data = response.json()

    assert data["status"] == "indexing"
    assert data["document_id"] == payload["metadata"]["document_id"]
    assert data["indexing_txn_id"]

    status_response = client.get(
        f"/index/status/{data['indexing_txn_id']}"
    )

    assert status_response.status_code == 200

    status_data = status_response.json()

    assert status_data["document_id"] == payload["metadata"]["document_id"]
    assert status_data["indexing_txn_id"] == data["indexing_txn_id"]
    assert status_data["status"] == "indexed"
    assert status_data["chunks_count"] == 0
    assert status_data["has_embeddings"] is False

    assert status_data["index_stats"]["sections"] == 1
    assert status_data["index_stats"]["chunks"] == 0
    assert status_data["index_stats"]["embeddings"] == 0

    assert len(status_data["warnings"]) == 1
    assert status_data["warnings"][0]["code"] == "NO_INDEXABLE_CONTENT"
    assert status_data["warnings"][0]["section_id"] is None
    assert status_data["errors"] == []
