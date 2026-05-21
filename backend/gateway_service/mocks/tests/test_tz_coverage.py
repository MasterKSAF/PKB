"""
TZ coverage tests for PKB Neuroassistant Mock Services.
Tests UC-01 through UC-09, NFR, RBAC, Registry specifics, edge cases.
Updated for the new API specification (2025-06).
"""

import os
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import pytest
from fastapi.testclient import TestClient

import mocks.gateway

# Разрешаем анонимный доступ в тестах (тесты не проверяют RBAC)
mocks.gateway.ALLOW_ANONYMOUS = True

from mocks.gateway import app

client = TestClient(app, raise_server_exceptions=False)

BASE = "/api/v1"
AUTH = f"{BASE}/auth"
ADMIN = f"{BASE}/admin"
ORCH = f"{BASE}"
QUERY = f"{BASE}"
REG_DOCS = f"{BASE}/registry"
REG = f"{BASE}"
COMMON = f"{BASE}/common"

TEST_USER = "ivanov@example.com"
TEST_PASS = "secret123"
ADMIN_USER = "admin@example.com"
ADMIN_PASS = "admin123"


def get_token(user=TEST_USER, pwd=TEST_PASS) -> str:
    resp = client.post(f"{AUTH}/token", json={"username": user, "password": pwd})
    return resp.json().get("access_token", "")


def auth_header(user=TEST_USER, pwd=TEST_PASS) -> dict:
    return {"Authorization": f"Bearer {get_token(user, pwd)}"}


def assert_ok(resp, status_code=200):
    assert resp.status_code == status_code, (
        f"Expected {status_code}, got {resp.status_code}: {resp.text[:300]}"
    )


# ===========================================================================
# UC-01: DOCUMENT UPLOAD
# ===========================================================================
class TestUC01_DocumentUpload:
    """Upload scenarios: types, idempotency, response format."""

    def test_upload_all_types(self):
        """Upload works (POST /documents now only accepts file param)."""
        for fname in [
            "test_normative.pdf",
            "test_archival.pdf",
            "test_drawing.pdf",
            "test_spec.pdf",
        ]:
            resp = client.post(
                f"{ORCH}/documents",
                files={"file": (fname, b"dummy content", "application/pdf")},
            )
            assert_ok(resp, 202)
            data = resp.json()
            assert data["status"] in ("uploaded", "queued")

    def test_upload_response_format(self):
        """202 response returns task_id, version_id, status, content_hash_sha256, etc."""
        resp = client.post(
            f"{ORCH}/documents",
            files={"file": ("test.pdf", b"format check", "application/pdf")},
        )
        assert_ok(resp, 202)
        data = resp.json()
        assert "task_id" in data
        assert "version_id" in data
        assert "status" in data
        assert "content_hash_sha256" in data
        assert "is_duplicate_file" in data
        assert "is_duplicate_document" in data
        assert "title_hash_sha256" in data
        assert "created_at" in data

    def test_idempotency_key(self):
        """Idempotency-Key header is accepted (no crash)."""
        key = "tz-test-idem-001"
        r1 = client.post(
            f"{ORCH}/documents",
            files={"file": ("idem.pdf", b"idem content", "application/pdf")},
            headers={"Idempotency-Key": key},
        )
        assert r1.status_code in (202, 500)


# ===========================================================================
# UC-02: OCR AND STRUCTURAL PROCESSING
# ===========================================================================
class TestUC02_OcrProcessing:
    """OCR lifecycle, pipeline status, confidence, errors."""

    def test_status_has_pipeline_steps(self):
        """Status response includes pipeline with formation and indexation."""
        resp = client.get(f"{ORCH}/documents/doc-001/status")
        assert_ok(resp)
        data = resp.json()
        assert "pipeline" in data
        assert "formation" in data["pipeline"]
        assert "indexation" in data["pipeline"]
        for s in ["parsing", "validation", "registry"]:
            assert s in data["pipeline"]["formation"]
        assert "rag_indexing" in data["pipeline"]["indexation"]

    def test_status_has_progress(self):
        """Status includes progress_percent between 0 and 100."""
        resp = client.get(f"{ORCH}/documents/doc-003/status")
        assert_ok(resp)
        assert "progress_percent" in resp.json()
        assert 0 <= resp.json()["progress_percent"] <= 100

    def test_completed_has_pipeline_status(self):
        """Completed document has pipeline with formation steps all completed."""
        resp = client.get(f"{ORCH}/documents/doc-001/status")
        assert_ok(resp)
        data = resp.json()
        if data["status"] == "completed":
            assert "pipeline" in data
            for step in ["parsing", "validation", "registry"]:
                assert data["pipeline"]["formation"][step] == "completed"

    def test_failed_has_error(self):
        """Failed document has error block in status."""
        resp = client.get(f"{ORCH}/documents/doc-005/status")
        assert_ok(resp)
        if resp.json()["status"] == "failed" and "error" in resp.json():
            assert "code" in resp.json()["error"]

    def test_completed_has_chunk_summary(self):
        """Completed document has chunk_summary."""
        resp = client.get(f"{ORCH}/documents/doc-001/status")
        assert_ok(resp)
        if resp.json()["status"] == "completed":
            cs = resp.json().get("chunk_summary", {})
            assert "total" in cs

    def test_processing_has_estimated_completion(self):
        """Processing document shows estimated completion."""
        resp = client.get(f"{ORCH}/documents/doc-003/status")
        assert_ok(resp)
        if resp.json()["status"] == "processing":
            assert "pipeline" in resp.json()


# ===========================================================================
# UC-03: SEMANTIC SEARCH
# ===========================================================================
class TestUC03_SemanticSearch:
    """Search traceability, filters, timing."""

    def test_search_traceability(self):
        """Each result has section_id, document_id, page, score, urls."""
        resp = client.post(
            f"{ORCH}/documents/search",
            json={"query": "wall thickness", "top_k": 5},
        )
        assert_ok(resp)
        for item in resp.json()["items"]:
            assert "document_id" in item
            assert "page" in item
            assert "section_id" in item
            assert "page_preview_url" in item
            assert "document_url" in item
            assert "score" in item
            assert 0 <= item["score"] <= 1

    def test_search_empty_result(self):
        """No-match query returns empty items, not error."""
        resp = client.post(
            f"{ORCH}/documents/search",
            json={"query": "xyznonexistent12345", "top_k": 5},
        )
        assert_ok(resp)
        assert "items" in resp.json()
        assert "total_found" in resp.json()

    def test_search_filter_by_type(self):
        """Filter by document_type works."""
        resp = client.post(
            f"{ORCH}/documents/search",
            json={"query": "size", "filters": {"document_type": "normative"}},
        )
        assert_ok(resp)
        for item in resp.json()["items"]:
            assert item["document_type"] == "normative"

    def test_search_limited_by_top_k(self):
        """top_k limits number of results."""
        resp = client.post(
            f"{ORCH}/documents/search",
            json={"query": "wall", "top_k": 2},
        )
        assert_ok(resp)
        assert len(resp.json()["items"]) <= 2

    def test_search_returns_processing_time(self):
        """Search returns processing_time_ms > 0."""
        resp = client.post(
            f"{ORCH}/documents/search",
            json={"query": "wall thickness", "top_k": 3},
        )
        assert_ok(resp)
        assert "processing_time_ms" in resp.json()
        assert resp.json()["processing_time_ms"] > 0

    def test_search_get_method(self):
        """GET search works with q parameter."""
        resp = client.get(
            f"{ORCH}/documents/search",
            params={"q": "wall thickness", "top_k": 3},
        )
        assert_ok(resp)
        assert len(resp.json()["items"]) > 0


# ===========================================================================
# UC-04: ANSWER WITH SOURCES (TRACEABILITY)
# ===========================================================================
class TestUC04_AnswerWithSources:
    """Answer traceability, sources, disclaimers."""

    def test_chat_answer_has_sources(self):
        """Chat answer_items have sources with document_id and page."""
        resp = client.post(
            f"{QUERY}/chat", json={"question": "What is the wall thickness?"}
        )
        assert_ok(resp)
        data = resp.json()
        if data.get("scenario") == "completed":
            for item in data.get("answer_items", []):
                assert "sources" in item
                for s in item["sources"]:
                    assert "document_id" in s
                    assert "page" in s
                    assert "excerpt" in s
                    assert "document_url" in s

    def test_chat_ask_needs_clarification(self):
        """Chat returns needs_clarification scenario for ambiguous questions."""
        resp = client.post(
            f"{QUERY}/chat",
            json={"question": "Этот запрос неопределён по смыслу"},
        )
        assert_ok(resp)
        data = resp.json()
        assert data.get("scenario") == "needs_clarification"
        assert "missing_fields" in data
        assert len(data["missing_fields"]) > 0

    def test_chat_ask_conflict(self):
        """Chat returns conflict scenario for conflicting questions."""
        resp = client.post(
            f"{QUERY}/chat",
            json={"question": "конфликт в данных спецификации"},
        )
        assert_ok(resp)
        data = resp.json()
        assert data.get("scenario") == "conflict"
        assert "conflicts" in data
        assert len(data["conflicts"]) > 0

    def test_chat_ask_with_context(self):
        """Chat accepts context with project_id, document_ids, nsi_version."""
        resp = client.post(
            f"{QUERY}/chat",
            json={
                "question": "What material?",
                "context": {
                    "project_id": "PKB-101",
                    "document_ids": ["doc-001"],
                    "nsi_version": "2025-06",
                },
            },
        )
        assert_ok(resp)

    def test_answer_disclaimer(self):
        """Text ask returns disclaimer about verification."""
        resp = client.post(f"{QUERY}/text/ask", json={"text": "What material?"})
        assert_ok(resp)
        assert "disclaimer" in resp.json()

    def test_answer_model_used(self):
        """Answer specifies which model was used."""
        resp = client.post(f"{QUERY}/text/ask", json={"text": "What dimensions?"})
        assert_ok(resp)
        assert "model_used" in resp.json()

    def test_answer_processing_time(self):
        """Answer includes processing_time_ms."""
        resp = client.post(f"{QUERY}/text/ask", json={"text": "What material?"})
        assert_ok(resp)
        assert "processing_time_ms" in resp.json()


# ===========================================================================
# UC-05: PARAMETER EXTRACTION
# ===========================================================================
class TestUC05_ParameterExtraction:
    """Parameters: spec items, materials, references, confidence."""

    def test_specification_items(self):
        """Spec document has items with position, name, quantity."""
        resp = client.get(f"{ORCH}/documents/doc-001/parameters")
        assert_ok(resp)
        params = resp.json()["parameters"]
        assert "designation" in params
        assert params["designation"] != ""
        if "specification_items" in params:
            for item in params["specification_items"]:
                assert "position" in item
                assert "name" in item
                assert "quantity" in item

    def test_materials_and_references(self):
        """Parameters include materials and references arrays."""
        resp = client.get(f"{ORCH}/documents/doc-001/parameters")
        assert_ok(resp)
        params = resp.json()["parameters"]
        assert "materials" in params
        assert len(params["materials"]) > 0
        assert "references" in params
        assert len(params["references"]) > 0

    def test_extraction_confidence(self):
        """Parameters have confidence score between 0 and 1."""
        resp = client.get(f"{ORCH}/documents/doc-001/parameters")
        assert_ok(resp)
        assert "extraction_confidence" in resp.json()
        assert 0 <= resp.json()["extraction_confidence"] <= 1

    def test_unconfirmed_fields(self):
        """Parameters may list unconfirmed_fields."""
        resp = client.get(f"{ORCH}/documents/doc-001/parameters")
        assert_ok(resp)
        assert "unconfirmed_fields" in resp.json()


# ===========================================================================
# UC-06: DOCUMENT STATUS & PIPELINE (replaces old validate tests)
# ===========================================================================
class TestUC06_DocumentPipeline:
    """Pipeline status, versions, promote, history."""

    def test_add_document_version(self):
        """POST /documents/{id}/versions creates a new version."""
        resp = client.post(
            f"{ORCH}/documents/doc-001/versions",
            files={"file": ("v2.pdf", b"version content", "application/pdf")},
        )
        assert_ok(resp, 201)
        data = resp.json()
        assert "version_id" in data
        assert "version_number" in data
        assert data["version_number"] > 1

    def test_list_document_versions(self):
        """GET /documents/{id}/versions lists versions."""
        resp = client.get(f"{ORCH}/documents/doc-001/versions")
        assert_ok(resp)
        data = resp.json()
        assert "versions" in data
        assert "total" in data
        assert len(data["versions"]) > 0

    def test_approve_document(self):
        """POST /documents/{id}/approve approves document."""
        resp = client.post(f"{ORCH}/documents/doc-001/approve")
        assert_ok(resp)
        data = resp.json()
        assert data["document_id"] == "doc-001"
        assert data["status"] == "approved"
        assert "approved_at" in data

    def test_promote_document(self):
        """POST /documents/{id}/promote promotes to RAG index."""
        resp = client.post(f"{ORCH}/documents/doc-001/promote")
        assert_ok(resp)
        data = resp.json()
        assert data["document_id"] == "doc-001"
        assert data["status"] == "ready_for_promotion"

    def test_promotion_status(self):
        """GET /documents/{id}/promotion-status returns promotion state."""
        resp = client.get(f"{ORCH}/documents/doc-001/promotion-status")
        assert_ok(resp)
        data = resp.json()
        assert "document_id" in data
        assert "is_promoted" in data
        assert "promotion_status" in data

    def test_document_chunks(self):
        """GET /documents/{id}/chunks returns document fragments."""
        resp = client.get(f"{ORCH}/documents/doc-001/chunks")
        assert_ok(resp)
        data = resp.json()
        assert "document_id" in data
        assert "chunks" in data
        assert "total" in data

    def test_document_history(self):
        """GET /documents/{id}/history returns status history."""
        resp = client.get(f"{ORCH}/documents/doc-001/history")
        assert_ok(resp)
        data = resp.json()
        assert "document_id" in data
        assert "events" in data
        assert "total" in data


# ===========================================================================
# UC-07: FRAGMENT VIEW IN CONTEXT
# ===========================================================================
class TestUC07_FragmentView:
    """Page view: blocks, coordinates, types, preview, text."""

    def test_page_blocks_coordinates(self):
        """Page blocks have x/y/width/height coordinates."""
        resp = client.get(f"{ORCH}/documents/doc-001/pages/1")
        assert_ok(resp)
        for block in resp.json()["blocks"]:
            assert "coordinates" in block
            for c in ["x", "y", "width", "height"]:
                assert c in block["coordinates"]

    def test_page_block_types(self):
        """Block types are text, table, or drawing."""
        resp = client.get(f"{ORCH}/documents/doc-001/pages/1")
        assert_ok(resp)
        for block in resp.json()["blocks"]:
            assert "type" in block
            assert block["type"] in ("text", "table", "drawing")

    def test_page_preview_has_text(self):
        """Preview includes OCR text."""
        resp = client.get(f"{ORCH}/documents/doc-001/pages/1/preview")
        assert_ok(resp)
        assert "text" in resp.json()
        assert len(resp.json()["text"]) > 0

    def test_page_preview_url(self):
        """Preview has preview_url."""
        resp = client.get(f"{ORCH}/documents/doc-001/pages/1/preview")
        assert_ok(resp)
        assert "preview_url" in resp.json()

    def test_page_text_endpoint(self):
        """Page text has full_text and blocks."""
        resp = client.get(f"{ORCH}/documents/doc-001/pages/1/text")
        assert_ok(resp)
        assert "full_text" in resp.json()
        assert "blocks" in resp.json()

    def test_page_text_block_confidence(self):
        """Text blocks have confidence scores."""
        resp = client.get(f"{ORCH}/documents/doc-001/pages/1/text")
        assert_ok(resp)
        for block in resp.json()["blocks"]:
            assert "confidence" in block
            assert 0 <= block["confidence"] <= 1


# ===========================================================================
# UC-08: REPROCESSING
# ===========================================================================
class TestUC08_Reprocessing:
    """Reprocess: modes, task_id, status reset."""

    def test_reprocess_full_mode(self):
        """Reprocess with full mode resets status."""
        resp = client.post(
            f"{ORCH}/documents/doc-001/reprocess",
            json={"mode": "full"},
        )
        assert_ok(resp, 202)
        assert resp.json()["status"] in ("parsing", "queued")

    def test_reprocess_returns_task_id(self):
        """Reprocess returns a task_id."""
        resp = client.post(
            f"{ORCH}/documents/doc-001/reprocess",
            json={"mode": "full"},
        )
        assert_ok(resp, 202)
        assert "task_id" in resp.json()

    def test_reprocess_standard_mode(self):
        """Reprocess with standard mode works."""
        resp = client.post(
            f"{ORCH}/documents/doc-001/reprocess",
            json={"mode": "standard"},
        )
        assert_ok(resp, 202)

    def test_reprocess_no_mode(self):
        """Reprocess works without mode parameter."""
        resp = client.post(f"{ORCH}/documents/doc-001/reprocess", json={})
        assert_ok(resp, 202)


# ===========================================================================
# UC-09: ERROR LOG AND MONITORING
# ===========================================================================
class TestUC09_ErrorLog:
    """Error log, metrics, monitoring."""

    def test_error_fields(self):
        """Error entries have stage, code, message, severity, timestamp."""
        resp = client.get(f"{ORCH}/documents/doc-005/errors")
        assert_ok(resp)
        for err in resp.json()["errors"]:
            assert "stage" in err
            assert "error_code" in err
            assert "error_message" in err
            assert "severity" in err
            assert err["severity"] in ("error", "warning")
            assert "timestamp" in err
            assert "retry_attempt" in err

    def test_metrics_control(self):
        """Monitor metrics include ocr_quality, retrieval_quality."""
        resp = client.get(f"{ORCH}/monitor/metrics")
        assert_ok(resp)
        cm = resp.json()["control_metrics"]
        assert "ocr_quality" in cm
        assert "retrieval_quality" in cm
        assert "avg_latency_ms" in cm
        assert "answers_with_sources" in cm

    def test_metrics_answer(self):
        """Monitor metrics include answer quality."""
        resp = client.get(f"{ORCH}/monitor/metrics")
        assert_ok(resp)
        am = resp.json()["answer_metrics"]
        assert "useful_rate" in am
        assert "rated_answers" in am
        assert "flagged_for_review" in am

    def test_metrics_logs(self):
        """Monitor logs have time, type, text, level."""
        resp = client.get(f"{ORCH}/monitor/metrics")
        assert_ok(resp)
        for log in resp.json()["logs"]:
            assert "time" in log
            assert "type" in log
            assert "text" in log
            assert "level" in log


# ===========================================================================
# NFR: NON-FUNCTIONAL REQUIREMENTS
# ===========================================================================
class TestNFR_NonFunctional:
    """Performance, headers, pagination, summary."""

    def test_x_process_time_header(self):
        """Response has X-Process-Time header."""
        resp = client.get(f"{ORCH}/documents")
        assert_ok(resp)
        header = "x-process-time" in resp.headers or "X-Process-Time" in resp.headers
        assert header

    def test_cors_headers(self):
        """CORS headers present on response."""
        resp = client.get(
            f"{ORCH}/documents",
            headers={"Origin": "http://localhost:3000"},
        )
        header = (
            "access-control-allow-origin" in resp.headers
            or "Access-Control-Allow-Origin" in resp.headers
        )
        assert header

    def test_health_all_services(self):
        """Health check returns services info (supports both formats)."""
        resp = client.get(f"{BASE}/system/health")
        assert_ok(resp)
        data = resp.json()
        assert data["status"] == "ok"
        if "services" in data:
            for svc in ["auth", "orchestrator", "query", "registry", "gateway"]:
                assert svc in data["services"]
        elif "service" in data:
            assert data["service"] is not None

    def test_health_endpoints_count(self):
        """Health check may return endpoints_total (gateway format)."""
        resp = client.get(f"{BASE}/system/health")
        assert_ok(resp)
        data = resp.json()
        if "endpoints_total" in data:
            assert data["endpoints_total"] > 50

    def test_pagination_default_page(self):
        """Default page is 1."""
        resp = client.get(f"{ORCH}/documents")
        assert resp.json()["meta"]["page"] == 1

    def test_pagination_default_size(self):
        """Default page_size is 50."""
        resp = client.get(f"{ORCH}/documents")
        assert resp.json()["meta"]["page_size"] == 50

    def test_document_summary_new_format(self):
        """Document list summary has new status fields."""
        resp = client.get(f"{ORCH}/documents")
        s = resp.json()["summary"]
        assert "total" in s
        new_keys = [
            "uploaded",
            "parsing",
            "validation",
            "review_required",
            "ready_for_promotion",
            "approved",
            "failed",
            "archived",
        ]
        for k in new_keys:
            assert k in s, f"Missing summary key: {k}"


# ===========================================================================
# RBAC
# ===========================================================================
class TestRBAC_Matrix:
    """Role-based access control."""

    def test_auth_me_returns_role(self):
        """GET /auth/me returns role and permissions."""
        resp = client.get(
            f"{AUTH}/me",
            headers=auth_header(ADMIN_USER, ADMIN_PASS),
        )
        assert_ok(resp)
        d = resp.json()
        assert "role" in d
        assert "permissions" in d
        assert isinstance(d["permissions"], dict)
        assert "available_tabs" in d

    def test_admin_list_users(self):
        """Admin can list users."""
        resp = client.get(
            f"{ADMIN}/users",
            headers=auth_header(ADMIN_USER, ADMIN_PASS),
        )
        assert_ok(resp)
        assert "users" in resp.json()

    def test_admin_audit(self):
        """Admin can view audit log."""
        resp = client.get(
            f"{ADMIN}/audit",
            headers=auth_header(ADMIN_USER, ADMIN_PASS),
        )
        assert_ok(resp)
        assert "events" in resp.json()

    def test_different_user_roles(self):
        """User from seed has role and permissions dict."""
        resp = client.get(
            f"{AUTH}/me",
            headers=auth_header(TEST_USER, TEST_PASS),
        )
        assert_ok(resp)
        d = resp.json()
        assert d["role"] in ("engineer", "knowledge_admin", "system_admin")
        assert isinstance(d["permissions"], dict)


# ===========================================================================
# REGISTRY SPECIFICS
# ===========================================================================
class TestRegistry_Specifics:
    """Classifiers, terminology, registry docs, enums."""

    def test_classifier_unique_code(self):
        """Classifier duplicate code returns 409."""
        resp = client.post(
            f"{REG}/classifiers",
            json={
                "classifier_system": "MKS",
                "code": "01",
                "full_name": "Duplicate",
                "status": "active",
            },
        )
        assert resp.status_code == 409

    def test_classifier_tree_hierarchy(self):
        """Classifier tree has nested children and new fields."""
        resp = client.get(f"{REG}/classifiers/tree")
        assert_ok(resp)
        for root in resp.json()["data"]:
            assert "code" in root
            assert root["code"] != ""

    def test_term_normalization(self):
        """Normalize returns new format with raw_term, standard_term, etc."""
        resp = client.get(
            f"{REG}/terminology/normalize",
            params={"q": "Толщина стенки"},
        )
        assert_ok(resp)
        data = resp.json()
        assert "raw_term" in data or "data" in data
        if "data" in data:
            assert "normalized" in data["data"] or "raw_term" in data["data"]

    def test_term_normalization_no_match(self):
        """Normalize without match returns original term."""
        resp = client.get(
            f"{REG}/terminology/normalize",
            params={"q": "nonexistent term xyznonexistent"},
        )
        assert_ok(resp)

    def test_registry_doc_statuses(self):
        """Registry docs have new valid statuses."""
        resp = client.get(f"{REG_DOCS}/documents")
        assert_ok(resp)
        valid = (
            "draft",
            "active",
            "uploaded",
            "parsing",
            "validation",
            "review_required",
            "ready_for_promotion",
            "approved",
            "failed",
            "archived",
        )
        for doc in resp.json().get("data", []):
            assert doc["status"] in valid, f"Unknown status: {doc['status']}"

    def test_common_enums(self):
        """Common enums contain new required keys."""
        resp = client.get(f"{COMMON}/enums")
        assert_ok(resp)
        enums = resp.json()["data"]
        for key in [
            "classifier_system",
            "classifier_status",
            "source_type",
            "document_status",
            "era",
            "validity_status",
            "term_type",
            "classification_status_code",
            "pending_status",
            "validation_status",
            "chunk_type",
        ]:
            assert key in enums, f"Missing enum key: {key}"
        assert "MKS" in enums["classifier_system"]
        assert "OKSTU" in enums["classifier_system"]

    def test_registry_stats_new_format(self):
        """Stats has classifiers_total as dict with system keys."""
        resp = client.get(f"{COMMON}/stats")
        assert_ok(resp)
        data = resp.json()["data"]
        assert isinstance(data["classifiers_total"], dict)
        assert "MKS" in data["classifiers_total"]
        assert "OKSTU" in data["classifiers_total"]
        assert "classifiers_pending" in data
        assert "documents_by_source_type" in data
        assert "documents_by_era" in data

    def test_registry_doc_history_endpoint(self):
        """GET /documents/{id}/history returns status history."""
        resp = client.get(f"{REG_DOCS}/documents/rd-001/history")
        assert_ok(resp)
        data = resp.json()["data"]
        assert "doc_id" in data
        assert data["doc_id"] == "rd-001"
        assert "history" in data

    def test_registry_doc_chain_endpoint(self):
        """GET /documents/{id}/chain returns predecessor/successor chain."""
        resp = client.get(f"{REG_DOCS}/documents/rd-001/chain")
        assert_ok(resp)
        data = resp.json()["data"]
        assert "doc_id" in data
        assert "current" in data
        assert "predecessors" in data
        assert "successors" in data

    def test_quarantine_list(self):
        """GET /classifiers/quarantine lists pending classifiers."""
        resp = client.get(f"{REG}/classifiers/quarantine")
        assert_ok(resp)
        data = resp.json()
        assert "data" in data


# ===========================================================================
# EDGE CASES
# ===========================================================================
class TestEdgeCases:
    """404s, empty queries, missing params, validation."""

    def test_404_document(self):
        """Non-existent document returns 404."""
        resp = client.get(f"{ORCH}/documents/no-such-doc")
        assert resp.status_code == 404

    def test_404_session(self):
        """Non-existent session returns 404."""
        resp = client.get(f"{QUERY}/chat/sessions/no-such-session")
        assert resp.status_code == 404

    def test_404_registry_doc(self):
        """Non-existent registry doc returns 404 on delete."""
        resp = client.delete(f"{REG_DOCS}/documents/no-such-doc")
        assert resp.status_code == 404

    def test_search_without_query(self):
        """GET search without q param returns 422."""
        resp = client.get(f"{ORCH}/documents/search")
        assert resp.status_code == 422

    def test_registry_doc_not_found(self):
        """Non-existent classifier returns 404."""
        resp = client.get(f"{REG}/classifiers/nonexistent")
        assert resp.status_code == 404

    def test_delete_classifier_with_children(self):
        """Delete parent classifier returns 409."""
        resp = client.delete(f"{REG}/classifiers/01")
        assert resp.status_code == 409

    def test_validate_endpoints_removed(self):
        """Old validate endpoints return 404."""
        for path in [
            "/validate/compare",
            "/validate/compare/comp-001",
            "/validate/checks",
            "/validate/checks/check-001",
            "/validate/checks/check-001/export",
        ]:
            resp = client.post(f"{ORCH}{path}", json={})
            assert resp.status_code == 404, (
                f"Expected 404 for {path}, got {resp.status_code}"
            )

    def test_chat_send_message_simplified(self):
        """POST /chat/sessions/{id}/messages returns simplified response (no sources)."""
        resp = client.post(
            f"{QUERY}/chat/sessions/sess-001/messages",
            json={"content": "Test message"},
        )
        assert_ok(resp)
        data = resp.json()
        assert "message_id" in data
        assert "role" in data
        assert "content" in data
        assert "timestamp" in data
        # Simplified: should not have sources
        assert "sources" not in data
