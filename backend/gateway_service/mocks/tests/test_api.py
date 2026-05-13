"""
Comprehensive API tests for PKB Neuroassistant Mock Services.
Tests all 4 services through the unified gateway (port 8081).
"""

import os
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import pytest
from fastapi.testclient import TestClient

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


def get_token() -> str:
    resp = client.post(
        f"{AUTH}/token",
        json={"username": TEST_USER_EMAIL, "password": TEST_USER_PASS},
    )
    return resp.json().get("access_token", "")


def auth_header() -> dict:
    """Returns admin token for admin endpoint tests."""
    resp = client.post(
        f"{AUTH}/token",
        json={"username": "admin@example.com", "password": "admin123"},
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def engineer_header() -> dict:
    """Returns engineer token for RBAC-negative tests."""
    resp = client.post(
        f"{AUTH}/token",
        json={"username": "ivanov@example.com", "password": "secret123"},
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def assert_ok(resp, status_code=200):
    assert resp.status_code == status_code, (
        f"Expected {status_code}, got {resp.status_code}: {resp.text[:200]}"
    )


def assert_paginated(data):
    assert "meta" in data, f"Missing meta: {data}"
    assert "total" in data["meta"]
    assert "page" in data["meta"]
    assert "page_size" in data["meta"]


# ===========================================================================
# 1. AUTH SERVICE TESTS
# ===========================================================================


class TestAuthService:
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

    def test_2_login_invalid_password(self):
        resp = client.post(
            f"{AUTH}/token", json={"username": TEST_USER_EMAIL, "password": "wrong"}
        )
        assert resp.status_code == 401

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
            f"{BASE}/internal/auth/validate", json={"access_token": "valid_token_12345"}
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
    def test_23_list_documents(self):
        resp = client.get(f"{ORCH}/documents")
        assert_ok(resp)
        data = resp.json()
        assert "items" in data
        assert "summary" in data
        assert_paginated(data)

    def test_24_list_documents_filter_type(self):
        resp = client.get(
            f"{ORCH}/documents", params={"document_type": "specification"}
        )
        assert_ok(resp)
        for doc in resp.json()["items"]:
            assert doc["document_type"] == "specification"

    def test_25_list_documents_filter_status(self):
        resp = client.get(f"{ORCH}/documents", params={"status": "completed"})
        assert_ok(resp)

    def test_26_get_document(self):
        resp = client.get(f"{ORCH}/documents/doc-001")
        assert_ok(resp)
        assert resp.json()["document_id"] == "doc-001"

    def test_27_get_document_not_found(self):
        resp = client.get(f"{ORCH}/documents/nonexistent")
        assert resp.status_code == 404

    def test_28_document_status(self):
        resp = client.get(f"{ORCH}/documents/doc-001/status")
        assert_ok(resp)
        assert resp.json()["status"] == "completed"

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
        assert "queue" in resp.json()

    def test_36_post_search(self):
        resp = client.post(
            f"{ORCH}/documents/search", json={"query": "wall thickness", "top_k": 5}
        )
        assert_ok(resp)
        data = resp.json()
        assert "items" in data
        assert len(data["items"]) > 0

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

    def test_40_validate_compare(self):
        resp = client.post(
            f"{ORCH}/validate/compare", json={"project_document_id": "doc-001"}
        )
        assert_ok(resp, 202)
        assert "comparison_id" in resp.json()

    def test_41_get_comparison(self):
        create = client.post(
            f"{ORCH}/validate/compare", json={"project_document_id": "doc-001"}
        ).json()
        resp = client.get(f"{ORCH}/validate/compare/{create['comparison_id']}")
        assert_ok(resp)
        assert "match_status" in resp.json()

    def test_42_validate_checks(self):
        resp = client.post(
            f"{ORCH}/validate/checks", json={"project_document_ids": ["doc-001"]}
        )
        assert resp.status_code in (200, 202)

    def test_43_get_check_result(self):
        create = client.post(
            f"{ORCH}/validate/checks", json={"project_document_ids": ["doc-001"]}
        ).json()
        if "check_run_id" in create:
            resp = client.get(f"{ORCH}/validate/checks/{create['check_run_id']}")
            assert_ok(resp)

    def test_44_export_check(self):
        create = client.post(
            f"{ORCH}/validate/checks", json={"project_document_ids": ["doc-001"]}
        ).json()
        if "check_run_id" in create:
            resp = client.get(f"{ORCH}/validate/checks/{create['check_run_id']}/export")
            assert_ok(resp)

    def test_45_monitor_metrics(self):
        resp = client.get(f"{ORCH}/monitor/metrics")
        assert_ok(resp)
        data = resp.json()
        assert "control_metrics" in data
        assert "logs" in data

    def test_46_reprocess_document(self):
        resp = client.post(f"{ORCH}/documents/doc-001/reprocess", json={"mode": "full"})
        assert_ok(resp, 202)
        assert resp.json()["status"] == "queued"

    def test_47_upload_document(self):
        resp = client.post(
            f"{ORCH}/documents",
            data={"document_type": "specification", "title": "Test Doc"},
        )
        assert_ok(resp, 202)
        assert "document_id" in resp.json()

    def test_48_delete_document(self):
        create = client.post(
            f"{ORCH}/documents", data={"document_type": "drawing", "title": "To Delete"}
        ).json()
        doc_id = create["document_id"]
        resp = client.delete(f"{ORCH}/documents/{doc_id}")
        assert_ok(resp)
        resp = client.get(f"{ORCH}/documents/{doc_id}")
        assert resp.status_code == 404

    def test_49_health(self):
        resp = client.get(f"{ORCH}/system/health")
        assert_ok(resp)


# ===========================================================================
# 3. QUERY SERVICE TESTS
# ===========================================================================


class TestQueryService:
    def test_50_create_session(self):
        resp = client.post(
            f"{QUERY}/chat/sessions",
            json={"title": "Test Session", "document_ids": ["doc-001"]},
        )
        assert_ok(resp, 201)
        assert "session_id" in resp.json()

    def test_51_list_sessions(self):
        resp = client.get(f"{QUERY}/chat/sessions")
        assert_ok(resp)
        data = resp.json()
        assert "sessions" in data
        assert_paginated(data)

    def test_52_get_session(self):
        resp = client.get(f"{QUERY}/chat/sessions/sess-001")
        assert_ok(resp)
        assert resp.json()["session_id"] == "sess-001"

    def test_53_get_session_not_found(self):
        resp = client.get(f"{QUERY}/chat/sessions/nonexistent")
        assert resp.status_code == 404

    def test_54_update_session(self):
        resp = client.put(f"{QUERY}/chat/sessions/sess-002", json={"title": "Updated"})
        assert_ok(resp)
        assert resp.json()["title"] == "Updated"

    def test_55_send_message(self):
        resp = client.post(
            f"{QUERY}/chat/sessions/sess-001/messages",
            json={"content": "What is the wall thickness?"},
        )
        assert_ok(resp)
        data = resp.json()
        assert data["role"] == "assistant"
        assert "sources" in data

    def test_56_manage_context(self):
        resp = client.post(
            f"{QUERY}/chat/sessions/sess-001/context", json={"action": "clear_history"}
        )
        assert_ok(resp)
        assert resp.json()["status"] == "completed"

    def test_57_export_session(self):
        resp = client.post(
            f"{QUERY}/chat/sessions/sess-001/export", json={"format": "pdf"}
        )
        assert_ok(resp)
        assert "export_id" in resp.json()

    def test_58_feedback(self):
        resp = client.post(
            f"{QUERY}/chat/feedback",
            json={"session_id": "sess-001", "message_id": "msg-001", "rating": 5},
        )
        assert_ok(resp)
        assert resp.json()["saved"] is True

    def test_59_chat_history(self):
        resp = client.get(f"{QUERY}/chat/history")
        assert_ok(resp)
        data = resp.json()
        assert "items" in data
        assert_paginated(data)

    def test_60_export_history(self):
        resp = client.get(f"{QUERY}/chat/history/export", params={"format": "csv"})
        assert_ok(resp)

    def test_61_chat_ask(self):
        resp = client.post(
            f"{QUERY}/chat", json={"question": "What are the dimensions?"}
        )
        assert_ok(resp)
        assert "answer_id" in resp.json()

    def test_62_text_search(self):
        resp = client.post(
            f"{QUERY}/text/search", json={"text": "wall thickness", "top_k": 3}
        )
        assert_ok(resp)
        assert "results" in resp.json()

    def test_63_text_search_filtered(self):
        resp = client.post(
            f"{QUERY}/text/search",
            json={
                "text": "steel",
                "document_ids": ["doc-001"],
                "filters": {"document_type": "specification"},
            },
        )
        assert_ok(resp)

    def test_64_text_ask(self):
        resp = client.post(
            f"{QUERY}/text/ask", json={"text": "What material is the body made of?"}
        )
        assert_ok(resp)
        assert "answer" in resp.json()
        assert "sources" in resp.json()

    def test_65_delete_session(self):
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
    def test_66_list_classifiers(self):
        resp = client.get(f"{REG}/classifiers")
        assert_ok(resp)
        data = resp.json()
        assert "data" in data
        assert_paginated(data)

    def test_67_list_classifiers_search(self):
        resp = client.get(f"{REG}/classifiers", params={"search": "GOST"})
        assert_ok(resp)

    def test_68_get_classifier_tree(self):
        resp = client.get(f"{REG}/classifiers/tree")
        assert_ok(resp)
        assert "data" in resp.json()

    def test_69_get_classifier_node(self):
        resp = client.get(f"{REG}/classifiers/01")
        assert_ok(resp)
        assert resp.json()["data"]["code"] == "01"

    def test_70_get_classifier_not_found(self):
        resp = client.get(f"{REG}/classifiers/nonexistent")
        assert resp.status_code == 404

    def test_71_create_classifier(self):
        resp = client.post(
            f"{REG}/classifiers",
            json={
                "code": "99.999",
                "full_name": "Test Classifier",
                "doc_type": "normative",
            },
        )
        assert_ok(resp, 201)
        assert resp.json()["data"]["code"] == "99.999"

    def test_72_create_classifier_duplicate(self):
        resp = client.post(
            f"{REG}/classifiers",
            json={"code": "01", "full_name": "Dup", "doc_type": "normative"},
        )
        assert resp.status_code == 409

    def test_73_update_classifier(self):
        resp = client.put(
            f"{REG}/classifiers/01", json={"full_name": "Updated Standard"}
        )
        assert_ok(resp)
        assert resp.json()["data"]["full_name"] == "Updated Standard"

    def test_74_patch_classifier(self):
        resp = client.patch(f"{REG}/classifiers/02", json={"is_thematic": True})
        assert_ok(resp)

    def test_75_delete_classifier_with_children(self):
        resp = client.delete(f"{REG}/classifiers/01")
        assert resp.status_code == 409

    def test_76_import_classifiers(self):
        resp = client.post(
            f"{REG}/classifiers/import",
            json={
                "items": [
                    {
                        "code": "IMP.001",
                        "full_name": "Imported 1",
                        "doc_type": "normative",
                    }
                ]
            },
        )
        assert_ok(resp)
        assert resp.json()["data"]["inserted"] >= 1

    def test_77_list_terminology(self):
        resp = client.get(f"{REG}/terminology")
        assert_ok(resp)
        data = resp.json()
        assert "data" in data
        assert_paginated(data)

    def test_78_search_terminology(self):
        resp = client.get(f"{REG}/terminology", params={"search": "thickness"})
        assert_ok(resp)

    def test_79_get_term(self):
        resp = client.get(f"{REG}/terminology/t-001")
        assert_ok(resp)

    def test_80_get_term_not_found(self):
        resp = client.get(f"{REG}/terminology/nonexistent")
        assert resp.status_code == 404

    def test_81_create_term(self):
        resp = client.post(
            f"{REG}/terminology", json={"term": "Test Term", "source": "Test"}
        )
        assert_ok(resp, 201)

    def test_82_update_term(self):
        resp = client.put(
            f"{REG}/terminology/t-001", json={"context": "Updated context"}
        )
        assert_ok(resp)

    def test_83_delete_term(self):
        create = client.post(f"{REG}/terminology", json={"term": "Temp Term"}).json()
        term_id = create["data"]["term_id"]
        resp = client.delete(f"{REG}/terminology/{term_id}")
        assert_ok(resp)

    def test_84_normalize_term(self):
        resp = client.get(
            f"{REG}/terminology/normalize", params={"q": "Wall Thickness"}
        )
        assert_ok(resp)
        assert resp.json()["data"]["normalized"]

    def test_85_import_terminology(self):
        resp = client.post(
            f"{REG}/terminology/import",
            json={"items": [{"term": "Imported", "source": "Test"}]},
        )
        assert_ok(resp)

    def test_86_list_registry_docs(self):
        resp = client.get(f"{REG_DOCS}/documents")
        assert_ok(resp)
        assert "data" in resp.json()

    def test_87_get_registry_doc(self):
        resp = client.get(f"{REG_DOCS}/documents/rd-001")
        assert_ok(resp)

    def test_88_create_registry_doc(self):
        resp = client.post(
            f"{REG_DOCS}/documents",
            json={
                "title": "Test Doc",
                "doc_number": "TEST-001",
                "classifier_code": "01",
            },
        )
        assert_ok(resp, 201)

    def test_89_update_registry_doc(self):
        resp = client.put(
            f"{REG_DOCS}/documents/rd-001", json={"notes": "Updated notes"}
        )
        assert_ok(resp)

    def test_90_update_doc_status(self):
        resp = client.patch(
            f"{REG_DOCS}/documents/rd-002/status", json={"status": "obsolete"}
        )
        assert_ok(resp)

    def test_91_export_registry_docs(self):
        resp = client.get(f"{REG_DOCS}/documents/export", params={"format": "json"})
        assert_ok(resp)
        assert resp.json()["data"]["format"] == "json"

    def test_92_import_registry_docs(self):
        resp = client.post(
            f"{REG_DOCS}/documents/import",
            json=[
                {"title": "Imported", "doc_number": "IMP-001", "classifier_code": "01"}
            ],
        )
        assert_ok(resp)

    def test_93_delete_registry_doc(self):
        create = client.post(
            f"{REG_DOCS}/documents",
            json={
                "title": "To Delete",
                "doc_number": "DEL-001",
                "classifier_code": "01",
            },
        ).json()
        doc_id = create["data"]["doc_id"]
        resp = client.delete(f"{REG_DOCS}/documents/{doc_id}")
        assert_ok(resp)

    def test_94_get_stats(self):
        resp = client.get(f"{COMMON}/stats")
        assert_ok(resp)
        data = resp.json()["data"]
        assert "classifiers_total" in data

    def test_95_get_enums(self):
        resp = client.get(f"{COMMON}/enums")
        assert_ok(resp)
        assert "doc_type" in resp.json()["data"]


# ===========================================================================
# 5. GATEWAY TESTS
# ===========================================================================


class TestGateway:
    def test_96_health(self):
        resp = client.get(f"{BASE}/system/health")
        assert_ok(resp)
        assert resp.json()["status"] == "ok"

    def test_97_routing_auth(self):
        resp = client.post(
            f"{AUTH}/token",
            json={"username": "admin@example.com", "password": "admin123"},
        )
        assert_ok(resp)

    def test_98_routing_orchestrator(self):
        resp = client.get(f"{ORCH}/documents")
        assert_ok(resp)

    def test_99_routing_query(self):
        resp = client.get(f"{QUERY}/chat/sessions")
        assert_ok(resp)

    def test_100_routing_registry(self):
        resp = client.get(f"{REG}/classifiers")
        assert_ok(resp)

    def test_101_no_conflict_queue(self):
        resp = client.get(f"{ORCH}/documents/queue")
        assert_ok(resp)
        assert "queue" in resp.json()

    def test_102_no_conflict_search(self):
        resp = client.get(f"{ORCH}/documents/search", params={"q": "test", "top_k": 2})
        assert_ok(resp)

    def test_103_pagination_defaults(self):
        resp = client.get(f"{ORCH}/documents")
        meta = resp.json()["meta"]
        assert meta["page"] == 1
        assert meta["page_size"] == 50

    def test_104_pagination_custom(self):
        resp = client.get(f"{ORCH}/documents", params={"page": 1, "page_size": 3})
        assert resp.json()["meta"]["page_size"] == 3

    def test_105_no_route_conflict(self):
        # Verify /documents/queue is not caught by /documents/{doc_id}
        resp = client.get(f"{ORCH}/documents/queue")
        assert_ok(resp)
        assert "queue" in resp.json()
        # Verify /documents/search is not caught by /documents/{doc_id}
        resp = client.get(f"{ORCH}/documents/search", params={"q": "test"})
        assert_ok(resp)
        assert "items" in resp.json()


# ===========================================================================
# 7. NEW FUNCTIONALITY TESTS (Review fixes)
# ===========================================================================


class TestAuthMeBinding:
    """Tests for GET /auth/me binding to JWT token (Review #1)."""

    def test_106_me_returns_correct_user_by_token(self):
        """Login as kuznetsov, /auth/me should return kuznetsov's profile."""
        # Login as kuznetsov (unmodified user, always engineer)
        resp = client.post(
            f"{AUTH}/token",
            json={"username": "kuznetsov@example.com", "password": "secret789"},
        )
        token = resp.json()["access_token"]

        # GET /auth/me with kuznetsov's token
        resp = client.get(f"{AUTH}/me", headers={"Authorization": f"Bearer {token}"})
        assert_ok(resp)
        data = resp.json()
        assert data["user_id"] == "u-004", (
            f"Expected kuznetsov (u-004), got {data['user_id']}"
        )
        assert data["full_name"] == "Кузнецов Дмитрий Олегович"
        assert data["role"] == "engineer", (
            f"Expected engineer, got '{data['role']}'. "
            f"User data: user_id={data.get('user_id')}, "
            f"full_name={data.get('full_name')}"
        )

    def test_107_me_returns_admin_user(self):
        """Login as admin, /auth/me should return admin."""
        resp = client.post(
            f"{AUTH}/token",
            json={"username": "admin@example.com", "password": "admin123"},
        )
        token = resp.json()["access_token"]

        resp = client.get(f"{AUTH}/me", headers={"Authorization": f"Bearer {token}"})
        assert_ok(resp)
        data = resp.json()
        assert data["user_id"] == "u-003", (
            f"Expected admin (u-003), got {data['user_id']}"
        )
        assert data["role"] == "system_admin"
        assert "admin" in data.get("available_tabs", [])

    def test_108_me_returns_401_without_token(self):
        """GET /auth/me without token should return 401."""
        resp = client.get(f"{AUTH}/me")
        assert resp.status_code == 401
        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] == "UNAUTHORIZED"

    def test_109_me_returns_401_with_invalid_token(self):
        """GET /auth/me with invalid token should return 401."""
        resp = client.get(
            f"{AUTH}/me",
            headers={"Authorization": "Bearer invalid_token_xxx"},
        )
        assert resp.status_code == 401
        data = resp.json()
        assert "error" in data


class TestRBAC:
    """Tests for RBAC on /admin/* endpoints (Review #2)."""

    def _get_admin_token(self) -> str:
        resp = client.post(
            f"{AUTH}/token",
            json={"username": "admin@example.com", "password": "admin123"},
        )
        return resp.json()["access_token"]

    def _get_engineer_token(self) -> str:
        resp = client.post(
            f"{AUTH}/token",
            json={"username": "ivanov@example.com", "password": "secret123"},
        )
        return resp.json()["access_token"]

    def test_110_admin_users_401_without_token(self):
        """GET /admin/users without token → 401."""
        resp = client.get(f"{ADMIN}/users")
        assert resp.status_code == 401
        data = resp.json()
        assert data["error"]["code"] == "UNAUTHORIZED"

    def test_111_admin_users_403_for_engineer(self):
        """GET /admin/users as engineer → 403."""
        token = self._get_engineer_token()
        resp = client.get(
            f"{ADMIN}/users", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 403
        data = resp.json()
        assert data["error"]["code"] == "FORBIDDEN"

    def test_112_admin_users_200_for_admin(self):
        """GET /admin/users as system_admin → 200."""
        token = self._get_admin_token()
        resp = client.get(
            f"{ADMIN}/users", headers={"Authorization": f"Bearer {token}"}
        )
        assert_ok(resp)
        assert "users" in resp.json()

    def test_113_admin_roles_403_for_engineer(self):
        """GET /admin/roles as engineer → 403."""
        token = self._get_engineer_token()
        resp = client.get(
            f"{ADMIN}/roles", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 403

    def test_114_admin_roles_200_for_admin(self):
        """POST /admin/roles as admin → 201."""
        token = self._get_admin_token()
        resp = client.post(
            f"{ADMIN}/roles",
            json={"name": "RBAC Test Role", "permissions": ["test:read"]},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert_ok(resp, 201)

    def test_115_admin_audit_403_for_knowledge_admin(self):
        """GET /admin/audit as knowledge_admin → 403."""
        resp = client.post(
            f"{AUTH}/token",
            json={"username": "petrova@example.com", "password": "secret456"},
        )
        token = resp.json()["access_token"]
        resp = client.get(
            f"{ADMIN}/audit", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 403

    def test_116_admin_endpoints_all_blocked_for_non_admin(self):
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


class TestErrorFormat:
    """Tests for unified error format (Review #3)."""

    def test_117_error_format_404(self):
        """404 error should use {error: {code, message, details}} format."""
        resp = client.get(f"{ORCH}/documents/nonexistent_doc_xxx")
        assert resp.status_code == 404
        data = resp.json()
        assert "error" in data, f"Missing 'error' wrapper: {data}"
        assert "code" in data["error"]
        assert "message" in data["error"]
        assert "details" in data["error"]
        assert data["error"]["code"] in ("NOT_FOUND", "DOCUMENT_NOT_FOUND"), (
            f"Expected NOT_FOUND or DOCUMENT_NOT_FOUND, got {data['error']['code']}"
        )

    def test_118_error_format_401(self):
        """401 error should use wrapped format."""
        resp = client.get(f"{AUTH}/me")
        assert resp.status_code == 401
        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] == "UNAUTHORIZED"

    def test_119_error_format_403(self):
        """403 error should use wrapped format."""
        token = client.post(
            f"{AUTH}/token",
            json={"username": "ivanov@example.com", "password": "secret123"},
        ).json()["access_token"]
        resp = client.get(
            f"{ADMIN}/users", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 403
        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] == "FORBIDDEN"

    def test_120_error_format_422_validation(self):
        """422 validation error should use wrapped format."""
        # Omit required 'password' field to trigger validation error
        resp = client.post(
            f"{AUTH}/token",
            json={"username": "test"},  # missing required 'password' field
        )
        assert resp.status_code == 422, (
            f"Expected 422, got {resp.status_code}: {resp.text[:200]}"
        )
        data = resp.json()
        assert "error" in data, f"Missing 'error' wrapper: {data}"
        assert data["error"]["code"] in ("VALIDATION_ERROR", "VALIDATION_FAILED")


class TestValidateChecksExtended:
    """Extended tests for POST /validate/checks (Review #5, #6)."""

    def test_121_validate_checks_returns_200(self):
        """POST /validate/checks should return 200 (not 202)."""
        resp = client.post(
            f"{ORCH}/validate/checks",
            json={"project_document_ids": ["doc-001"]},
        )
        assert_ok(resp)  # expects 200

    def test_122_validate_checks_has_check_run_id(self):
        """Response must contain check_run_id."""
        resp = client.post(
            f"{ORCH}/validate/checks",
            json={"project_document_ids": ["doc-001"]},
        )
        data = resp.json()
        assert "check_run_id" in data, f"Missing check_run_id: {data}"
        assert data["check_run_id"].startswith("check-")

    def test_123_validate_checks_has_summary(self):
        """Response must contain summary with ok/warning/error counts."""
        resp = client.post(
            f"{ORCH}/validate/checks",
            json={"project_document_ids": ["doc-001"]},
        )
        data = resp.json()
        assert "summary" in data, f"Missing summary: {data}"
        summary = data["summary"]
        assert "ok" in summary
        assert "warning" in summary
        assert "error" in summary

    def test_124_validate_checks_has_created_at(self):
        """Response must contain created_at."""
        resp = client.post(
            f"{ORCH}/validate/checks",
            json={"project_document_ids": ["doc-001"]},
        )
        data = resp.json()
        assert "created_at" in data, f"Missing created_at: {data}"

    def test_125_validate_checks_items_have_match_status(self):
        """Each item in items[] must have match_status field."""
        resp = client.post(
            f"{ORCH}/validate/checks",
            json={"project_document_ids": ["doc-001"]},
        )
        data = resp.json()
        assert "items" in data
        for item in data["items"]:
            assert "match_status" in item, f"Missing match_status in item: {item}"
            assert item["match_status"] in (
                "match",
                "mismatch",
                "partial_match",
            ), f"Invalid match_status: {item['match_status']}"

    def test_126_validate_checks_status_is_completed(self):
        """Overall check status should be 'completed'."""
        resp = client.post(
            f"{ORCH}/validate/checks",
            json={"project_document_ids": ["doc-001"]},
        )
        data = resp.json()
        assert data["status"] == "completed"

    def test_127_validate_checks_items_have_correct_statuses(self):
        """Item statuses should be from check_result_status enum."""
        resp = client.post(
            f"{ORCH}/validate/checks",
            json={"project_document_ids": ["doc-001"]},
        )
        data = resp.json()
        valid_statuses = {"ok", "warning", "error"}
        for item in data["items"]:
            assert item["status"] in valid_statuses, f"Invalid status: {item['status']}"


class TestDocumentRegistryLink:
    """Tests for /documents ↔ /registry/documents link (Review #11)."""

    def test_128_documents_have_registry_doc_id(self):
        """GET /documents items should contain registry_doc_id."""
        resp = client.get(f"{ORCH}/documents")
        data = resp.json()
        for item in data["items"]:
            assert "registry_doc_id" in item, f"Missing registry_doc_id in: {item}"

    def test_129_document_detail_has_registry_doc_id(self):
        """GET /documents/{id} should contain registry_doc_id."""
        resp = client.get(f"{ORCH}/documents/doc-001")
        data = resp.json()
        assert "registry_doc_id" in data
        assert data["registry_doc_id"] == "rd-001"

    def test_130_registry_doc_id_links_to_registry(self):
        """registry_doc_id from documents should match registry doc_id."""
        resp = client.get(f"{ORCH}/documents/doc-002")
        doc_data = resp.json()
        reg_id = doc_data.get("registry_doc_id")
        if reg_id:
            resp = client.get(f"{REG_DOCS}/documents/{reg_id}")
            assert_ok(resp)
            assert resp.json()["data"]["doc_id"] == reg_id


class TestLoginUsernameAndEmail:
    """Tests for login with username and email fields (Review #8)."""

    def test_131_login_with_username_full_email(self):
        """Login with username=full email should work."""
        resp = client.post(
            f"{AUTH}/token",
            json={"username": "ivanov@example.com", "password": "secret123"},
        )
        assert_ok(resp)
        assert "access_token" in resp.json()

    def test_132_login_with_username_part(self):
        """Login with username=ivanov (without domain) should work."""
        resp = client.post(
            f"{AUTH}/token",
            json={"username": "ivanov", "password": "secret123"},
        )
        assert_ok(resp)
        assert "access_token" in resp.json()

    def test_133_login_with_email_field(self):
        """Login with email field should also work."""
        resp = client.post(
            f"{AUTH}/token",
            json={"username": "petrova@example.com", "password": "secret456"},
        )
        assert_ok(resp)
        assert "access_token" in resp.json()

    def test_134_login_invalid_credentials(self):
        """Invalid credentials should return 401 with error wrapper."""
        resp = client.post(
            f"{AUTH}/token",
            json={"username": "ivanov@example.com", "password": "wrong_password"},
        )
        assert resp.status_code == 401
        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] == "UNAUTHORIZED"


class TestResponseModels:
    """Tests that response_model is present (OpenAPI schema check, Review #7)."""

    def test_135_openapi_has_chat_response_schema(self):
        """OpenAPI schema should define ChatResponse."""
        resp = client.get("/openapi.json")
        assert_ok(resp)
        schemas = resp.json().get("components", {}).get("schemas", {})
        assert "ChatResponse" in schemas, "Missing ChatResponse schema"
        assert "AnswerItem" in schemas, "Missing AnswerItem schema"

    def test_136_openapi_has_check_result_schema(self):
        """OpenAPI schema should define CheckResultResponse."""
        resp = client.get("/openapi.json")
        schemas = resp.json().get("components", {}).get("schemas", {})
        assert "CheckResultResponse" in schemas
        assert "CheckItem" in schemas

    def test_137_openapi_has_token_response(self):
        """OpenAPI schema should define TokenResponse."""
        resp = client.get("/openapi.json")
        schemas = resp.json().get("components", {}).get("schemas", {})
        assert "TokenResponse" in schemas

    def test_138_openapi_has_user_profile_response(self):
        """OpenAPI schema should define UserProfileResponse."""
        resp = client.get("/openapi.json")
        schemas = resp.json().get("components", {}).get("schemas", {})
        assert "UserProfileResponse" in schemas

    def test_139_openapi_has_text_search_response(self):
        """OpenAPI schema should define TextSearchResponse."""
        resp = client.get("/openapi.json")
        schemas = resp.json().get("components", {}).get("schemas", {})
        assert "TextSearchResponse" in schemas

    def test_140_openapi_has_document_list_response(self):
        """OpenAPI schema should define DocumentListResponse."""
        resp = client.get("/openapi.json")
        schemas = resp.json().get("components", {}).get("schemas", {})
        assert "DocumentListResponse" in schemas


class TestRegistryPagination:
    """Tests that registry endpoints include meta (Review #4)."""

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
