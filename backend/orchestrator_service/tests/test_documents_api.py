"""
Tests for Documents API endpoints (versions, approve, history).

Covers:
  - POST /api/v1/documents/{doc_id}/versions — upload version
  - GET /api/v1/documents/{doc_id}/versions — list versions
  - POST /api/v1/documents/{doc_id}/approve — approve document
  - GET /api/v1/documents/{doc_id}/history — document history

NOTE: These endpoints are part of the Documents API group and coexist
with the Drafts API. They return mock data in mock mode.
"""

import io
from datetime import datetime

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
#  POST /api/v1/documents/{doc_id}/versions
# ---------------------------------------------------------------------------


class TestVersionCreate:
    """Tests for POST /api/v1/documents/{doc_id}/versions."""

    VERSIONS_URL = "/api/v1/documents/{doc_id}/versions"

    def test_upload_version_returns_202(self, client: TestClient, auth_header: dict):
        """Uploading a new version returns 202."""
        response = client.post(
            self.VERSIONS_URL.format(doc_id="doc-test-001"),
            files={
                "file": (
                    "v2.pdf",
                    io.BytesIO(b"%PDF-1.4 version 2 content"),
                    "application/pdf",
                )
            },
            headers=auth_header,
        )
        assert response.status_code == 202

    def test_upload_version_response_structure(
        self, client: TestClient, auth_header: dict
    ):
        """Response has all expected VersionCreateResponse fields."""
        response = client.post(
            self.VERSIONS_URL.format(doc_id="doc-test-001"),
            files={
                "file": (
                    "v2.pdf",
                    io.BytesIO(b"%PDF-1.4 version"),
                    "application/pdf",
                )
            },
            headers=auth_header,
        )
        data = response.json()
        assert "document_id" in data
        assert "version_id" in data
        assert "version_number" in data
        assert "status" in data
        assert "task_id" in data
        assert "file_hash_sha256" in data
        assert "is_duplicate_file" in data
        assert "created_at" in data

        assert data["document_id"] == "doc-test-001"
        assert isinstance(data["version_id"], str)
        assert isinstance(data["version_number"], int)
        assert isinstance(data["status"], str)
        assert isinstance(data["task_id"], int)
        assert isinstance(data["file_hash_sha256"], str)
        assert isinstance(data["is_duplicate_file"], bool)

    def test_upload_version_status_uploaded(
        self, client: TestClient, auth_header: dict
    ):
        """Version upload status should be 'uploaded'."""
        response = client.post(
            self.VERSIONS_URL.format(doc_id="doc-test-001"),
            files={
                "file": (
                    "v2.pdf",
                    io.BytesIO(b"%PDF-1.4 version"),
                    "application/pdf",
                )
            },
            headers=auth_header,
        )
        data = response.json()
        assert data["status"] == "uploaded"

    def test_upload_version_unsupported_type(
        self, client: TestClient, auth_header: dict
    ):
        """Uploading a non-PDF file type returns 400."""
        response = client.post(
            self.VERSIONS_URL.format(doc_id="doc-test-001"),
            files={
                "file": (
                    "v2.txt",
                    io.BytesIO(b"plain text"),
                    "text/plain",
                )
            },
            headers=auth_header,
        )
        assert response.status_code == 400

    def test_upload_version_without_file(
        self, client: TestClient, auth_header: dict
    ):
        """Request without file returns 422."""
        response = client.post(
            self.VERSIONS_URL.format(doc_id="doc-test-001"),
            headers=auth_header,
        )
        assert response.status_code == 422

    def test_upload_version_without_auth(self, client: TestClient):
        """Version upload works without auth in mock mode."""
        response = client.post(
            self.VERSIONS_URL.format(doc_id="doc-test-001"),
            files={
                "file": (
                    "v2.pdf",
                    io.BytesIO(b"%PDF-1.4 content"),
                    "application/pdf",
                )
            },
        )
        assert response.status_code == 202


# ---------------------------------------------------------------------------
#  GET /api/v1/documents/{doc_id}/versions
# ---------------------------------------------------------------------------


class TestVersionsList:
    """Tests for GET /api/v1/documents/{doc_id}/versions."""

    VERSIONS_URL = "/api/v1/documents/{doc_id}/versions"

    def test_list_versions_returns_200(self, client: TestClient, auth_header: dict):
        """Listing versions returns 200."""
        response = client.get(
            self.VERSIONS_URL.format(doc_id="doc-test-001"),
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_list_versions_response_structure(
        self, client: TestClient, auth_header: dict
    ):
        """Response has document_id, versions list, and meta with total."""
        response = client.get(
            self.VERSIONS_URL.format(doc_id="doc-test-001"),
            headers=auth_header,
        )
        data = response.json()
        assert "document_id" in data
        assert "versions" in data
        assert "meta" in data
        assert data["document_id"] == "doc-test-001"
        assert isinstance(data["versions"], list)
        assert "total" in data["meta"]

    def test_list_versions_item_structure(
        self, client: TestClient, auth_header: dict
    ):
        """Each version item has the expected fields."""
        response = client.get(
            self.VERSIONS_URL.format(doc_id="doc-test-001"),
            headers=auth_header,
        )
        data = response.json()
        if data["versions"]:
            version = data["versions"][0]
            assert "version_id" in version
            assert "version_number" in version
            assert "format_code" in version
            assert "format_label" in version
            assert "file_key" in version
            assert "file_hash_sha256" in version
            assert "size_bytes" in version
            assert "uploaded_at" in version
            assert "uploaded_by" in version

            assert isinstance(version["version_id"], str)
            assert isinstance(version["version_number"], int)
            assert isinstance(version["format_code"], str)
            assert isinstance(version["format_label"], str)
            assert isinstance(version["file_key"], str)
            assert isinstance(version["file_hash_sha256"], str)
            assert isinstance(version["size_bytes"], int)

    def test_list_versions_meta_total_is_int(
        self, client: TestClient, auth_header: dict
    ):
        """Meta.total is a non-negative integer."""
        response = client.get(
            self.VERSIONS_URL.format(doc_id="doc-test-001"),
            headers=auth_header,
        )
        data = response.json()
        total = data["meta"]["total"]
        assert isinstance(total, int)
        assert total >= 0

    def test_list_versions_without_auth(self, client: TestClient):
        """List versions works without auth in mock mode."""
        response = client.get(
            self.VERSIONS_URL.format(doc_id="doc-test-001"),
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
#  POST /api/v1/documents/{doc_id}/approve
# ---------------------------------------------------------------------------


class TestApproveDocument:
    """Tests for POST /api/v1/documents/{doc_id}/approve."""

    APPROVE_URL = "/api/v1/documents/{doc_id}/approve"

    def test_approve_with_force_and_comment(
        self, client: TestClient, auth_header: dict
    ):
        """Approve with force=True and a comment returns 202."""
        response = client.post(
            self.APPROVE_URL.format(doc_id="doc-test-001"),
            json={"force": True, "comment": "Утверждено главным инженером"},
            headers=auth_header,
        )
        assert response.status_code == 202

    def test_approve_without_force(self, client: TestClient, auth_header: dict):
        """Approve with force=False (default) also works."""
        response = client.post(
            self.APPROVE_URL.format(doc_id="doc-test-001"),
            json={"force": False},
            headers=auth_header,
        )
        assert response.status_code == 202

    def test_approve_default_force(self, client: TestClient, auth_header: dict):
        """Approve with empty body uses default force=False."""
        response = client.post(
            self.APPROVE_URL.format(doc_id="doc-test-001"),
            json={},
            headers=auth_header,
        )
        assert response.status_code == 202

    def test_approve_response_structure(self, client: TestClient, auth_header: dict):
        """Response has all expected ApproveResponse fields."""
        response = client.post(
            self.APPROVE_URL.format(doc_id="doc-test-001"),
            json={"force": True, "comment": "OK"},
            headers=auth_header,
        )
        data = response.json()
        assert "document_id" in data
        assert "status" in data
        assert "promotion_task_id" in data
        assert "approved_by" in data
        assert "approved_at" in data

        assert data["document_id"] == "doc-test-001"
        assert data["status"] == "approved"
        assert isinstance(data["promotion_task_id"], str)
        assert isinstance(data["approved_by"], str)
        assert isinstance(data["approved_at"], str)

    def test_approve_promotion_task_id_prefix(
        self, client: TestClient, auth_header: dict
    ):
        """promotion_task_id starts with 'promo-'."""
        response = client.post(
            self.APPROVE_URL.format(doc_id="doc-test-001"),
            json={"force": True},
            headers=auth_header,
        )
        data = response.json()
        assert data["promotion_task_id"].startswith("promo-")

    def test_approve_approved_at_iso_datetime(
        self, client: TestClient, auth_header: dict
    ):
        """approved_at is a valid ISO datetime string."""
        response = client.post(
            self.APPROVE_URL.format(doc_id="doc-test-001"),
            json={"force": True},
            headers=auth_header,
        )
        data = response.json()
        parsed = datetime.fromisoformat(data["approved_at"])
        assert parsed is not None

    def test_approve_without_auth(self, client: TestClient):
        """Approve works without auth in mock mode."""
        response = client.post(
            self.APPROVE_URL.format(doc_id="doc-test-001"),
            json={"force": True},
        )
        assert response.status_code == 202


# ---------------------------------------------------------------------------
#  GET /api/v1/documents/{doc_id}/history
# ---------------------------------------------------------------------------


class TestDocumentHistory:
    """Tests for GET /api/v1/documents/{doc_id}/history."""

    HISTORY_URL = "/api/v1/documents/{doc_id}/history"

    def test_get_history_returns_200(self, client: TestClient, auth_header: dict):
        """Getting document history returns 200."""
        response = client.get(
            self.HISTORY_URL.format(doc_id="doc-test-001"),
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_history_response_structure(self, client: TestClient, auth_header: dict):
        """Response has document_id, history list, and meta with total."""
        response = client.get(
            self.HISTORY_URL.format(doc_id="doc-test-001"),
            headers=auth_header,
        )
        data = response.json()
        assert "document_id" in data
        assert "history" in data
        assert "meta" in data
        assert data["document_id"] == "doc-test-001"
        assert isinstance(data["history"], list)
        assert "total" in data["meta"]

    def test_history_item_structure(self, client: TestClient, auth_header: dict):
        """Each history item has the expected fields."""
        response = client.get(
            self.HISTORY_URL.format(doc_id="doc-test-001"),
            headers=auth_header,
        )
        data = response.json()
        if data["history"]:
            item = data["history"][0]
            assert "history_id" in item
            assert "old_status" in item
            assert "new_status" in item
            assert "comment" in item
            assert "changed_by" in item
            assert "changed_at" in item

            assert isinstance(item["history_id"], str)
            assert isinstance(item["new_status"], str)
            assert isinstance(item["changed_by"], str)

    def test_history_comment_structure(self, client: TestClient, auth_header: dict):
        """Comment inside a history item has reason and details fields."""
        response = client.get(
            self.HISTORY_URL.format(doc_id="doc-test-001"),
            headers=auth_header,
        )
        data = response.json()
        if data["history"]:
            comment = data["history"][0].get("comment")
            if comment is not None:
                assert "reason" in comment
                assert "details" in comment
                assert isinstance(comment.get("reason"), (str, type(None)))
                assert isinstance(comment.get("details"), (str, type(None)))

    def test_history_meta_total_is_int(self, client: TestClient, auth_header: dict):
        """Meta.total is a non-negative integer."""
        response = client.get(
            self.HISTORY_URL.format(doc_id="doc-test-001"),
            headers=auth_header,
        )
        data = response.json()
        total = data["meta"]["total"]
        assert isinstance(total, int)
        assert total >= 0

    def test_history_changed_at_iso_datetime(
        self, client: TestClient, auth_header: dict
    ):
        """changed_at is a valid ISO datetime string."""
        response = client.get(
            self.HISTORY_URL.format(doc_id="doc-test-001"),
            headers=auth_header,
        )
        data = response.json()
        if data["history"]:
            parsed = datetime.fromisoformat(data["history"][0]["changed_at"])
            assert parsed is not None

    def test_history_old_status_may_be_null(
        self, client: TestClient, auth_header: dict
    ):
        """old_status can be null (first transition has no previous status)."""
        response = client.get(
            self.HISTORY_URL.format(doc_id="doc-test-001"),
            headers=auth_header,
        )
        data = response.json()
        if data["history"]:
            item = data["history"][0]
            assert item["old_status"] is None or isinstance(item["old_status"], str)

    def test_history_without_auth(self, client: TestClient):
        """History works without auth in mock mode."""
        response = client.get(
            self.HISTORY_URL.format(doc_id="doc-test-001"),
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
#  GET /api/v1/documents/ — ListWithFilters
# ---------------------------------------------------------------------------


class TestListDocuments:
    """Tests for GET /api/v1/documents/ with filtering, sorting, pagination."""

    LIST_URL = "/api/v1/documents/"

    def test_list_default(self, client: TestClient, auth_header: dict):
        """Default list returns 200 with items, summary, meta."""
        response = client.get(self.LIST_URL, headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "summary" in data
        assert "meta" in data

    def test_list_with_source_type_filter(self, client: TestClient, auth_header: dict):
        """Filter by source_type returns 200."""
        response = client.get(self.LIST_URL, params={"source_type": "GOST"}, headers=auth_header)
        assert response.status_code == 200

    def test_list_with_era_filter(self, client: TestClient, auth_header: dict):
        """Filter by era returns 200."""
        response = client.get(self.LIST_URL, params={"era": "USSR"}, headers=auth_header)
        assert response.status_code == 200

    def test_list_with_validity_status_filter(self, client: TestClient, auth_header: dict):
        """Filter by validity_status returns 200."""
        response = client.get(self.LIST_URL, params={"validity_status": "active"}, headers=auth_header)
        assert response.status_code == 200

    def test_list_with_jurisdiction_filter(self, client: TestClient, auth_header: dict):
        """Filter by jurisdiction returns 200."""
        response = client.get(self.LIST_URL, params={"jurisdiction": "RU"}, headers=auth_header)
        assert response.status_code == 200

    def test_list_with_multiple_filters(self, client: TestClient, auth_header: dict):
        """Combination of filters returns 200."""
        response = client.get(
            self.LIST_URL,
            params={"source_type": "GOST", "era": "USSR", "validity_status": "active"},
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_list_with_mks_oks_code_filter(self, client: TestClient, auth_header: dict):
        """Filter by mks_oks_code returns 200."""
        response = client.get(self.LIST_URL, params={"mks_oks_code": "31.240"}, headers=auth_header)
        assert response.status_code == 200

    def test_list_with_okstu_code_filter(self, client: TestClient, auth_header: dict):
        """Filter by okstu_code returns 200."""
        response = client.get(self.LIST_URL, params={"okstu_code": "OKP 1234"}, headers=auth_header)
        assert response.status_code == 200

    def test_list_with_doc_code_filter(self, client: TestClient, auth_header: dict):
        """Filter by doc_code returns 200."""
        response = client.get(self.LIST_URL, params={"doc_code": "20868-81"}, headers=auth_header)
        assert response.status_code == 200

    def test_list_with_search_filter(self, client: TestClient, auth_header: dict):
        """Filter by search returns 200."""
        response = client.get(self.LIST_URL, params={"search": "стойки"}, headers=auth_header)
        assert response.status_code == 200

    def test_list_with_date_range(self, client: TestClient, auth_header: dict):
        """Filter by date range returns 200."""
        response = client.get(
            self.LIST_URL,
            params={"date_from": "2024-01-01T00:00:00", "date_to": "2026-12-31T23:59:59"},
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_list_with_sort_by_and_order(self, client: TestClient, auth_header: dict):
        """Sort by created_at/title with asc/desc order returns 200."""
        response = client.get(
            self.LIST_URL,
            params={"sort_by": "created_at", "order": "asc"},
            headers=auth_header,
        )
        assert response.status_code == 200
        response = client.get(
            self.LIST_URL,
            params={"sort_by": "title", "order": "desc"},
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_list_with_status_filter(self, client: TestClient, auth_header: dict):
        """Filter by status returns 200."""
        response = client.get(self.LIST_URL, params={"status": "approved"}, headers=auth_header)
        assert response.status_code == 200

    def test_list_with_all_filter_params(self, client: TestClient, auth_header: dict):
        """All filter params simultaneously returns 200."""
        response = client.get(
            self.LIST_URL,
            params={
                "source_type": "GOST",
                "era": "USSR",
                "validity_status": "active",
                "jurisdiction": "RU",
                "mks_oks_code": "31.240",
                "okstu_code": "OKP 1234",
                "doc_code": "20868-81",
                "search": "стойки",
                "date_from": "2024-01-01T00:00:00",
                "date_to": "2026-12-31T23:59:59",
                "sort_by": "created_at",
                "order": "desc",
                "status": "approved",
            },
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_list_with_page_size(self, client: TestClient, auth_header: dict):
        """page_size param is reflected in meta.page_size."""
        response = client.get(self.LIST_URL, params={"page_size": 50}, headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["page_size"] == 50

    def test_list_invalid_page_size(self, client: TestClient, auth_header: dict):
        """page_size > 100 returns 422."""
        response = client.get(self.LIST_URL, params={"page_size": 200}, headers=auth_header)
        assert response.status_code == 422

    def test_list_item_structure(self, client: TestClient, auth_header: dict):
        """items[0] contains all DocumentListItem fields."""
        response = client.get(self.LIST_URL, headers=auth_header)
        data = response.json()
        assert len(data["items"]) > 0
        item = data["items"][0]
        assert "document_id" in item
        assert "title" in item
        assert "doc_code" in item
        assert "source_type" in item
        assert "era" in item
        assert "validity_status" in item
        assert "jurisdiction" in item
        assert "issuing_body" in item
        assert "mks_oks_code" in item
        assert "okstu_code" in item
        assert "classification_status" in item
        assert "file_hash_sha256" in item
        assert "file_size_bytes" in item
        assert "status" in item
        assert "latest_version" in item
        assert "total_versions" in item
        assert "user_id" in item
        assert "uploaded_by" in item
        assert "created_at" in item
        assert "updated_at" in item
        assert isinstance(item["document_id"], str)
        assert isinstance(item["source_type"], str)
        assert isinstance(item["status"], str)
        assert isinstance(item["latest_version"], int)
        assert isinstance(item["total_versions"], int)

    def test_list_without_auth(self, client: TestClient):
        """List documents works without auth in mock mode."""
        response = client.get(self.LIST_URL)
        assert response.status_code == 200


# ---------------------------------------------------------------------------
#  GET /api/v1/documents/queue
# ---------------------------------------------------------------------------


class TestDocumentQueue:
    """Tests for GET /api/v1/documents/queue."""

    QUEUE_URL = "/api/v1/documents/queue"

    def test_get_queue_returns_200(self, client: TestClient, auth_header: dict):
        """Getting queue returns 200."""
        response = client.get(self.QUEUE_URL, headers=auth_header)
        assert response.status_code == 200

    def test_queue_response_structure(self, client: TestClient, auth_header: dict):
        """Response has queue and meta."""
        response = client.get(self.QUEUE_URL, headers=auth_header)
        data = response.json()
        assert "queue" in data
        assert "meta" in data
        assert isinstance(data["queue"], list)

    def test_queue_item_structure(self, client: TestClient, auth_header: dict):
        """Each queue item has document_id, title, status, progress_percent etc."""
        response = client.get(self.QUEUE_URL, headers=auth_header)
        data = response.json()
        if data["queue"]:
            item = data["queue"][0]
            assert "document_id" in item
            assert "title" in item
            assert "doc_code" in item
            assert "source_type" in item
            assert "status" in item
            assert "progress_percent" in item
            assert "current_step" in item
            assert "steps" in item
            assert "user_id" in item
            assert "uploaded_by" in item
            assert "created_at" in item

            assert isinstance(item["document_id"], str)
            assert isinstance(item["status"], str)
            assert isinstance(item["progress_percent"], float)
            assert isinstance(item["user_id"], str)

    def test_queue_meta_structure(self, client: TestClient, auth_header: dict):
        """Meta contains total_in_queue, page, page_size."""
        response = client.get(self.QUEUE_URL, headers=auth_header)
        data = response.json()
        meta = data["meta"]
        assert "total_in_queue" in meta
        assert "page" in meta
        assert "page_size" in meta
        assert isinstance(meta["total_in_queue"], int)
        assert isinstance(meta["page"], int)
        assert isinstance(meta["page_size"], int)

    def test_queue_with_pagination(self, client: TestClient, auth_header: dict):
        """Queue with page and page_size params returns 200."""
        response = client.get(
            self.QUEUE_URL,
            params={"page": 1, "page_size": 10},
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["page"] == 1
        assert data["meta"]["page_size"] == 10

    def test_queue_without_auth(self, client: TestClient):
        """Queue works without auth in mock mode."""
        response = client.get(self.QUEUE_URL)
        assert response.status_code == 200


# ---------------------------------------------------------------------------
#  GET /api/v1/documents/{doc_id}
# ---------------------------------------------------------------------------


class TestGetDocument:
    """Tests for GET /api/v1/documents/{doc_id}."""

    DOC_URL = "/api/v1/documents/{doc_id}"

    def test_get_document_returns_200(self, client: TestClient, auth_header: dict):
        """Get document returns 200."""
        response = client.get(self.DOC_URL.format(doc_id="doc-test-001"), headers=auth_header)
        assert response.status_code == 200

    def test_get_document_response_structure(self, client: TestClient, auth_header: dict):
        """Response has all expected DocumentDetailResponse fields."""
        response = client.get(self.DOC_URL.format(doc_id="doc-test-001"), headers=auth_header)
        data = response.json()
        assert "document_id" in data
        assert "title" in data
        assert "doc_code" in data
        assert "source_type" in data
        assert "status" in data
        assert "era" in data
        assert "validity_status" in data
        assert "jurisdiction" in data
        assert "issuing_body" in data
        assert "mks_oks_code" in data
        assert "okstu_code" in data
        assert "classification_status" in data
        assert "metadata" in data
        assert "latest_version" in data
        assert "total_versions" in data
        assert "user_id" in data
        assert "uploaded_by" in data
        assert "created_at" in data
        assert "updated_at" in data

        assert data["document_id"] == "doc-test-001"
        assert isinstance(data["source_type"], str)
        assert isinstance(data["status"], str)
        assert isinstance(data["total_versions"], int)

    def test_get_document_latest_version(self, client: TestClient, auth_header: dict):
        """latest_version contains version_id, version_number etc."""
        response = client.get(self.DOC_URL.format(doc_id="doc-test-001"), headers=auth_header)
        data = response.json()
        lv = data.get("latest_version")
        if lv is not None:
            assert "version_id" in lv
            assert "version_number" in lv
            assert "format_code" in lv
            assert "file_hash_sha256" in lv
            assert "size_bytes" in lv
            assert isinstance(lv["version_number"], int)
            assert isinstance(lv["version_id"], str)

    def test_get_document_without_auth(self, client: TestClient):
        """Get document works without auth in mock mode."""
        response = client.get(self.DOC_URL.format(doc_id="doc-test-001"))
        assert response.status_code == 200


# ---------------------------------------------------------------------------
#  GET /api/v1/documents/{doc_id}/status
# ---------------------------------------------------------------------------


class TestDocumentStatus:
    """Tests for GET /api/v1/documents/{doc_id}/status."""

    STATUS_URL = "/api/v1/documents/{doc_id}/status"

    def test_get_status_returns_200(self, client: TestClient, auth_header: dict):
        """Get status returns 200."""
        response = client.get(self.STATUS_URL.format(doc_id="doc-test-001"), headers=auth_header)
        assert response.status_code == 200

    def test_get_status_response_structure(self, client: TestClient, auth_header: dict):
        """Response has document_id, status, progress_percent, steps."""
        response = client.get(self.STATUS_URL.format(doc_id="doc-test-001"), headers=auth_header)
        data = response.json()
        assert "document_id" in data
        assert "status" in data
        assert "progress_percent" in data
        assert "steps" in data
        assert data["document_id"] == "doc-test-001"
        assert isinstance(data["status"], str)
        assert isinstance(data["progress_percent"], float)

    def test_get_status_pipeline_structure(self, client: TestClient, auth_header: dict):
        """steps.pipeline contains formation and indexation."""
        response = client.get(self.STATUS_URL.format(doc_id="doc-test-001"), headers=auth_header)
        data = response.json()
        pipeline = data["steps"]["pipeline"]
        assert "formation" in pipeline
        assert "indexation" in pipeline
        assert "status" in pipeline["formation"]
        assert "status" in pipeline["indexation"]

    def test_get_status_with_longpoll(self, client: TestClient, auth_header: dict):
        """Status with longpoll param returns 200."""
        response = client.get(
            self.STATUS_URL.format(doc_id="doc-test-001"),
            params={"longpoll": 0},
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_get_status_invalid_longpoll(self, client: TestClient, auth_header: dict):
        """Status with longpoll < 0 returns 422."""
        response = client.get(
            self.STATUS_URL.format(doc_id="doc-test-001"),
            params={"longpoll": -1},
            headers=auth_header,
        )
        assert response.status_code == 422

    def test_get_status_without_auth(self, client: TestClient):
        """Status works without auth in mock mode."""
        response = client.get(self.STATUS_URL.format(doc_id="doc-test-001"))
        assert response.status_code == 200


# ---------------------------------------------------------------------------
#  GET /api/v1/documents/{doc_id}/file
# ---------------------------------------------------------------------------


class TestDocumentFile:
    """Tests for GET /api/v1/documents/{doc_id}/file."""

    FILE_URL = "/api/v1/documents/{doc_id}/file"

    def test_get_file_returns_200(self, client: TestClient, auth_header: dict):
        """Get file info returns 200."""
        response = client.get(self.FILE_URL.format(doc_id="doc-test-001"), headers=auth_header)
        assert response.status_code == 200

    def test_get_file_response_structure(self, client: TestClient, auth_header: dict):
        """Response has document_id, version_id, content_type, file_url."""
        response = client.get(self.FILE_URL.format(doc_id="doc-test-001"), headers=auth_header)
        data = response.json()
        assert "document_id" in data
        assert "version_id" in data
        assert "content_type" in data
        assert "file_url" in data
        assert data["document_id"] == "doc-test-001"
        assert isinstance(data["version_id"], str)
        assert isinstance(data["content_type"], str)
        assert isinstance(data["file_url"], str)

    def test_get_file_content_type(self, client: TestClient, auth_header: dict):
        """content_type is application/pdf."""
        response = client.get(self.FILE_URL.format(doc_id="doc-test-001"), headers=auth_header)
        data = response.json()
        assert data["content_type"] == "application/pdf"

    def test_get_file_without_auth(self, client: TestClient):
        """File info works without auth in mock mode."""
        response = client.get(self.FILE_URL.format(doc_id="doc-test-001"))
        assert response.status_code == 200


# ---------------------------------------------------------------------------
#  GET /api/v1/documents/{doc_id}/pages
# ---------------------------------------------------------------------------


class TestDocumentPages:
    """Tests for GET /api/v1/documents/{doc_id}/pages."""

    PAGES_URL = "/api/v1/documents/{doc_id}/pages"

    def test_list_pages_returns_200(self, client: TestClient, auth_header: dict):
        """List pages returns 200."""
        response = client.get(self.PAGES_URL.format(doc_id="doc-test-001"), headers=auth_header)
        assert response.status_code == 200

    def test_list_pages_response_structure(self, client: TestClient, auth_header: dict):
        """Response has document_id, pages_total, pages, meta."""
        response = client.get(self.PAGES_URL.format(doc_id="doc-test-001"), headers=auth_header)
        data = response.json()
        assert "document_id" in data
        assert "pages_total" in data
        assert "pages" in data
        assert "meta" in data
        assert data["document_id"] == "doc-test-001"
        assert isinstance(data["pages_total"], int)
        assert isinstance(data["pages"], list)
        assert "total" in data["meta"]

    def test_list_pages_item_structure(self, client: TestClient, auth_header: dict):
        """Each page item has page, width, height, ocr_status, confidence, has_text_layer."""
        response = client.get(self.PAGES_URL.format(doc_id="doc-test-001"), headers=auth_header)
        data = response.json()
        if data["pages"]:
            page = data["pages"][0]
            assert "page" in page
            assert "width" in page
            assert "height" in page
            assert "ocr_status" in page
            assert "confidence" in page
            assert "has_text_layer" in page
            assert isinstance(page["page"], int)
            assert isinstance(page["width"], int)
            assert isinstance(page["height"], int)
            assert isinstance(page["ocr_status"], str)
            assert isinstance(page["confidence"], float)
            assert isinstance(page["has_text_layer"], bool)

    def test_list_pages_without_auth(self, client: TestClient):
        """List pages works without auth in mock mode."""
        response = client.get(self.PAGES_URL.format(doc_id="doc-test-001"))
        assert response.status_code == 200


# ---------------------------------------------------------------------------
#  GET /api/v1/documents/{doc_id}/pages/{page_num}
# ---------------------------------------------------------------------------


class TestDocumentPageView:
    """Tests for GET /api/v1/documents/{doc_id}/pages/{page_num}."""

    PAGE_VIEW_URL = "/api/v1/documents/{doc_id}/pages/{page_num}"

    def test_page_view_returns_200(self, client: TestClient, auth_header: dict):
        """Page view returns 200."""
        response = client.get(
            self.PAGE_VIEW_URL.format(doc_id="doc-test-001", page_num=1),
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_page_view_response_structure(self, client: TestClient, auth_header: dict):
        """Response has document_id, page, image_url, width, height, blocks."""
        response = client.get(
            self.PAGE_VIEW_URL.format(doc_id="doc-test-001", page_num=1),
            headers=auth_header,
        )
        data = response.json()
        assert "document_id" in data
        assert "page" in data
        assert "image_url" in data
        assert "width" in data
        assert "height" in data
        assert "blocks" in data
        assert data["document_id"] == "doc-test-001"
        assert data["page"] == 1
        assert isinstance(data["image_url"], str)
        assert isinstance(data["width"], int)
        assert isinstance(data["height"], int)
        assert isinstance(data["blocks"], list)

    def test_page_view_without_auth(self, client: TestClient):
        """Page view works without auth in mock mode."""
        response = client.get(
            self.PAGE_VIEW_URL.format(doc_id="doc-test-001", page_num=1),
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
#  GET /api/v1/documents/{doc_id}/pages/{page_num}/text
# ---------------------------------------------------------------------------


class TestDocumentPageText:
    """Tests for GET /api/v1/documents/{doc_id}/pages/{page_num}/text."""

    PAGE_TEXT_URL = "/api/v1/documents/{doc_id}/pages/{page_num}/text"

    def test_page_text_returns_200(self, client: TestClient, auth_header: dict):
        """Page text returns 200."""
        response = client.get(
            self.PAGE_TEXT_URL.format(doc_id="doc-test-001", page_num=1),
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_page_text_response_structure(self, client: TestClient, auth_header: dict):
        """Response has document_id, page, width, height, blocks."""
        response = client.get(
            self.PAGE_TEXT_URL.format(doc_id="doc-test-001", page_num=1),
            headers=auth_header,
        )
        data = response.json()
        assert "document_id" in data
        assert "page" in data
        assert "width" in data
        assert "height" in data
        assert "blocks" in data
        assert data["document_id"] == "doc-test-001"
        assert data["page"] == 1
        assert isinstance(data["width"], int)
        assert isinstance(data["height"], int)
        assert isinstance(data["blocks"], list)

    def test_page_text_block_structure(self, client: TestClient, auth_header: dict):
        """Each block has number, type, bbox, content, confidence."""
        response = client.get(
            self.PAGE_TEXT_URL.format(doc_id="doc-test-001", page_num=1),
            headers=auth_header,
        )
        data = response.json()
        if data["blocks"]:
            block = data["blocks"][0]
            assert "number" in block
            assert "type" in block
            assert "bbox" in block
            assert "content" in block
            assert "confidence" in block
            assert isinstance(block["number"], int)
            assert isinstance(block["type"], str)
            assert isinstance(block["bbox"], list)
            assert isinstance(block["confidence"], (float, int))

    def test_page_text_bbox_range(self, client: TestClient, auth_header: dict):
        """Bbox coordinates are in [0, 1] range."""
        response = client.get(
            self.PAGE_TEXT_URL.format(doc_id="doc-test-001", page_num=1),
            headers=auth_header,
        )
        data = response.json()
        for block in data["blocks"]:
            for coord in block["bbox"]:
                assert 0.0 <= coord <= 1.0, f"bbox coord {coord} out of [0,1] range"

    def test_page_text_without_auth(self, client: TestClient):
        """Page text works without auth in mock mode."""
        response = client.get(
            self.PAGE_TEXT_URL.format(doc_id="doc-test-001", page_num=1),
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
#  GET /api/v1/documents/{doc_id}/pages/{page_num}/preview
# ---------------------------------------------------------------------------


class TestDocumentPagePreview:
    """Tests for GET /api/v1/documents/{doc_id}/pages/{page_num}/preview."""

    PREVIEW_URL = "/api/v1/documents/{doc_id}/pages/{page_num}/preview"

    def test_page_preview_returns_200(self, client: TestClient, auth_header: dict):
        """Page preview returns 200."""
        response = client.get(
            self.PREVIEW_URL.format(doc_id="doc-test-001", page_num=1),
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_page_preview_response_structure(self, client: TestClient, auth_header: dict):
        """Response has document_id, page, image_url, blocks, text_layer."""
        response = client.get(
            self.PREVIEW_URL.format(doc_id="doc-test-001", page_num=1),
            headers=auth_header,
        )
        data = response.json()
        assert "document_id" in data
        assert "page" in data
        assert "image_url" in data
        assert "blocks" in data
        assert "text_layer" in data
        assert data["document_id"] == "doc-test-001"
        assert data["page"] == 1
        assert isinstance(data["image_url"], str)
        assert isinstance(data["blocks"], list)

    def test_page_preview_without_auth(self, client: TestClient):
        """Page preview works without auth in mock mode."""
        response = client.get(
            self.PREVIEW_URL.format(doc_id="doc-test-001", page_num=1),
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
#  GET /api/v1/documents/{doc_id}/errors
# ---------------------------------------------------------------------------


class TestDocumentErrors:
    """Tests for GET /api/v1/documents/{doc_id}/errors."""

    ERRORS_URL = "/api/v1/documents/{doc_id}/errors"

    def test_get_errors_returns_200(self, client: TestClient, auth_header: dict):
        """Get errors returns 200."""
        response = client.get(self.ERRORS_URL.format(doc_id="doc-test-001"), headers=auth_header)
        assert response.status_code == 200

    def test_get_errors_response_structure(self, client: TestClient, auth_header: dict):
        """Response has errors and meta."""
        response = client.get(self.ERRORS_URL.format(doc_id="doc-test-001"), headers=auth_header)
        data = response.json()
        assert "errors" in data
        assert "meta" in data
        assert isinstance(data["errors"], list)
        assert "total" in data["meta"]

    def test_get_errors_filter_by_stage(self, client: TestClient, auth_header: dict):
        """Filter errors by stage returns 200."""
        response = client.get(
            self.ERRORS_URL.format(doc_id="doc-test-001"),
            params={"stage": "ocr"},
            headers=auth_header,
        )
        assert response.status_code == 200

    def test_get_errors_item_structure(self, client: TestClient, auth_header: dict):
        """Each error item has error_id, stage, error_code, error_message etc."""
        response = client.get(self.ERRORS_URL.format(doc_id="doc-test-001"), headers=auth_header)
        data = response.json()
        if data["errors"]:
            err = data["errors"][0]
            assert "error_id" in err
            assert "stage" in err
            assert "error_code" in err
            assert "error_message" in err
            assert "severity" in err
            assert "retry_attempt" in err
            assert "timestamp" in err
            assert isinstance(err["error_id"], str)
            assert isinstance(err["stage"], str)
            assert isinstance(err["error_code"], str)
            assert isinstance(err["error_message"], str)
            assert isinstance(err["severity"], str)
            assert isinstance(err["retry_attempt"], int)

    def test_get_errors_without_auth(self, client: TestClient):
        """Errors works without auth in mock mode."""
        response = client.get(self.ERRORS_URL.format(doc_id="doc-test-001"))
        assert response.status_code == 200


# ---------------------------------------------------------------------------
#  GET /api/v1/documents/{doc_id}/parameters
# ---------------------------------------------------------------------------


class TestDocumentParameters:
    """Tests for GET /api/v1/documents/{doc_id}/parameters."""

    PARAMS_URL = "/api/v1/documents/{doc_id}/parameters"

    def test_get_parameters_returns_200(self, client: TestClient, auth_header: dict):
        """Get parameters returns 200."""
        response = client.get(self.PARAMS_URL.format(doc_id="doc-test-001"), headers=auth_header)
        assert response.status_code == 200

    def test_get_parameters_response_structure(self, client: TestClient, auth_header: dict):
        """Response has document_id, parameters, total."""
        response = client.get(self.PARAMS_URL.format(doc_id="doc-test-001"), headers=auth_header)
        data = response.json()
        assert "document_id" in data
        assert "parameters" in data
        assert "total" in data
        assert data["document_id"] == "doc-test-001"
        assert isinstance(data["parameters"], list)
        assert isinstance(data["total"], int)

    def test_get_parameters_item_structure(self, client: TestClient, auth_header: dict):
        """Each parameter has symbol, description, unit, value, source_clause, source_page."""
        response = client.get(self.PARAMS_URL.format(doc_id="doc-test-001"), headers=auth_header)
        data = response.json()
        if data["parameters"]:
            param = data["parameters"][0]
            assert "symbol" in param
            assert "description" in param
            assert "unit" in param
            assert "value" in param
            assert "source_clause" in param
            assert "source_page" in param
            assert isinstance(param["symbol"], str)
            assert isinstance(param["description"], str)

    def test_get_parameters_with_range(self, client: TestClient, auth_header: dict):
        """Parameter with range has min/max fields."""
        response = client.get(self.PARAMS_URL.format(doc_id="doc-test-001"), headers=auth_header)
        data = response.json()
        range_params = [p for p in data["parameters"] if "range" in p and p["range"] is not None]
        if range_params:
            r = range_params[0]["range"]
            assert "min" in r
            assert "max" in r

    def test_get_parameters_without_auth(self, client: TestClient):
        """Parameters works without auth in mock mode."""
        response = client.get(self.PARAMS_URL.format(doc_id="doc-test-001"))
        assert response.status_code == 200


# ---------------------------------------------------------------------------
#  POST /api/v1/documents/{doc_id}/reprocess
# ---------------------------------------------------------------------------


class TestDocumentReprocess:
    """Tests for POST /api/v1/documents/{doc_id}/reprocess."""

    REPROCESS_URL = "/api/v1/documents/{doc_id}/reprocess"

    def test_reprocess_full_mode(self, client: TestClient, auth_header: dict):
        """Reprocess with mode=full returns 202."""
        response = client.post(
            self.REPROCESS_URL.format(doc_id="doc-test-001"),
            json={"mode": "full"},
            headers=auth_header,
        )
        assert response.status_code == 202

    def test_reprocess_ocr_only(self, client: TestClient, auth_header: dict):
        """Reprocess with mode=ocr_only returns 202."""
        response = client.post(
            self.REPROCESS_URL.format(doc_id="doc-test-001"),
            json={"mode": "ocr_only"},
            headers=auth_header,
        )
        assert response.status_code == 202

    def test_reprocess_invalid_mode(self, client: TestClient, auth_header: dict):
        """Reprocess with invalid mode returns 422."""
        response = client.post(
            self.REPROCESS_URL.format(doc_id="doc-test-001"),
            json={"mode": "invalid"},
            headers=auth_header,
        )
        assert response.status_code == 422

    def test_reprocess_response_structure(self, client: TestClient, auth_header: dict):
        """Response has mode, document_id, user_id, task_id, status, created_at."""
        response = client.post(
            self.REPROCESS_URL.format(doc_id="doc-test-001"),
            json={"mode": "full"},
            headers=auth_header,
        )
        data = response.json()
        assert "mode" in data
        assert "document_id" in data
        assert "user_id" in data
        assert "task_id" in data
        assert "status" in data
        assert "created_at" in data
        assert data["document_id"] == "doc-test-001"
        assert data["mode"] == "full"
        assert isinstance(data["user_id"], str)
        assert isinstance(data["task_id"], str)
        assert isinstance(data["status"], str)

    def test_reprocess_without_auth(self, client: TestClient):
        """Reprocess works without auth in mock mode."""
        response = client.post(
            self.REPROCESS_URL.format(doc_id="doc-test-001"),
            json={"mode": "full"},
        )
        assert response.status_code == 202
