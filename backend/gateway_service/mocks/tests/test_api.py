"""
Comprehensive API tests for PKB Neuroassistant Mock Services.
Tests all 4 services through the unified gateway (port 8081).
Updated for new API specifications — seed data, models, endpoints.
"""

import os
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import pytest
from fastapi.testclient import TestClient

import mocks.gateway

# Import rate limiter state to reset between test classes
from mocks.auth_service.main import _rate_limits as _auth_rate_limits

# Разрешаем анонимный доступ в тестах (тесты не проверяют RBAC)
mocks.gateway.ALLOW_ANONYMOUS = True
from mocks.gateway import app

client = TestClient(app, raise_server_exceptions=False)

# Constants
BASE = "/api/v1"
AUTH = f"{BASE}/auth"
ADMIN = f"{BASE}/admin"
ORCH = f"{BASE}"
QUERY = f"{BASE}"
REG_DOCS = f"{BASE}/registry"
REG = f"{BASE}"
COMMON = f"{BASE}/common"

TEST_USER_EMAIL = "ivanov@example.com"
TEST_USER_PASS = "secret123"


def _reset_rate_limiter():
    """Reset the auth rate limiter between test classes (5 req/min per IP)."""
    _auth_rate_limits.clear()


# Cached tokens to avoid hitting the 5 req/min rate limiter
# All tokens are pre-cached at module load time.
# Note: get_token() and engineer_header() both use ivanov@example.com
_CACHED_TOKEN: str = ""
_CACHED_ENGINEER_HEADER: dict = {}
_CACHED_ADMIN_HEADER: dict = {}
_CACHED_KUZNETSOV_TOKEN: str = ""
_CACHED_PETROVA_TOKEN: str = ""


def _precache_all_tokens():
    """Pre-cache (5) tokens at module load to avoid rate limiting (5 req/min per IP).

    Login calls: ivanov (shared), admin, kuznetsov, petrova = 4 total
    """
    # 1. ivanov@example.com — shared by get_token() and engineer_header()
    resp = client.post(
        f"{AUTH}/token",
        json={"username": "ivanov@example.com", "password": "secret123"},
    )
    token = resp.json().get("access_token", "")
    global _CACHED_TOKEN
    _CACHED_TOKEN = token
    global _CACHED_ENGINEER_HEADER
    _CACHED_ENGINEER_HEADER = {"Authorization": f"Bearer {token}"}

    # 2. admin@example.com
    resp = client.post(
        f"{AUTH}/token",
        json={"username": "admin@example.com", "password": "admin123"},
    )
    global _CACHED_ADMIN_HEADER
    _CACHED_ADMIN_HEADER = {"Authorization": f"Bearer {resp.json()['access_token']}"}

    # 3. kuznetsov@example.com
    resp = client.post(
        f"{AUTH}/token",
        json={"username": "kuznetsov@example.com", "password": "secret789"},
    )
    global _CACHED_KUZNETSOV_TOKEN
    _CACHED_KUZNETSOV_TOKEN = resp.json().get("access_token", "")

    # 4. petrova@example.com
    resp = client.post(
        f"{AUTH}/token",
        json={"username": "petrova@example.com", "password": "secret456"},
    )
    global _CACHED_PETROVA_TOKEN
    _CACHED_PETROVA_TOKEN = resp.json().get("access_token", "")


# Pre-cache all tokens at module load time
_precache_all_tokens()


def _login_user(username: str, password: str) -> dict:
    """Uncached login call — for tests that specifically test login behavior."""
    resp = client.post(
        f"{AUTH}/token",
        json={"username": username, "password": password},
    )
    return resp.json()


def _get_cached_token(username: str, password: str) -> str:
    """Get a token for a user from the pre-cached store."""
    cache_key = f"{username}:{password}"
    if cache_key == f"{TEST_USER_EMAIL}:{TEST_USER_PASS}":
        return _CACHED_TOKEN
    if cache_key == "admin@example.com:admin123":
        return _CACHED_ADMIN_HEADER.get("Authorization", "").replace("Bearer ", "")
    if cache_key == "ivanov@example.com:secret123":
        return _CACHED_ENGINEER_HEADER.get("Authorization", "").replace("Bearer ", "")
    if cache_key == "kuznetsov@example.com:secret789":
        return _CACHED_KUZNETSOV_TOKEN
    if cache_key == "petrova@example.com:secret456":
        return _CACHED_PETROVA_TOKEN
    # Fallback — this will likely be rate limited, but cache miss is rare
    return _login_user(username, password).get("access_token", "")


def get_token() -> str:
    """Returns the pre-cached token for the test user."""
    return _CACHED_TOKEN


def auth_header() -> dict:
    """Returns pre-cached admin token for admin endpoint tests."""
    return _CACHED_ADMIN_HEADER


def engineer_header() -> dict:
    """Returns pre-cached engineer token for RBAC-negative tests."""
    return _CACHED_ENGINEER_HEADER


def assert_ok(resp, status_code=200):
    assert resp.status_code == status_code, (
        f"Expected {status_code}, got {resp.status_code}: {resp.text[:200]}"
    )


def _make_header_from_token(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def assert_paginated(data):
    assert "meta" in data, f"Missing meta: {data}"
    assert "total" in data["meta"]
    assert "page" in data["meta"]
    assert "page_size" in data["meta"]


# ===========================================================================
# 1. AUTH SERVICE TESTS
# ===========================================================================


class TestAuthService:
    def setup_method(self):
        _reset_rate_limiter()

    def test_1_login_success(self):
        resp = client.post(
            f"{AUTH}/token",
            json={"username": TEST_USER_EMAIL, "password": TEST_USER_PASS},
        )
        assert_ok(resp)
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 3600
        assert "expires_at" in data

    def test_2_login_invalid_password(self):
        resp = client.post(
            f"{AUTH}/token", json={"username": TEST_USER_EMAIL, "password": "wrong"}
        )
        assert resp.status_code == 401
        assert "error" in resp.json()

    def test_3_refresh_token(self):
        login = client.post(
            f"{AUTH}/token",
            json={"username": TEST_USER_EMAIL, "password": TEST_USER_PASS},
        ).json()
        resp = client.post(
            f"{AUTH}/refresh", json={"refresh_token": login["refresh_token"]}
        )
        assert_ok(resp)
        assert "access_token" in resp.json()

    def test_4_revoke_token(self):
        login = client.post(
            f"{AUTH}/token",
            json={"username": TEST_USER_EMAIL, "password": TEST_USER_PASS},
        ).json()
        resp = client.post(
            f"{AUTH}/revoke", json={"refresh_token": login["refresh_token"]}
        )
        assert_ok(resp)
        assert resp.json()["message"] == "Токен отозван"

    def test_5_get_me(self):
        resp = client.get(f"{AUTH}/me", headers=auth_header())
        assert_ok(resp)
        data = resp.json()
        assert "user_id" in data
        assert "full_name" in data
        assert "permissions" in data
        # permissions is Dict[str, bool] in new spec
        assert isinstance(data["permissions"], dict)

    def test_6_list_users(self):
        resp = client.get(
            f"{ADMIN}/users", params={"page": 1, "page_size": 3}, headers=auth_header()
        )
        assert_ok(resp)
        data = resp.json()
        assert "users" in data
        assert_paginated(data)

    def test_7_list_users_filter_role(self):
        resp = client.get(
            f"{ADMIN}/users", params={"role": "engineer"}, headers=auth_header()
        )
        assert_ok(resp)
        for user in resp.json()["users"]:
            assert "engineer" in user.get("roles", [])

    def test_8_list_users_search(self):
        resp = client.get(
            f"{ADMIN}/users", params={"search": "Ivanov"}, headers=auth_header()
        )
        assert_ok(resp)

    def test_9_create_user(self):
        resp = client.post(
            f"{ADMIN}/users",
            json={
                "email": "new@test.com",
                "full_name": "New User",
                "password": "Pass123!",
                "roles": ["engineer"],
            },
            headers=auth_header(),
        )
        assert_ok(resp, 201)
        assert resp.json()["email"] == "new@test.com"

    def test_10_create_user_duplicate(self):
        resp = client.post(
            f"{ADMIN}/users",
            json={
                "email": "ivanov@example.com",
                "full_name": "Dup",
                "password": "Pass123!",
                "roles": ["engineer"],
            },
            headers=auth_header(),
        )
        assert resp.status_code == 409

    def test_11_get_user(self):
        resp = client.get(f"{ADMIN}/users/u-001", headers=auth_header())
        assert_ok(resp)
        assert resp.json()["user_id"] == "u-001"

    def test_12_get_user_not_found(self):
        resp = client.get(f"{ADMIN}/users/nonexistent", headers=auth_header())
        assert resp.status_code == 404

    def test_13_update_user(self):
        resp = client.put(
            f"{ADMIN}/users/u-001",
            json={"position": "Lead Engineer"},
            headers=auth_header(),
        )
        assert_ok(resp)
        assert resp.json()["position"] == "Lead Engineer"

    def test_14_patch_user_role(self):
        resp = client.patch(
            f"{ADMIN}/users/u-002", json={"role": "system_admin"}, headers=auth_header()
        )
        assert_ok(resp)

    def test_15_deactivate_user(self):
        create = client.post(
            f"{ADMIN}/users",
            json={
                "email": "todel@test.com",
                "full_name": "To Del",
                "password": "Pass123!",
                "roles": ["engineer"],
            },
            headers=auth_header(),
        ).json()
        resp = client.delete(
            f"{ADMIN}/users/{create['user_id']}", headers=auth_header()
        )
        assert_ok(resp)
        assert resp.json()["is_active"] is False

    def test_16_list_roles(self):
        resp = client.get(f"{ADMIN}/roles", headers=auth_header())
        assert_ok(resp)
        assert len(resp.json()["roles"]) >= 3

    def test_17_create_role(self):
        resp = client.post(
            f"{ADMIN}/roles",
            json={"name": "Test Role", "permissions": ["test:read"]},
            headers=auth_header(),
        )
        assert_ok(resp, 201)

    def test_18_list_audit(self):
        resp = client.get(f"{ADMIN}/audit", headers=auth_header())
        assert_ok(resp)
        data = resp.json()
        assert "events" in data
        assert_paginated(data)

    def test_19_audit_filters(self):
        resp = client.get(
            f"{ADMIN}/audit", params={"user_id": "u-001"}, headers=auth_header()
        )
        assert_ok(resp)

    def test_20_internal_validate_token(self):
        resp = client.post(
            f"{BASE}/internal/auth/validate",
            json={"access_token": "valid_token_12345"},
        )
        assert_ok(resp)
        assert resp.json()["valid"] is True

    def test_21_internal_validate_invalid(self):
        resp = client.post(
            f"{BASE}/internal/auth/validate", json={"access_token": "short"}
        )
        assert resp.status_code == 401

    def test_22_error_format(self):
        resp = client.get(f"{ADMIN}/users/nonexistent", headers=auth_header())
        assert resp.status_code == 404


# ===========================================================================
# 2. ORCHESTRATOR SERVICE TESTS
# ===========================================================================


class TestOrchestratorService:
    def setup_method(self):
        _reset_rate_limiter()

    def test_23_list_documents(self):
        resp = client.get(f"{ORCH}/documents")
        assert_ok(resp)
        data = resp.json()
        assert "items" in data
        assert "summary" in data
        assert_paginated(data)
        # New summary structure
        summary = data["summary"]
        assert "total" in summary
        assert "uploaded" in summary
        assert "parsing" in summary
        assert "validation" in summary
        assert "review_required" in summary
        assert "ready_for_promotion" in summary
        assert "approved" in summary
        assert "failed" in summary
        assert "archived" in summary

    def test_24_list_documents_filter_type(self):
        resp = client.get(f"{ORCH}/documents", params={"document_type": "GOST"})
        assert_ok(resp)
        for doc in resp.json()["items"]:
            assert doc["source_type"] == "GOST"

    def test_25_list_documents_filter_status(self):
        resp = client.get(f"{ORCH}/documents", params={"status": "completed"})
        assert_ok(resp)

    def test_26_get_document(self):
        resp = client.get(f"{ORCH}/documents/doc-001")
        assert_ok(resp)
        data = resp.json()
        assert data["document_id"] == "doc-001"
        # New fields in DocumentDetailResponse
        assert "doc_code" in data
        assert "source_type" in data
        assert "era" in data
        assert "validity_status" in data
        assert "jurisdiction" in data
        assert "issuing_body" in data
        assert "mks_oks_code" in data
        assert "okstu_code" in data
        assert "classification_status" in data
        assert "successor_doc_id" in data
        assert "predecessor_doc_id" in data
        assert "chunk_container_id" in data
        assert "metadata" in data
        assert "latest_version" in data
        assert "total_versions" in data
        assert "chunk_count" in data

    def test_27_get_document_not_found(self):
        resp = client.get(f"{ORCH}/documents/nonexistent")
        assert resp.status_code == 404

    def test_28_document_status(self):
        resp = client.get(f"{ORCH}/documents/doc-001/status")
        assert_ok(resp)
        data = resp.json()
        assert data["status"] == "completed"
        # New pipeline structure
        assert "pipeline" in data
        pipeline = data["pipeline"]
        assert "formation" in pipeline
        assert "indexation" in pipeline
        assert "parsing" in pipeline["formation"]
        assert "validation" in pipeline["formation"]
        assert "registry" in pipeline["formation"]
        assert "rag_indexing" in pipeline["indexation"]
        # Chunk summary
        assert "chunk_summary" in data
        assert "total" in data["chunk_summary"]
        assert "indexed" in data["chunk_summary"]

    def test_29_document_file(self):
        resp = client.get(f"{ORCH}/documents/doc-001/file")
        assert_ok(resp)
        assert "file_url" in resp.json()

    def test_30_document_pages(self):
        resp = client.get(f"{ORCH}/documents/doc-001/pages")
        assert_ok(resp)
        assert len(resp.json()["pages"]) > 0

    def test_31_page_detail(self):
        resp = client.get(f"{ORCH}/documents/doc-001/pages/1")
        assert_ok(resp)
        assert "blocks" in resp.json()

    def test_32_page_preview(self):
        resp = client.get(f"{ORCH}/documents/doc-001/pages/1/preview")
        assert_ok(resp)
        assert "preview_url" in resp.json()

    def test_33_page_text(self):
        resp = client.get(f"{ORCH}/documents/doc-001/pages/1/text")
        assert_ok(resp)
        assert "full_text" in resp.json()

    def test_34_document_parameters(self):
        resp = client.get(f"{ORCH}/documents/doc-001/parameters")
        assert_ok(resp)
        assert "parameters" in resp.json()
        assert "extraction_confidence" in resp.json()

    def test_35_document_queue(self):
        resp = client.get(f"{ORCH}/documents/queue")
        assert_ok(resp)
        data = resp.json()
        assert "queue" in data
        if len(data["queue"]) > 0:
            item = data["queue"][0]
            # New queue item uses pipeline structure
            assert "pipeline" in item
            assert "formation" in item["pipeline"]
            assert "indexation" in item["pipeline"]

    def test_36_post_search(self):
        resp = client.post(
            f"{ORCH}/documents/search", json={"query": "wall thickness", "top_k": 5}
        )
        assert_ok(resp)
        data = resp.json()
        assert "items" in data
        assert len(data["items"]) > 0
        # New field names: section_id, clause, content
        item = data["items"][0]
        assert "section_id" in item
        assert "clause" in item
        assert "content" in item
        assert "page" in item

    def test_37_get_search(self):
        resp = client.get(
            f"{ORCH}/documents/search", params={"q": "wall thickness", "top_k": 3}
        )
        assert_ok(resp)
        assert len(resp.json()["items"]) > 0

    def test_38_search_with_filters(self):
        resp = client.post(
            f"{ORCH}/documents/search",
            json={"query": "size", "filters": {"document_type": "normative"}},
        )
        assert_ok(resp)

    def test_39_document_errors(self):
        resp = client.get(f"{ORCH}/documents/doc-005/errors")
        assert_ok(resp)
        assert "errors" in resp.json()

    # --- validate/compare and validate/checks tests REMOVED ---

    def test_40_monitor_metrics(self):
        resp = client.get(f"{ORCH}/monitor/metrics")
        assert_ok(resp)
        data = resp.json()
        assert "control_metrics" in data
        assert "logs" in data

    def test_41_reprocess_document(self):
        resp = client.post(f"{ORCH}/documents/doc-001/reprocess", json={"mode": "full"})
        assert_ok(resp, 202)
        assert resp.json()["status"] == "parsing"

    def test_42_upload_document(self):
        """Upload document — new response format with task_id, version_id etc."""
        resp = client.post(
            f"{ORCH}/documents",
            files={"file": ("test.pdf", b"%PDF-1.4 mock content", "application/pdf")},
        )
        assert_ok(resp, 202)
        data = resp.json()
        # New response fields
        assert "task_id" in data
        assert "version_id" in data
        assert "status" in data
        assert "content_hash_sha256" in data
        assert "is_duplicate_file" in data
        assert "is_duplicate_document" in data
        assert "title_hash_sha256" in data
        assert "created_at" in data

    def test_43_delete_document(self):
        # Upload a doc first to have something to delete
        create = client.post(
            f"{ORCH}/documents",
            files={"file": ("todel.pdf", b"delete me", "application/pdf")},
        ).json()
        # We need to get the document_id. Since the upload response doesn't have it,
        # let's list documents and find the latest one
        resp = client.get(f"{ORCH}/documents", params={"page": 1, "page_size": 1})
        docs = resp.json()["items"]
        if docs:
            doc_id = docs[0]["document_id"]
            resp = client.delete(f"{ORCH}/documents/{doc_id}")
            assert_ok(resp)

    def test_44_health(self):
        resp = client.get(f"{ORCH}/system/health")
        assert_ok(resp)

    # --- NEW endpoint tests for documents ---

    def test_45_add_document_version(self):
        """POST /documents/{doc_id}/versions — add new version."""
        resp = client.post(
            f"{ORCH}/documents/doc-001/versions",
            files={"file": ("v2.pdf", b"version 2 content", "application/pdf")},
        )
        assert_ok(resp, 201)
        data = resp.json()
        assert "version_id" in data
        assert "version_number" in data
        assert data["document_id"] == "doc-001"
        assert data["version_number"] > 1
        assert "content_hash_sha256" in data
        assert "title_hash_sha256" in data
        assert "status" in data

    def test_46_list_document_versions(self):
        """GET /documents/{doc_id}/versions — list versions."""
        resp = client.get(f"{ORCH}/documents/doc-001/versions")
        assert_ok(resp)
        data = resp.json()
        assert "versions" in data
        assert "total" in data
        assert len(data["versions"]) > 0

    def test_47_approve_document(self):
        """POST /documents/{doc_id}/approve — approve document."""
        resp = client.post(f"{ORCH}/documents/doc-001/approve")
        assert_ok(resp)
        data = resp.json()
        assert data["document_id"] == "doc-001"
        assert data["status"] == "approved"
        assert "approved_at" in data
        assert "previous_status" in data

    def test_50_get_document_history(self):
        """GET /documents/{doc_id}/history — status history."""
        resp = client.get(f"{ORCH}/documents/doc-001/history")
        assert_ok(resp)
        data = resp.json()
        assert data["document_id"] == "doc-001"
        assert "events" in data
        assert "total" in data
        assert len(data["events"]) > 0


# ===========================================================================
# 3. QUERY SERVICE TESTS
# ===========================================================================


class TestQueryService:
    def setup_method(self):
        _reset_rate_limiter()

    def test_52_create_session(self):
        resp = client.post(
            f"{QUERY}/chat/sessions",
            json={"title": "Test Session", "document_ids": ["doc-001"]},
        )
        assert_ok(resp, 201)
        assert "session_id" in resp.json()

    def test_53_list_sessions(self):
        resp = client.get(f"{QUERY}/chat/sessions")
        assert_ok(resp)
        data = resp.json()
        assert "sessions" in data
        assert_paginated(data)

    def test_54_get_session(self):
        resp = client.get(f"{QUERY}/chat/sessions/sess-001")
        assert_ok(resp)
        assert resp.json()["session_id"] == "sess-001"

    def test_55_get_session_not_found(self):
        resp = client.get(f"{QUERY}/chat/sessions/nonexistent")
        assert resp.status_code == 404

    def test_56_update_session(self):
        resp = client.put(f"{QUERY}/chat/sessions/sess-002", json={"title": "Updated"})
        assert_ok(resp)
        assert resp.json()["title"] == "Updated"

    def test_57_send_message(self):
        """POST /chat/sessions/{id}/messages — simplified response (no sources)."""
        resp = client.post(
            f"{QUERY}/chat/sessions/sess-001/messages",
            json={"content": "What is the wall thickness?"},
        )
        assert_ok(resp)
        data = resp.json()
        assert data["role"] == "assistant"
        # Simplified response — sources are no longer returned
        assert "message_id" in data
        assert "session_id" in data
        assert "status" in data
        assert "content" in data

    def test_58_manage_context(self):
        resp = client.post(
            f"{QUERY}/chat/sessions/sess-001/context", json={"action": "clear_history"}
        )
        assert_ok(resp)
        assert resp.json()["status"] == "completed"

    def test_59_export_session(self):
        resp = client.post(
            f"{QUERY}/chat/sessions/sess-001/export", json={"format": "pdf"}
        )
        assert_ok(resp)
        assert "export_id" in resp.json()

    def test_60_feedback(self):
        """POST /chat/feedback — includes new fields: answer_id, useful, opened_citation_ids."""
        resp = client.post(
            f"{QUERY}/chat/feedback",
            json={
                "session_id": "sess-001",
                "message_id": "msg-001",
                "rating": 5,
                "answer_id": "ans-001",
                "useful": True,
                "opened_citation_ids": ["cit-001", "cit-002"],
            },
        )
        assert_ok(resp)
        assert resp.json()["saved"] is True

    def test_61_chat_history(self):
        resp = client.get(f"{QUERY}/chat/history")
        assert_ok(resp)
        data = resp.json()
        assert "items" in data
        assert_paginated(data)

    def test_62_export_history(self):
        resp = client.get(f"{QUERY}/chat/history/export", params={"format": "csv"})
        assert_ok(resp)

    def test_63_chat_ask(self):
        """POST /chat — supports 3 scenarios: completed, needs_clarification, conflict."""
        # Test completed scenario
        resp = client.post(
            f"{QUERY}/chat", json={"question": "What are the dimensions?"}
        )
        assert_ok(resp)
        data = resp.json()
        assert "scenario" in data
        assert data["scenario"] == "completed"
        assert "answer_id" in data
        assert "answer_items" in data
        if data["answer_items"]:
            item = data["answer_items"][0]
            # New source format: section_id, excerpt
            if "sources" in item:
                src = item["sources"][0]
                assert "section_id" in src
                assert "excerpt" in src
                assert "page" in src

    def test_63b_chat_ask_needs_clarification(self):
        """Chat ask with ambiguous question → needs_clarification scenario."""
        resp = client.post(f"{QUERY}/chat", json={"question": "This is ambiguous"})
        assert_ok(resp)
        data = resp.json()
        assert data["scenario"] == "needs_clarification"
        assert "missing_fields" in data

    def test_63c_chat_ask_conflict(self):
        """Chat ask with conflict-related question → conflict scenario."""
        resp = client.post(
            f"{QUERY}/chat", json={"question": "There is a conflict in norms"}
        )
        assert_ok(resp)
        data = resp.json()
        assert data["scenario"] == "conflict"
        assert "conflicts" in data

    def test_63d_chat_ask_with_context(self):
        """Chat ask with context field."""
        resp = client.post(
            f"{QUERY}/chat",
            json={
                "question": "Check dimensions",
                "context": {"document_ids": ["doc-001"]},
            },
        )
        assert_ok(resp)

    def test_64_text_search(self):
        """POST /text/search — new field names: section_id, content."""
        resp = client.post(
            f"{QUERY}/text/search", json={"text": "wall thickness", "top_k": 3}
        )
        assert_ok(resp)
        data = resp.json()
        assert "results" in data
        if data["results"]:
            result = data["results"][0]
            assert "section_id" in result
            assert "content" in result
            assert "page" in result

    def test_65_text_search_filtered(self):
        resp = client.post(
            f"{QUERY}/text/search",
            json={
                "text": "steel",
                "document_ids": ["doc-001"],
                "filters": {"document_type": "specification"},
            },
        )
        assert_ok(resp)

    def test_65b_text_search_with_options(self):
        """Text search with options field."""
        resp = client.post(
            f"{QUERY}/text/search",
            json={
                "text": "thickness",
                "top_k": 5,
                "options": {"search_mode": "semantic"},
            },
        )
        assert_ok(resp)

    def test_66_text_ask(self):
        """POST /text/ask — new field names: section_id, excerpt."""
        resp = client.post(
            f"{QUERY}/text/ask",
            json={"text": "What material is the body made of?"},
        )
        assert_ok(resp)
        data = resp.json()
        assert "answer" in data
        assert "sources" in data
        if data["sources"]:
            src = data["sources"][0]
            assert "section_id" in src
            assert "excerpt" in src
            assert "page" in src

    def test_67_delete_session(self):
        create = client.post(
            f"{QUERY}/chat/sessions", json={"title": "To Delete"}
        ).json()
        sess_id = create["session_id"]
        resp = client.delete(f"{QUERY}/chat/sessions/{sess_id}")
        assert_ok(resp)
        resp = client.get(f"{QUERY}/chat/sessions/{sess_id}")
        assert resp.status_code == 404


# ===========================================================================
# 4. REGISTRY SERVICE TESTS
# ===========================================================================


class TestRegistryService:
    def setup_method(self):
        _reset_rate_limiter()

    def test_68_list_classifiers(self):
        resp = client.get(f"{REG}/classifiers")
        assert_ok(resp)
        data = resp.json()
        assert "data" in data
        assert_paginated(data)
        if data["data"]:
            classifier = data["data"][0]
            # New fields
            assert "classifier_system" in classifier
            assert "status" in classifier
            assert "effective_date" in classifier
            assert "replaced_by" in classifier
            assert "code" in classifier
            assert "full_name" in classifier

    def test_69_list_classifiers_search(self):
        resp = client.get(f"{REG}/classifiers", params={"search": "GOST"})
        assert_ok(resp)

    def test_69b_list_classifiers_filter_system(self):
        resp = client.get(f"{REG}/classifiers", params={"classifier_system": "MKS"})
        assert_ok(resp)
        for c in resp.json()["data"]:
            assert c["classifier_system"] == "MKS"

    def test_70_get_classifier_tree(self):
        resp = client.get(f"{REG}/classifiers/tree")
        assert_ok(resp)
        data = resp.json()
        assert "data" in data
        assert "meta" in data
        if data["data"]:
            node = data["data"][0]
            assert "classifier_system" in node
            assert "status" in node
            assert "effective_date" in node
            assert "replaced_by" in node

    def test_71_get_classifier_node(self):
        resp = client.get(f"{REG}/classifiers/01")
        assert_ok(resp)
        node = resp.json()["data"]
        assert node["code"] == "01"
        assert "classifier_system" in node
        assert "status" in node
        assert "effective_date" in node

    def test_72_get_classifier_not_found(self):
        resp = client.get(f"{REG}/classifiers/nonexistent")
        assert resp.status_code == 404

    def test_73_create_classifier(self):
        resp = client.post(
            f"{REG}/classifiers",
            json={
                "classifier_system": "MKS",
                "code": "99.999",
                "full_name": "Test Classifier",
                "status": "active",
                "effective_date": "2024-01-01",
            },
        )
        assert_ok(resp, 201)
        data = resp.json()["data"]
        assert data["code"] == "99.999"
        assert data["classifier_system"] == "MKS"
        assert data["status"] == "active"

    def test_74_create_classifier_duplicate(self):
        resp = client.post(
            f"{REG}/classifiers",
            json={
                "classifier_system": "MKS",
                "code": "01",
                "full_name": "Dup",
                "status": "active",
            },
        )
        assert resp.status_code == 409

    def test_75_update_classifier(self):
        resp = client.put(
            f"{REG}/classifiers/01",
            json={"full_name": "Updated Standard", "status": "active"},
        )
        assert_ok(resp)
        assert resp.json()["data"]["full_name"] == "Updated Standard"

    def test_76_patch_classifier(self):
        resp = client.patch(f"{REG}/classifiers/02", json={"parent_code": None})
        assert_ok(resp)

    def test_77_delete_classifier_with_children(self):
        resp = client.delete(f"{REG}/classifiers/01")
        assert resp.status_code == 409

    def test_78_import_classifiers(self):
        resp = client.post(
            f"{REG}/classifiers/import",
            json={
                "items": [
                    {
                        "classifier_system": "MKS",
                        "code": "IMP.001",
                        "full_name": "Imported 1",
                        "status": "active",
                        "effective_date": "2024-06-01",
                    }
                ]
            },
        )
        assert_ok(resp)
        assert resp.json()["data"]["inserted"] >= 1

    def test_79_list_terminology(self):
        resp = client.get(f"{REG}/terminology")
        assert_ok(resp)
        data = resp.json()
        assert "data" in data
        assert_paginated(data)
        if data["data"]:
            term = data["data"][0]
            # New fields
            assert "raw_term" in term
            assert "standard_term" in term
            assert "normalized_value" in term
            assert "term_type" in term
            assert "is_case_sensitive" in term
            assert "definition" in term
            assert "synonyms" in term
            assert "related_docs" in term
            assert "scope" in term
            assert "is_blocked" in term

    def test_80_search_terminology(self):
        resp = client.get(f"{REG}/terminology", params={"search": "thickness"})
        assert_ok(resp)

    def test_81_get_term(self):
        resp = client.get(f"{REG}/terminology/t-001")
        assert_ok(resp)
        data = resp.json()["data"]
        assert "raw_term" in data
        assert "standard_term" in data
        assert "normalized_value" in data
        assert "term_type" in data

    def test_82_get_term_not_found(self):
        resp = client.get(f"{REG}/terminology/nonexistent")
        assert resp.status_code == 404

    def test_83_create_term(self):
        resp = client.post(
            f"{REG}/terminology",
            json={
                "raw_term": "Test Term",
                "term_type": "preferred",
                "is_case_sensitive": False,
                "is_blocked": False,
                "synonyms": [],
                "related_docs": [],
            },
        )
        assert_ok(resp, 201)
        data = resp.json()["data"]
        assert data["raw_term"] == "Test Term"

    def test_84_update_term(self):
        resp = client.put(
            f"{REG}/terminology/t-001",
            json={"definition": "Updated definition"},
        )
        assert_ok(resp)

    def test_85_delete_term(self):
        create = client.post(
            f"{REG}/terminology",
            json={
                "raw_term": "Temp Term",
                "term_type": "preferred",
                "is_case_sensitive": False,
                "is_blocked": False,
                "synonyms": [],
                "related_docs": [],
            },
        ).json()
        term_id = create["data"]["id"]
        resp = client.delete(f"{REG}/terminology/{term_id}")
        assert_ok(resp)

    def test_86_normalize_term(self):
        """Normalize response: {raw_term, standard_term, normalized_value, term_type, is_blocked}."""
        resp = client.get(
            f"{REG}/terminology/normalize", params={"q": "Wall Thickness"}
        )
        assert_ok(resp)
        data = resp.json()["data"]
        assert "raw_term" in data
        assert "standard_term" in data
        assert "normalized_value" in data
        assert "term_type" in data
        assert "is_blocked" in data

    def test_87_import_terminology(self):
        resp = client.post(
            f"{REG}/terminology/import",
            json={
                "items": [
                    {
                        "raw_term": "Imported",
                        "term_type": "preferred",
                        "is_case_sensitive": False,
                        "is_blocked": False,
                        "synonyms": [],
                        "related_docs": [],
                    }
                ]
            },
        )
        assert_ok(resp)

    def test_88_list_registry_docs(self):
        resp = client.get(f"{REG_DOCS}/documents")
        assert_ok(resp)
        data = resp.json()
        assert "data" in data
        assert_paginated(data)
        if data["data"]:
            doc = data["data"][0]
            # New fields (~28 fields)
            assert "id" in doc
            assert "title" in doc
            assert "doc_code" in doc
            assert "source_type" in doc
            assert "title_hash_sha256" in doc
            assert "status" in doc
            assert "era" in doc
            assert "validity_status" in doc
            assert "jurisdiction" in doc
            assert "issuing_body" in doc
            assert "mks_oks_code" in doc
            assert "mks_name" in doc
            assert "okstu_code" in doc
            assert "okstu_name" in doc
            assert "classification_status" in doc
            assert "successor_doc_id" in doc
            assert "predecessor_doc_id" in doc
            assert "total_versions" in doc
            assert "chunk_count" in doc
            assert "created_by" in doc
            assert "updated_by" in doc

    def test_89_get_registry_doc(self):
        resp = client.get(f"{REG_DOCS}/documents/rd-001")
        assert_ok(resp)
        doc = resp.json()["data"]
        assert doc["id"] == "rd-001"
        assert "title" in doc
        assert "doc_code" in doc
        assert "source_type" in doc
        assert "classification_status" in doc

    def test_90_create_registry_doc(self):
        resp = client.post(
            f"{REG_DOCS}/documents",
            json={
                "title": "Test Doc",
                "doc_code": "TEST-001",
                "source_type": "GOST",
                "status": "draft",
                "era": "CURRENT",
                "validity_status": "active",
            },
        )
        assert_ok(resp, 201)
        data = resp.json()["data"]
        assert data["title"] == "Test Doc"
        assert data["doc_code"] == "TEST-001"
        assert "id" in data

    def test_91_update_registry_doc(self):
        resp = client.put(
            f"{REG_DOCS}/documents/rd-001",
            json={"jurisdiction": "RF"},
        )
        assert_ok(resp)

    def test_92_update_doc_status(self):
        """PATCH /documents/{id}/status — enhanced with comment."""
        resp = client.patch(
            f"{REG_DOCS}/documents/rd-002/status",
            json={"status": "archived", "comment": "Test archive"},
        )
        assert_ok(resp)
        data = resp.json()["data"]
        assert data["status"] == "archived"
        assert "previous_status" in data
        assert "history_id" in data

    def test_93_export_registry_docs(self):
        resp = client.get(f"{REG_DOCS}/documents/export", params={"format": "json"})
        assert_ok(resp)
        assert resp.json()["data"]["format"] == "json"

    def test_94_import_registry_docs(self):
        resp = client.post(
            f"{REG_DOCS}/documents/import",
            json=[
                {
                    "title": "Imported",
                    "doc_code": "IMP-001",
                    "source_type": "GOST",
                    "status": "draft",
                    "era": "CURRENT",
                    "validity_status": "active",
                }
            ],
        )
        assert_ok(resp)

    def test_95_delete_registry_doc(self):
        create = client.post(
            f"{REG_DOCS}/documents",
            json={
                "title": "To Delete",
                "doc_code": "DEL-001",
                "source_type": "GOST",
                "status": "draft",
                "era": "CURRENT",
                "validity_status": "active",
            },
        ).json()
        doc_id = create["data"]["id"]
        resp = client.delete(f"{REG_DOCS}/documents/{doc_id}")
        assert_ok(resp)

    def test_96_get_stats(self):
        """New stats structure with classifiers by system, documents by status/source_type/era."""
        resp = client.get(f"{COMMON}/stats")
        assert_ok(resp)
        data = resp.json()["data"]
        assert "classifiers_total" in data
        # classifiers_total is now a dict with system keys
        assert isinstance(data["classifiers_total"], dict)
        assert "MKS" in data["classifiers_total"]
        assert "OKSTU" in data["classifiers_total"]
        assert "UDC" in data["classifiers_total"]
        assert "classifiers_pending" in data
        assert "terminology_total" in data
        assert "documents_total" in data
        assert "documents_by_status" in data
        assert "documents_by_source_type" in data
        assert "documents_by_era" in data

    def test_97_get_enums(self):
        """Expanded enums with more values."""
        resp = client.get(f"{COMMON}/enums")
        assert_ok(resp)
        data = resp.json()["data"]
        assert "classifier_system" in data
        assert "classifier_status" in data
        assert "source_type" in data
        assert "document_status" in data
        assert "era" in data
        assert "validity_status" in data
        assert "term_type" in data
        assert "classification_status_code" in data
        assert "pending_status" in data
        assert "validation_status" in data
        assert "chunk_type" in data

    # --- NEW endpoint tests for Registry ---

    def test_98_list_quarantine(self):
        """GET /classifiers/quarantine — list pending classifiers."""
        resp = client.get(f"{REG}/classifiers/quarantine")
        assert_ok(resp)
        data = resp.json()
        assert "data" in data
        assert_paginated(data)

    def test_99_accept_quarantine(self):
        """POST /classifiers/quarantine/{id}/accept — accept pending classifier."""
        resp = client.post(f"{REG}/classifiers/quarantine/pend-001/accept")
        assert_ok(resp)
        data = resp.json()["data"]
        assert data["status"] == "accepted"
        assert "classifier_code" in data

    def test_100_reject_quarantine(self):
        """POST /classifiers/quarantine/{id}/reject — reject pending classifier."""
        resp = client.post(f"{REG}/classifiers/quarantine/pend-001/reject")
        assert_ok(resp)
        data = resp.json()["data"]
        assert data["status"] == "rejected"

    def test_101_validate_classification(self):
        """POST /classifiers/validate — validate classification code."""
        resp = client.post(
            f"{REG}/classifiers/validate",
            json={"code": "01", "classifier_system": "MKS"},
        )
        assert_ok(resp)
        data = resp.json()["data"]
        assert "valid" in data
        assert "code" in data
        assert "classifier_system" in data
        assert "exists_in_registry" in data
        assert "validation_status" in data

    def test_102_registry_doc_history(self):
        """GET /documents/{id}/history — registry doc history."""
        resp = client.get(f"{REG_DOCS}/documents/rd-001/history")
        assert_ok(resp)
        data = resp.json()["data"]
        assert "doc_id" in data
        assert data["doc_id"] == "rd-001"
        assert "history" in data

    def test_103_registry_doc_chain(self):
        """GET /documents/{id}/chain — registry doc chain (predecessors/successors)."""
        resp = client.get(f"{REG_DOCS}/documents/rd-001/chain")
        assert_ok(resp)
        data = resp.json()["data"]
        assert "doc_id" in data
        assert "current" in data
        assert "predecessors" in data
        assert "successors" in data


# ===========================================================================
# 5. GATEWAY TESTS
# ===========================================================================


class TestGateway:
    def setup_method(self):
        _reset_rate_limiter()

    def test_104_health(self):
        resp = client.get(f"{BASE}/system/health")
        assert_ok(resp)
        assert resp.json()["status"] == "ok"

    def test_105_routing_auth(self):
        resp = client.get(f"{AUTH}/me", headers=auth_header())
        assert_ok(resp)

    def test_106_routing_orchestrator(self):
        resp = client.get(f"{ORCH}/documents")
        assert_ok(resp)

    def test_107_routing_query(self):
        resp = client.get(f"{QUERY}/chat/sessions")
        assert_ok(resp)

    def test_108_routing_registry(self):
        resp = client.get(f"{REG}/classifiers")
        assert_ok(resp)

    def test_109_no_conflict_queue(self):
        resp = client.get(f"{ORCH}/documents/queue")
        assert_ok(resp)
        assert "queue" in resp.json()

    def test_110_no_conflict_search(self):
        resp = client.get(f"{ORCH}/documents/search", params={"q": "test", "top_k": 2})
        assert_ok(resp)

    def test_111_pagination_defaults(self):
        resp = client.get(f"{ORCH}/documents")
        meta = resp.json()["meta"]
        assert meta["page"] == 1
        assert meta["page_size"] == 50

    def test_112_pagination_custom(self):
        resp = client.get(f"{ORCH}/documents", params={"page": 1, "page_size": 3})
        assert resp.json()["meta"]["page_size"] == 3

    def test_113_no_route_conflict(self):
        # Verify /documents/queue is not caught by /documents/{doc_id}
        resp = client.get(f"{ORCH}/documents/queue")
        assert_ok(resp)
        assert "queue" in resp.json()
        # Verify /documents/search is not caught by /documents/{doc_id}
        resp = client.get(f"{ORCH}/documents/search", params={"q": "test"})
        assert_ok(resp)
        assert "items" in resp.json()


# ===========================================================================
# 6. AUTH-ME BINDING TESTS
# ===========================================================================


class TestAuthMeBinding:
    """Tests for GET /auth/me binding to JWT token."""

    def setup_method(self):
        _reset_rate_limiter()

    def test_114_me_returns_correct_user_by_token(self):
        """Login as kuznetsov, /auth/me should return kuznetsov's profile."""
        token = _get_cached_token("kuznetsov@example.com", "secret789")

        resp = client.get(f"{AUTH}/me", headers={"Authorization": f"Bearer {token}"})
        assert_ok(resp)
        data = resp.json()
        assert data["user_id"] == "u-004"
        assert data["full_name"] == "Кузнецов Дмитрий Олегович"
        assert data["role"] == "engineer"

    def test_115_me_returns_admin_user(self):
        """Login as admin, /auth/me should return admin."""
        token = _get_cached_token("admin@example.com", "admin123")

        resp = client.get(f"{AUTH}/me", headers={"Authorization": f"Bearer {token}"})
        assert_ok(resp)
        data = resp.json()
        assert data["user_id"] == "u-003"
        assert data["role"] == "system_admin"
        assert "admin" in data.get("available_tabs", [])

    def test_116_me_returns_401_without_token(self):
        """GET /auth/me without token should return 401."""
        resp = client.get(f"{AUTH}/me")
        assert resp.status_code == 401
        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] == "UNAUTHORIZED"

    def test_117_me_returns_401_with_invalid_token(self):
        """GET /auth/me with invalid token should return 401."""
        resp = client.get(
            f"{AUTH}/me",
            headers={"Authorization": "Bearer invalid_token_xxx"},
        )
        assert resp.status_code == 401
        data = resp.json()
        assert "error" in data


# ===========================================================================
# 7. RBAC TESTS
# ===========================================================================


class TestRBAC:
    """Tests for RBAC on /admin/* endpoints."""

    def setup_method(self):
        _reset_rate_limiter()

    _admin_token: str = ""
    _engineer_token: str = ""
    _petrova_token: str = ""

    def _get_admin_token(self) -> str:
        if not self._admin_token:
            self._admin_token = _get_cached_token("admin@example.com", "admin123")
        return self._admin_token

    def _get_engineer_token(self) -> str:
        if not self._engineer_token:
            self._engineer_token = _get_cached_token("ivanov@example.com", "secret123")
        return self._engineer_token

    def _get_petrova_token(self) -> str:
        if not self._petrova_token:
            self._petrova_token = _get_cached_token("petrova@example.com", "secret456")
        return self._petrova_token

    def test_118_admin_users_401_without_token(self):
        """GET /admin/users without token → 401."""
        resp = client.get(f"{ADMIN}/users")
        assert resp.status_code == 401
        data = resp.json()
        assert data["error"]["code"] == "UNAUTHORIZED"

    def test_119_admin_users_403_for_engineer(self):
        """GET /admin/users as engineer → 403."""
        token = self._get_engineer_token()
        resp = client.get(
            f"{ADMIN}/users", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 403
        data = resp.json()
        assert data["error"]["code"] == "FORBIDDEN"

    def test_120_admin_users_200_for_admin(self):
        """GET /admin/users as system_admin → 200."""
        token = self._get_admin_token()
        resp = client.get(
            f"{ADMIN}/users", headers={"Authorization": f"Bearer {token}"}
        )
        assert_ok(resp)
        assert "users" in resp.json()

    def test_121_admin_roles_403_for_engineer(self):
        """GET /admin/roles as engineer → 403."""
        token = self._get_engineer_token()
        resp = client.get(
            f"{ADMIN}/roles", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 403

    def test_122_admin_roles_200_for_admin(self):
        """POST /admin/roles as admin → 201."""
        token = self._get_admin_token()
        resp = client.post(
            f"{ADMIN}/roles",
            json={"name": "RBAC Test Role", "permissions": ["test:read"]},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert_ok(resp, 201)

    def test_123_admin_audit_403_for_knowledge_admin(self):
        """GET /admin/audit as knowledge_admin → 403."""
        token = self._get_petrova_token()
        resp = client.get(
            f"{ADMIN}/audit", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 403

    def test_124_admin_endpoints_all_blocked_for_non_admin(self):
        """All /admin/* variants blocked for non-admin users."""
        token = self._get_engineer_token()
        headers = {"Authorization": f"Bearer {token}"}
        for method, path in [
            ("GET", f"{ADMIN}/users"),
            ("POST", f"{ADMIN}/users"),
            ("GET", f"{ADMIN}/users/u-001"),
            ("PUT", f"{ADMIN}/users/u-001"),
            ("PATCH", f"{ADMIN}/users/u-001"),
            ("DELETE", f"{ADMIN}/users/u-001"),
            ("GET", f"{ADMIN}/roles"),
            ("POST", f"{ADMIN}/roles"),
            ("GET", f"{ADMIN}/audit"),
        ]:
            fn = {
                "GET": client.get,
                "POST": client.post,
                "PUT": client.put,
                "PATCH": client.patch,
                "DELETE": client.delete,
            }[method]
            resp = fn(path, headers=headers)
            assert resp.status_code in (
                401,
                403,
            ), f"{method} {path} returned {resp.status_code} for engineer"


# ===========================================================================
# 8. ERROR FORMAT TESTS
# ===========================================================================


class TestErrorFormat:
    """Tests for unified error format."""

    def setup_method(self):
        _reset_rate_limiter()

    def test_125_error_format_404(self):
        """404 error should use {error: {code, message, details}} format."""
        resp = client.get(f"{ORCH}/documents/nonexistent_doc_xxx")
        assert resp.status_code == 404
        data = resp.json()
        assert "error" in data, f"Missing 'error' wrapper: {data}"
        assert "code" in data["error"]
        assert "message" in data["error"]
        assert "details" in data["error"]
        assert data["error"]["code"] in ("NOT_FOUND", "DOCUMENT_NOT_FOUND")

    def test_126_error_format_401(self):
        """401 error should use wrapped format."""
        resp = client.get(f"{AUTH}/me")
        assert resp.status_code == 401
        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] == "UNAUTHORIZED"

    def test_127_error_format_403(self):
        """403 error should use wrapped format."""
        token = _get_cached_token("ivanov@example.com", "secret123")
        resp = client.get(
            f"{ADMIN}/users", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 403
        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] == "FORBIDDEN"

    def test_128_error_format_422_validation(self):
        """422 validation error should use wrapped format."""
        # Omit required 'password' field to trigger validation error
        resp = client.post(
            f"{AUTH}/token",
            json={"username": "test"},
        )
        assert resp.status_code == 422
        data = resp.json()
        assert "error" in data, f"Missing 'error' wrapper: {data}"
        assert data["error"]["code"] in ("VALIDATION_ERROR", "VALIDATION_FAILED")


# ===========================================================================
# 9. LOGIN USERNAME TESTS
# ===========================================================================


class TestLoginUsernameAndEmail:
    """Tests for login with username field (new spec: only username, no email field)."""

    def setup_method(self):
        _reset_rate_limiter()

    def test_129_login_with_username_full_email(self):
        """Login with username=full email should work."""
        resp = client.post(
            f"{AUTH}/token",
            json={"username": "ivanov@example.com", "password": "secret123"},
        )
        assert_ok(resp)
        assert "access_token" in resp.json()

    def test_130_login_with_username_part(self):
        """Login with username=ivanov (without domain) should work."""
        resp = client.post(
            f"{AUTH}/token",
            json={"username": "ivanov", "password": "secret123"},
        )
        assert_ok(resp)
        assert "access_token" in resp.json()

    def test_131_login_with_username_email_only(self):
        """Login with another user using full email."""
        resp = client.post(
            f"{AUTH}/token",
            json={"username": "petrova@example.com", "password": "secret456"},
        )
        assert_ok(resp)
        assert "access_token" in resp.json()

    def test_132_login_invalid_credentials(self):
        """Invalid credentials should return 401 with error wrapper."""
        resp = client.post(
            f"{AUTH}/token",
            json={"username": "ivanov@example.com", "password": "wrong_password"},
        )
        assert resp.status_code == 401
        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] == "UNAUTHORIZED"


# ===========================================================================
# 10. RESPONSE MODELS (OpenAPI schema) TESTS
# ===========================================================================


class TestResponseModels:
    """Tests that response_model schemas are present in OpenAPI."""

    def setup_method(self):
        _reset_rate_limiter()

    def test_133_openapi_has_chat_response_schema(self):
        """OpenAPI schema should define ChatResponse."""
        resp = client.get("/openapi.json")
        assert_ok(resp)
        schemas = resp.json().get("components", {}).get("schemas", {})
        assert "ChatResponse" in schemas, "Missing ChatResponse schema"
        assert "AnswerItem" in schemas, "Missing AnswerItem schema"

    def test_134_openapi_has_token_response(self):
        """OpenAPI schema should define TokenResponse."""
        resp = client.get("/openapi.json")
        schemas = resp.json().get("components", {}).get("schemas", {})
        assert "TokenResponse" in schemas

    def test_135_openapi_has_user_profile_response(self):
        """OpenAPI schema should define UserProfileResponse."""
        resp = client.get("/openapi.json")
        schemas = resp.json().get("components", {}).get("schemas", {})
        assert "UserProfileResponse" in schemas

    def test_136_openapi_has_text_search_response(self):
        """OpenAPI schema should define TextSearchResponse."""
        resp = client.get("/openapi.json")
        schemas = resp.json().get("components", {}).get("schemas", {})
        assert "TextSearchResponse" in schemas
        assert "TextSearchResultItem" in schemas

    def test_137_openapi_has_document_list_response(self):
        """OpenAPI schema should define DocumentListResponse."""
        resp = client.get("/openapi.json")
        schemas = resp.json().get("components", {}).get("schemas", {})
        assert "DocumentListResponse" in schemas
        assert "DocumentListItem" in schemas

    def test_138_openapi_has_document_detail_response(self):
        """OpenAPI schema should define DocumentDetailResponse."""
        resp = client.get("/openapi.json")
        schemas = resp.json().get("components", {}).get("schemas", {})
        assert "DocumentDetailResponse" in schemas

    def test_139_openapi_has_search_response(self):
        """OpenAPI schema should define SearchResponse and SearchResultItem."""
        resp = client.get("/openapi.json")
        schemas = resp.json().get("components", {}).get("schemas", {})
        assert "SearchResponse" in schemas
        assert "SearchResultItem" in schemas

    def test_140_openapi_has_text_ask_response(self):
        """OpenAPI schema should define TextAskResponse."""
        resp = client.get("/openapi.json")
        schemas = resp.json().get("components", {}).get("schemas", {})
        assert "TextAskResponse" in schemas
        assert "TextAskSource" in schemas


# ===========================================================================
# 11. REGISTRY PAGINATION TESTS
# ===========================================================================


class TestRegistryPagination:
    """Tests that registry endpoints include meta."""

    def setup_method(self):
        _reset_rate_limiter()

    def test_141_registry_documents_has_meta(self):
        """GET /registry/documents must include meta block."""
        resp = client.get(f"{REG_DOCS}/documents")
        assert_ok(resp)
        data = resp.json()
        assert "data" in data
        assert "meta" in data, f"Missing meta in registry response: {data}"
        assert "total" in data["meta"]
        assert "page" in data["meta"]

    def test_142_registry_classifiers_has_meta(self):
        """GET /classifiers must include meta block."""
        resp = client.get(f"{REG}/classifiers")
        assert_ok(resp)
        data = resp.json()
        assert "data" in data
        assert "meta" in data, f"Missing meta in classifiers response: {data}"

    def test_143_registry_terminology_has_meta(self):
        """GET /terminology must include meta block."""
        resp = client.get(f"{REG}/terminology")
        assert_ok(resp)
        data = resp.json()
        assert "data" in data
        assert "meta" in data


# ===========================================================================
# 12. DOCUMENT-REGISTRY LINK TESTS (updated)
# ===========================================================================


class TestDocumentRegistryLink:
    """Tests for /documents ↔ /registry/documents link."""

    def setup_method(self):
        _reset_rate_limiter()

    def test_144_documents_have_doc_code(self):
        """GET /documents items should contain doc_code."""
        resp = client.get(f"{ORCH}/documents")
        data = resp.json()
        for item in data["items"]:
            assert "doc_code" in item, f"Missing doc_code in: {item}"

    def test_145_document_detail_has_source_type(self):
        """GET /documents/{id} should contain source_type."""
        resp = client.get(f"{ORCH}/documents/doc-001")
        data = resp.json()
        assert "source_type" in data
        assert "doc_code" in data

    def test_146_doc_code_links_to_registry(self):
        """doc_code from documents should match registry doc_code."""
        resp = client.get(f"{ORCH}/documents/doc-001")
        doc_data = resp.json()
        doc_code = doc_data.get("doc_code")
        if doc_code:
            # Search registry documents by doc_code
            resp = client.get(f"{REG_DOCS}/documents", params={"search": doc_code})
            assert_ok(resp)
            data = resp.json()
            if data["data"]:
                assert data["data"][0].get("doc_code") == doc_code
