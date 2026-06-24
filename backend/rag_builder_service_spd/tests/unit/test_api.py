# tests/unit/test_api.py

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from rag_builder.api.app import app
from rag_builder.repositories.postgres_chunk_repository import PostgresChunkRepository


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


def test_api_v1_rag_build_accepts_flat_registry_payload():
    payload = {
        "document_id": 420000,
        "sections": [
            {
                "section_id": 1,
                "document_id": 420000,
                "parent_id": None,
                "clause": "1",
                "title": None,
                "level": 1,
                "path": "1",
                "page": 1,
                "bbox": None,
                "type": "text",
                "content": {
                    "text": "Настоящий стандарт распространяется...",
                },
                "references": [],
            }
        ],
        "protected_spans": [],
        "options": {
            "strategy": "semantic_1024",
        },
    }

    response = client.post("/api/v1/rag/build", json=payload)

    assert response.status_code == 202

    data = response.json()

    assert data["status"] == "indexing"
    assert data["document_id"] == payload["document_id"]
    assert data["indexing_txn_id"]


def test_api_v1_rag_build_delete_index():
    response = client.delete("/api/v1/rag/build/420000")

    assert response.status_code == 200

    data = response.json()

    assert data["document_id"] == 420000
    assert data["status"] == "completed"
    assert "deleted_count" in data



def test_api_v1_health_endpoint():
    response = client.get("/api/v1/health")

    assert response.status_code == 200

    data = response.json()

    assert data["service"] == "rag_builder_service_spd"
    assert data["database"] == "ok"


def test_api_v1_rag_build_jobs_list(monkeypatch):
    timestamp = datetime(2026, 6, 24, 12, 0, tzinfo=timezone.utc)

    def fake_list_indexing_jobs(
        self,
        status_filter=None,
        page=1,
        page_size=50,
    ):
        assert status_filter == "indexed"
        assert page == 2
        assert page_size == 10

        return [
            {
                "id": 26,
                "indexing_txn_id": "5c2d9d45-2e02-44ad-a2d7-806ba5158341",
                "document_id": 420000,
                "status": "indexed",
                "chunks_count": 3,
                "has_embeddings": True,
                "indexed_at": timestamp,
                "index_stats": {
                    "sections": 3,
                    "chunks": 3,
                    "embeddings": 3,
                },
                "warnings": [],
                "errors": [],
                "created_at": timestamp,
                "updated_at": timestamp,
            }
        ], 11

    monkeypatch.setattr(
        PostgresChunkRepository,
        "list_indexing_jobs",
        fake_list_indexing_jobs,
    )

    response = client.get(
        "/api/v1/rag/build/jobs?status=indexed&page=2&page_size=10"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["meta"] == {
        "total": 11,
        "page": 2,
        "page_size": 10,
    }

    assert len(data["items"]) == 1

    item = data["items"][0]

    assert item["id"] == 26
    assert item["document_id"] == 420000
    assert item["status"] == "indexed"
    assert item["chunks_count"] == 3
    assert item["has_embeddings"] is True
    assert item["index_stats"]["chunks"] == 3


def test_api_v1_rag_build_jobs_rejects_invalid_status():
    response = client.get(
        "/api/v1/rag/build/jobs?status=unknown"
    )

    assert response.status_code == 422
