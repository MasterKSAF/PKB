from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from rag_builder.api.app import create_app
from rag_builder.models.contracts import BuildResponse


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


class TestOpenAPI:
    def test_openapi_and_contract_shape(self, client: TestClient) -> None:
        spec = client.get("/openapi.json")
        assert spec.status_code == 200
        paths = spec.json()["paths"]
        assert "/api/v1/rag/build" in paths
        assert "/api/v1/rag/build/{doc_id}" in paths
        assert "/api/v1/rag/build/{doc_id}/status" in paths
        assert "/api/v1/health" in paths
        assert "/api/v1/rag/health" not in paths
        assert "/api/v1/rag/health/live" not in paths
        assert "/api/v1/rag/health/ready" not in paths

    def test_health_endpoint(self, client: TestClient) -> None:
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        body = resp.json()
        # Without DB, health returns "degraded"; with DB returns "ok"
        assert body["status"] in ("ok", "degraded")
        assert body["service"] == "rag-builder"
        assert isinstance(body["uptime_seconds"], int)


@pytest.mark.asyncio
async def test_build_minimal_payload_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_build(req, session):  # type: ignore[no-untyped-def]
        return BuildResponse(
            document_id=req.document_id,
            status="indexed",
            indexed_at=datetime.now(timezone(timedelta(hours=3))),
            chunks_count=0,
            index_stats={"sections": 0, "chunks": 0, "embeddings": 0},
        )

    monkeypatch.setattr("rag_builder.api.v1.rag_routes.indexing_service.build", fake_build)
    client = TestClient(create_app())
    payload = {"document_id": 1, "sections": [], "protected_spans": [], "options": {}}
    resp = client.post("/api/v1/rag/build", json=payload)
    assert resp.status_code == 202


@pytest.mark.asyncio
async def test_build_document3_payload_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_build(req, session):  # type: ignore[no-untyped-def]
        return BuildResponse(
            document_id=req.document_id,
            status="indexed",
            indexed_at=datetime.now(timezone(timedelta(hours=3))),
            chunks_count=1,
            index_stats={"sections": 1, "chunks": 1, "embeddings": 1},
        )

    monkeypatch.setattr("rag_builder.api.v1.rag_routes.indexing_service.build", fake_build)
    client = TestClient(create_app())
    doc_id = 420001
    payload = {
        "metadata": {"schema": "for_rag_v1", "document_id": doc_id, "created_at": "2026-05-28T12:00:00Z"},
        "document": {"id": doc_id, "doc_code": "TEST-001", "title": "Test"},
        "sections": [
            {
                "section_id": 1,
                "document_id": doc_id,
                "parent_id": None,
                "clause": "1",
                "title": None,
                "level": 1,
                "path": "1",
                "page": 1,
                "bbox": [10, 20, 200, 40],
                "type": "text",
                "content": {"text": "sample"},
                "created_at": "2026-05-28T12:00:00Z",
            }
        ],
        "terminology": [{"term": "t", "definition": "d"}],
        "protected_spans": [],
        "options": {"strategy": "semantic_1024"},
    }
    resp = client.post("/api/v1/rag/build", json=payload)
    assert resp.status_code == 202


class TestBuildValidation:
    """Tests real HTTP 422 validation — no DB, no mocking needed."""

    def test_missing_document_id_returns_422(self, client: TestClient) -> None:
        payload = {"sections": []}
        resp = client.post("/api/v1/rag/build", json=payload)
        assert resp.status_code == 422
        errors = resp.json()["detail"]
        assert any("document_id" in str(e) for e in errors)

    def test_missing_sections_returns_422(self, client: TestClient) -> None:
        payload = {"document_id": 1}
        resp = client.post("/api/v1/rag/build", json=payload)
        assert resp.status_code == 422

    def test_page_0_returns_422(self, client: TestClient) -> None:
        payload = {
            "document_id": 1,
            "sections": [{
                "section_id": 1, "document_id": 1, "level": 1, "path": "1",
                "page": 0, "type": "text", "content": {"text": "x"},
            }],
        }
        resp = client.post("/api/v1/rag/build", json=payload)
        assert resp.status_code == 422
        assert any("page must be 1-based" in str(e) for e in resp.json()["detail"])

    def test_duplicate_section_id_returns_422(self, client: TestClient) -> None:
        payload = {
            "document_id": 1,
            "sections": [
                {"section_id": 1, "document_id": 1, "level": 1, "path": "1", "type": "text", "content": {"text": "a"}},
                {"section_id": 1, "document_id": 1, "level": 1, "path": "2", "type": "text", "content": {"text": "b"}},
            ],
        }
        resp = client.post("/api/v1/rag/build", json=payload)
        assert resp.status_code == 422
        assert any("duplicate section_id" in str(e) for e in resp.json()["detail"])

    def test_invalid_parent_id_returns_422(self, client: TestClient) -> None:
        payload = {
            "document_id": 1,
            "sections": [
                {"section_id": 1, "document_id": 1, "level": 1, "path": "1", "type": "text", "content": {"text": "a"}, "parent_id": 999},
            ],
        }
        resp = client.post("/api/v1/rag/build", json=payload)
        assert resp.status_code == 422
        assert any("non-existent section_id" in str(e) for e in resp.json()["detail"])

    def test_document_id_mismatch_section_returns_422(self, client: TestClient) -> None:
        payload = {
            "document_id": 1,
            "sections": [
                {"section_id": 1, "document_id": 999, "level": 1, "path": "1", "type": "text", "content": {"text": "a"}},
            ],
        }
        resp = client.post("/api/v1/rag/build", json=payload)
        assert resp.status_code == 422
        assert any("section.document_id" in str(e) for e in resp.json()["detail"])

    def test_invalid_section_type_returns_422(self, client: TestClient) -> None:
        payload = {
            "document_id": 1,
            "sections": [
                {"section_id": 1, "document_id": 1, "level": 1, "path": "1", "type": "section", "content": {"text": "a"}},
            ],
        }
        resp = client.post("/api/v1/rag/build", json=payload)
        assert resp.status_code == 422

    def test_empty_json_body_returns_422(self, client: TestClient) -> None:
        resp = client.post("/api/v1/rag/build", json={})
        assert resp.status_code == 422

    def test_non_json_body_returns_422(self, client: TestClient) -> None:
        resp = client.post("/api/v1/rag/build", content="not json", headers={"Content-Type": "application/json"})
        assert resp.status_code == 422

    def test_string_document_id_returns_422(self, client: TestClient) -> None:
        """document_id must be int, not string."""
        payload = {"document_id": "not-a-number", "sections": []}
        resp = client.post("/api/v1/rag/build", json=payload)
        assert resp.status_code == 422



