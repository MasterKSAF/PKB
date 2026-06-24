# tests/unit/test_api.py

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from rag_builder.api.app import app
from rag_builder.core.config import settings
from rag_builder.repositories.postgres_chunk_repository import PostgresChunkRepository


client = TestClient(app)


def test_legacy_health_endpoint_removed():
    legacy_path = "/" + "health"
    response = client.get(legacy_path)

    assert response.status_code == 404


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

def test_api_v1_rag_build_rejects_duplicate_active_job(monkeypatch):
    active_txn_id = "5c2d9d45-2e02-44ad-a2d7-806ba5158341"

    def fake_mark_stale_indexing_jobs_failed(
        self,
        stale_after_seconds,
    ):
        assert stale_after_seconds > 0
        return 0

    def fake_get_active_indexing_job_for_document(
        self,
        document_id,
        stale_after_seconds,
    ):
        assert document_id == 420000
        assert stale_after_seconds > 0

        return {
            "document_id": document_id,
            "status": "indexing",
            "indexing_txn_id": active_txn_id,
            "chunks_count": 0,
            "has_embeddings": False,
            "indexed_at": None,
            "index_stats": {},
            "warnings": [],
            "errors": [],
        }

    def fail_create_indexing_job(
        self,
        document_id,
        indexing_txn_id,
        status="indexing",
    ):
        raise AssertionError("create_indexing_job must not be called")

    monkeypatch.setattr(
        PostgresChunkRepository,
        "mark_stale_indexing_jobs_failed",
        fake_mark_stale_indexing_jobs_failed,
    )
    monkeypatch.setattr(
        PostgresChunkRepository,
        "get_active_indexing_job_for_document",
        fake_get_active_indexing_job_for_document,
    )
    monkeypatch.setattr(
        PostgresChunkRepository,
        "create_indexing_job",
        fail_create_indexing_job,
    )

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
                    "text": "????????? ???????? ????????????????...",
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

    assert response.status_code == 409

    data = response.json()

    assert data["detail"]["code"] == "ALREADY_PROCESSING"
    assert data["detail"]["details"] == {
        "document_id": 420000,
        "indexing_txn_id": active_txn_id,
        "status": "indexing",
    }

def test_api_v1_rag_build_rejects_when_active_jobs_limit_reached(monkeypatch):
    monkeypatch.setattr(settings, "MAX_ACTIVE_INDEXING_JOBS", 1)

    def fake_mark_stale_indexing_jobs_failed(
        self,
        stale_after_seconds,
    ):
        assert stale_after_seconds > 0
        return 0

    def fake_get_active_indexing_job_for_document(
        self,
        document_id,
        stale_after_seconds,
    ):
        assert document_id == 420000
        assert stale_after_seconds > 0
        return None

    def fake_count_active_indexing_jobs(
        self,
        stale_after_seconds,
    ):
        assert stale_after_seconds > 0
        return 1

    def fail_create_indexing_job(
        self,
        document_id,
        indexing_txn_id,
        status="indexing",
    ):
        raise AssertionError("create_indexing_job must not be called")

    monkeypatch.setattr(
        PostgresChunkRepository,
        "mark_stale_indexing_jobs_failed",
        fake_mark_stale_indexing_jobs_failed,
    )
    monkeypatch.setattr(
        PostgresChunkRepository,
        "get_active_indexing_job_for_document",
        fake_get_active_indexing_job_for_document,
    )
    monkeypatch.setattr(
        PostgresChunkRepository,
        "count_active_indexing_jobs",
        fake_count_active_indexing_jobs,
    )
    monkeypatch.setattr(
        PostgresChunkRepository,
        "create_indexing_job",
        fail_create_indexing_job,
    )

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
                    "text": "????????? ???????? ????????????????...",
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

    assert response.status_code == 429

    data = response.json()

    assert data["detail"]["code"] == "TOO_MANY_REQUESTS"
    assert data["detail"]["details"] == {
        "active_jobs": 1,
        "max_active_jobs": 1,
    }
