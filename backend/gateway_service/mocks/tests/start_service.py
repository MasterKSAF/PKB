import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient

from mocks.auth_service.main import app as auth_app, _rate_limits as auth_rate_limits
from mocks.orchestrator_service.main import app as orch_app
from mocks.query_service.main import app as query_app
from mocks.registry_service.main import app as reg_app

auth_client = TestClient(auth_app)
orch_client = TestClient(orch_app)
query_client = TestClient(query_app)
reg_client = TestClient(reg_app)

BASE = "/api/v1"

def reset_rate_limiter():
    auth_rate_limits.clear()

def auth_header_admin():
    resp = auth_client.post(
        f"{BASE}/auth/token",
        json={"username": "admin@example.com", "password": "admin123"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def auth_header_engineer():
    resp = auth_client.post(
        f"{BASE}/auth/token",
        json={"username": "ivanov@example.com", "password": "secret123"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

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
    def setup_method(self):
        reset_rate_limiter()

    def test_1_login_success(self):
        resp = auth_client.post(
            f"{BASE}/auth/token",
            json={"username": "ivanov@example.com", "password": "secret123"},
        )
        assert_ok(resp)
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 3600

    def test_2_login_invalid_password(self):
        resp = auth_client.post(
            f"{BASE}/auth/token",
            json={"username": "ivanov@example.com", "password": "wrong"},
        )
        assert resp.status_code == 401

    def test_3_refresh_token(self):
        login = auth_client.post(
            f"{BASE}/auth/token",
            json={"username": "ivanov@example.com", "password": "secret123"},
        ).json()
        resp = auth_client.post(
            f"{BASE}/auth/refresh",
            json={"refresh_token": login["refresh_token"]},
        )
        assert_ok(resp)
        assert "access_token" in resp.json()

    def test_4_revoke_token(self):
        login = auth_client.post(
            f"{BASE}/auth/token",
            json={"username": "ivanov@example.com", "password": "secret123"},
        ).json()
        resp = auth_client.post(
            f"{BASE}/auth/revoke",
            json={"refresh_token": login["refresh_token"]},
        )
        assert_ok(resp)
        assert resp.json()["message"] == "Токен отозван"

    def test_5_get_me(self):
        resp = auth_client.get(f"{BASE}/auth/me", headers=auth_header_engineer())
        assert_ok(resp)
        data = resp.json()
        assert data["user_id"] == "u-001"
        assert "full_name" in data
        assert "permissions" in data

    def test_6_list_users(self):
        resp = auth_client.get(
            f"{BASE}/admin/users", params={"page": 1, "page_size": 3}, headers=auth_header_admin()
        )
        assert_ok(resp)
        data = resp.json()
        assert "users" in data
        assert_paginated(data)

    def test_7_list_users_filter_role(self):
        resp = auth_client.get(
            f"{BASE}/admin/users", params={"role": "engineer"}, headers=auth_header_admin()
        )
        assert_ok(resp)
        for u in resp.json()["users"]:
            assert "engineer" in u.get("roles", [])

    def test_8_list_users_search(self):
        resp = auth_client.get(
            f"{BASE}/admin/users", params={"search": "Ivanov"}, headers=auth_header_admin()
        )
        assert_ok(resp)

    def test_9_create_user(self):
        resp = auth_client.post(
            f"{BASE}/admin/users",
            json={"email": "new@test.com", "full_name": "New User", "password": "Pass123!", "roles": ["engineer"]},
            headers=auth_header_admin(),
        )
        assert_ok(resp, 201)
        assert resp.json()["email"] == "new@test.com"

    def test_10_create_user_duplicate(self):
        resp = auth_client.post(
            f"{BASE}/admin/users",
            json={"email": "ivanov@example.com", "full_name": "Dup", "password": "Pass123!", "roles": ["engineer"]},
            headers=auth_header_admin(),
        )
        assert resp.status_code == 409

    def test_11_get_user(self):
        resp = auth_client.get(f"{BASE}/admin/users/u-001", headers=auth_header_admin())
        assert_ok(resp)
        assert resp.json()["user_id"] == "u-001"

    def test_12_get_user_not_found(self):
        resp = auth_client.get(f"{BASE}/admin/users/nonexistent", headers=auth_header_admin())
        assert resp.status_code == 404

    def test_13_update_user(self):
        resp = auth_client.put(
            f"{BASE}/admin/users/u-001",
            json={"position": "Lead Engineer"},
            headers=auth_header_admin(),
        )
        assert_ok(resp)
        assert resp.json()["position"] == "Lead Engineer"

    def test_14_patch_user_role(self):
        resp = auth_client.patch(
            f"{BASE}/admin/users/u-002", json={"role": "system_admin"}, headers=auth_header_admin()
        )
        assert_ok(resp)

    def test_15_deactivate_user(self):
        create = auth_client.post(
            f"{BASE}/admin/users",
            json={"email": "todel@test.com", "full_name": "To Del", "password": "Pass123!", "roles": ["engineer"]},
            headers=auth_header_admin(),
        ).json()
        resp = auth_client.delete(
            f"{BASE}/admin/users/{create['user_id']}", headers=auth_header_admin()
        )
        assert_ok(resp)
        assert resp.json()["is_active"] is False

    def test_16_list_roles(self):
        resp = auth_client.get(f"{BASE}/admin/roles", headers=auth_header_admin())
        assert_ok(resp)
        assert "roles" in resp.json()

    def test_17_create_role(self):
        resp = auth_client.post(
            f"{BASE}/admin/roles",
            json={"name": "Test Role", "permissions": ["test:read"]},
            headers=auth_header_admin(),
        )
        assert_ok(resp, 201)

    def test_18_list_audit(self):
        resp = auth_client.get(f"{BASE}/admin/audit", headers=auth_header_admin())
        assert_ok(resp)
        data = resp.json()
        assert "events" in data
        assert_paginated(data)

    def test_19_internal_validate_token(self):
        resp = auth_client.post(
            f"{BASE}/internal/auth/validate",
            json={"access_token": auth_header_engineer()["Authorization"].split(" ")[1]},
        )
        assert_ok(resp)
        assert resp.json()["valid"] is True

    def test_20_internal_validate_invalid(self):
        resp = auth_client.post(
            f"{BASE}/internal/auth/validate", json={"access_token": "short"}
        )
        assert resp.status_code == 401

    def test_21_error_format_401(self):
        resp = auth_client.get(f"{BASE}/auth/me")
        assert resp.status_code == 401
        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] == "UNAUTHORIZED"

# ===========================================================================
# 2. ORCHESTRATOR SERVICE TESTS
# ===========================================================================
class TestOrchestratorService:
    def setup_method(self):
        reset_rate_limiter()

    def test_22_list_documents(self):
        resp = orch_client.get(f"{BASE}/documents")
        assert_ok(resp)
        data = resp.json()
        assert "items" in data
        assert "summary" in data
        assert_paginated(data)

    def test_23_get_document(self):
        resp = orch_client.get(f"{BASE}/documents/doc-001")
        assert_ok(resp)
        data = resp.json()
        assert data["document_id"] == "doc-001"
        assert "source_type" in data

    def test_24_get_document_not_found(self):
        resp = orch_client.get(f"{BASE}/documents/nonexistent")
        assert resp.status_code == 404
        assert "error" in resp.json()

    def test_25_document_status(self):
        resp = orch_client.get(f"{BASE}/documents/doc-001/status")
        assert_ok(resp)
        data = resp.json()
        assert "pipeline" in data
        assert "formation" in data["pipeline"]

    def test_26_document_file(self):
        resp = orch_client.get(f"{BASE}/documents/doc-001/file")
        assert_ok(resp)
        assert "file_url" in resp.json()

    def test_27_document_pages(self):
        resp = orch_client.get(f"{BASE}/documents/doc-001/pages")
        assert_ok(resp)
        assert "pages" in resp.json()

    def test_28_page_detail(self):
        resp = orch_client.get(f"{BASE}/documents/doc-001/pages/1")
        assert_ok(resp)
        assert "blocks" in resp.json()

    def test_29_page_preview(self):
        resp = orch_client.get(f"{BASE}/documents/doc-001/pages/1/preview")
        assert_ok(resp)
        assert "preview_url" in resp.json()

    def test_30_page_text(self):
        resp = orch_client.get(f"{BASE}/documents/doc-001/pages/1/text")
        assert_ok(resp)
        assert "full_text" in resp.json()

    def test_31_document_parameters(self):
        resp = orch_client.get(f"{BASE}/documents/doc-001/parameters")
        assert_ok(resp)
        assert "parameters" in resp.json()

    def test_32_document_queue(self):
        resp = orch_client.get(f"{BASE}/documents/queue")
        assert_ok(resp)
        data = resp.json()
        assert "queue" in data

    def test_33_post_search(self):
        resp = orch_client.post(
            f"{BASE}/documents/search", json={"query": "wall thickness", "top_k": 5}
        )
        assert_ok(resp)
        data = resp.json()
        assert "items" in data
        assert len(data["items"]) > 0

    def test_34_get_search(self):
        resp = orch_client.get(f"{BASE}/documents/search", params={"q": "test", "top_k": 3})
        assert_ok(resp)
        assert len(resp.json()["items"]) > 0

    def test_35_document_errors(self):
        resp = orch_client.get(f"{BASE}/documents/doc-001/errors")
        assert_ok(resp)
        assert "errors" in resp.json()

    def test_36_monitor_metrics(self):
        resp = orch_client.get(f"{BASE}/monitor/metrics")
        assert_ok(resp)
        data = resp.json()
        assert "control_metrics" in data

    def test_37_reprocess_document(self):
        resp = orch_client.post(f"{BASE}/documents/doc-001/reprocess", json={"mode": "full"})
        assert_ok(resp, 202)
        assert resp.json()["status"] == "parsing"

    def test_38_upload_document(self):
        resp = orch_client.post(
            f"{BASE}/documents",
            files={"file": ("test.pdf", b"%PDF-1.4 mock content", "application/pdf")},
        )
        assert_ok(resp, 202)
        data = resp.json()
        assert "task_id" in data

    def test_39_delete_document(self):
        # Удаляем doc-001 напрямую
        resp = orch_client.delete(f"{BASE}/documents/doc-001")
        assert_ok(resp)
        assert resp.json()["document_id"] == "doc-001"

    def test_40_add_document_version(self):
        resp = orch_client.post(
            f"{BASE}/documents/doc-001/versions",
            files={"file": ("v2.pdf", b"version 2", "application/pdf")},
        )
        assert_ok(resp, 201)
        data = resp.json()
        assert "version_id" in data

    def test_41_list_document_versions(self):
        resp = orch_client.get(f"{BASE}/documents/doc-001/versions")
        assert_ok(resp)
        assert "versions" in resp.json()

    def test_42_approve_document(self):
        resp = orch_client.post(f"{BASE}/documents/doc-001/approve")
        assert_ok(resp, 202)
        assert resp.json()["status"] == "approved"

    def test_43_document_history(self):
        resp = orch_client.get(f"{BASE}/documents/doc-001/history")
        assert_ok(resp)
        assert "history" in resp.json()

    def test_44_health(self):
        resp = orch_client.get(f"{BASE}/system/health")
        assert_ok(resp)
        assert resp.json()["status"] == "ok"

# ===========================================================================
# 3. QUERY SERVICE TESTS
# ===========================================================================
class TestQueryService:
    def setup_method(self):
        reset_rate_limiter()

    def test_45_create_session(self):
        resp = query_client.post(
            f"{BASE}/chat/sessions",
            json={"title": "Test Session", "document_ids": ["doc-001"]},
        )
        assert_ok(resp, 201)
        assert "session_id" in resp.json()

    def test_46_list_sessions(self):
        resp = query_client.get(f"{BASE}/chat/sessions")
        assert_ok(resp)
        data = resp.json()
        assert "sessions" in data
        assert_paginated(data)

    def test_47_get_session(self):
        resp = query_client.get(f"{BASE}/chat/sessions/sess-001")
        assert_ok(resp)
        assert resp.json()["session_id"] == "sess-001"

    def test_48_get_session_not_found(self):
        resp = query_client.get(f"{BASE}/chat/sessions/nonexistent")
        assert resp.status_code == 404

    def test_49_update_session(self):
        resp = query_client.put(
            f"{BASE}/chat/sessions/sess-001", json={"title": "Updated"}
        )
        assert_ok(resp)
        assert resp.json()["title"] == "Updated"

    def test_50_send_message(self):
        resp = query_client.post(
            f"{BASE}/chat/sessions/sess-001/messages",
            json={"content": "What is the wall thickness?"},
        )
        assert_ok(resp)
        data = resp.json()
        assert data["role"] == "assistant"
        assert "content" in data

    def test_51_manage_context(self):
        resp = query_client.post(
            f"{BASE}/chat/sessions/sess-001/context",
            json={"action": "clear_history"},
        )
        assert_ok(resp)
        assert resp.json()["status"] == "completed"

    def test_52_export_session(self):
        resp = query_client.post(
            f"{BASE}/chat/sessions/sess-001/export", json={"format": "pdf"}
        )
        assert_ok(resp)
        assert "export_id" in resp.json()

    def test_53_feedback(self):
        resp = query_client.post(
            f"{BASE}/chat/feedback",
            json={
                "session_id": "sess-001",
                "message_id": "msg-001",
                "rating": 5,
                "answer_id": "ans-001",
                "useful": True,
                "opened_citation_ids": ["cit-001"],
            },
        )
        assert_ok(resp)
        assert resp.json()["saved"] is True

    def test_54_chat_history(self):
        resp = query_client.get(f"{BASE}/chat/history")
        assert_ok(resp)
        data = resp.json()
        assert "items" in data
        assert_paginated(data)

    def test_55_export_history(self):
        resp = query_client.get(f"{BASE}/chat/history/export", params={"format": "csv"})
        assert_ok(resp)

    def test_56_chat_ask_completed(self):
        resp = query_client.post(
            f"{BASE}/chat", json={"question": "What are the dimensions?"}
        )
        assert_ok(resp)
        data = resp.json()
        assert data["scenario"] == "completed"
        assert "answer_items" in data

    def test_56b_chat_ask_needs_clarification(self):
        resp = query_client.post(
            f"{BASE}/chat", json={"question": "This is ambiguous"}
        )
        assert_ok(resp)
        assert resp.json()["scenario"] == "needs_clarification"

    def test_56c_chat_ask_conflict(self):
        resp = query_client.post(
            f"{BASE}/chat", json={"question": "There is a conflict in norms"}
        )
        assert_ok(resp)
        assert resp.json()["scenario"] == "conflict"

    def test_57_text_search(self):
        resp = query_client.post(
            f"{BASE}/text/search", json={"text": "wall thickness", "top_k": 3}
        )
        assert_ok(resp)
        data = resp.json()
        assert "results" in data

    def test_58_text_search_filtered(self):
        resp = query_client.post(
            f"{BASE}/text/search",
            json={"text": "steel", "document_ids": ["doc-001"]},
        )
        assert_ok(resp)

    def test_59_text_ask(self):
        resp = query_client.post(
            f"{BASE}/text/ask", json={"text": "What material is the body made of?"}
        )
        assert_ok(resp)
        data = resp.json()
        assert "answer" in data
        assert "sources" in data

    def test_60_delete_session(self):
        create = query_client.post(
            f"{BASE}/chat/sessions", json={"title": "To Delete"}
        ).json()
        sess_id = create["session_id"]
        resp = query_client.delete(f"{BASE}/chat/sessions/{sess_id}")
        assert_ok(resp)
        resp = query_client.get(f"{BASE}/chat/sessions/{sess_id}")
        assert resp.status_code == 404

# ===========================================================================
# 4. REGISTRY SERVICE TESTS
# ===========================================================================
class TestRegistryService:
    def setup_method(self):
        reset_rate_limiter()

    def test_61_list_classifiers(self):
        resp = reg_client.get(f"{BASE}/classifiers")
        assert_ok(resp)
        data = resp.json()
        assert "data" in data
        assert_paginated(data)

    def test_62_get_classifier_tree(self):
        resp = reg_client.get(f"{BASE}/classifiers/tree")
        assert_ok(resp)
        assert "data" in resp.json()

    def test_63_get_classifier_node(self):
        resp = reg_client.get(f"{BASE}/classifiers/47")
        assert_ok(resp)
        assert resp.json()["data"]["code"] == "47"

    def test_64_get_classifier_not_found(self):
        resp = reg_client.get(f"{BASE}/classifiers/nonexistent")
        assert resp.status_code == 404

    def test_65_create_classifier(self):
        resp = reg_client.post(
            f"{BASE}/classifiers",
            json={
                "classifier_system": "MKS",
                "code": "99.999",
                "full_name": "Test",
                "status": "active",
            },
        )
        assert_ok(resp, 201)
        assert resp.json()["data"]["code"] == "99.999"

    def test_66_create_classifier_duplicate(self):
        resp = reg_client.post(
            f"{BASE}/classifiers",
            json={"classifier_system": "MKS", "code": "47", "full_name": "Dup", "status": "active"},
        )
        assert resp.status_code == 409

    def test_67_update_classifier(self):
        resp = reg_client.put(
            f"{BASE}/classifiers/47", json={"full_name": "Updated"}
        )
        assert_ok(resp)
        assert resp.json()["data"]["full_name"] == "Updated"

    def test_68_patch_classifier(self):
        resp = reg_client.patch(f"{BASE}/classifiers/47", json={"parent_code": None})
        assert_ok(resp)

    def test_69_delete_classifier_with_children(self):
        resp = reg_client.delete(f"{BASE}/classifiers/47")
        assert resp.status_code == 409

    def test_70_import_classifiers(self):
        resp = reg_client.post(
            f"{BASE}/classifiers/import",
            json=[
                {
                    "classifier_system": "MKS",
                    "code": "IMP.001",
                    "full_name": "Imported",
                    "status": "active",
                }
            ],
        )
        assert_ok(resp)
        assert resp.json()["data"]["inserted"] >= 1

    def test_71_list_terminology(self):
        resp = reg_client.get(f"{BASE}/terminology")
        assert_ok(resp)
        data = resp.json()
        assert "data" in data
        assert_paginated(data)

    def test_72_get_term(self):
        resp = reg_client.get(f"{BASE}/terminology/t-001")
        assert_ok(resp)
        assert "raw_term" in resp.json()["data"]

    def test_73_get_term_not_found(self):
        resp = reg_client.get(f"{BASE}/terminology/nonexistent")
        assert resp.status_code == 404

    def test_74_create_term(self):
        resp = reg_client.post(
            f"{BASE}/terminology",
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
        assert resp.json()["data"]["raw_term"] == "Test Term"

    def test_75_update_term(self):
        resp = reg_client.put(
            f"{BASE}/terminology/t-001", json={"definition": "Updated"}
        )
        assert_ok(resp)

    def test_76_delete_term(self):
        create = reg_client.post(
            f"{BASE}/terminology",
            json={
                "raw_term": "Temp",
                "term_type": "preferred",
                "is_case_sensitive": False,
                "is_blocked": False,
                "synonyms": [],
                "related_docs": [],
            },
        ).json()
        term_id = create["data"]["id"]
        resp = reg_client.delete(f"{BASE}/terminology/{term_id}")
        assert_ok(resp)

    def test_77_normalize_term(self):
        resp = reg_client.get(f"{BASE}/terminology/normalize", params={"term": "GOST"})
        assert_ok(resp)
        data = resp.json()["data"]
        assert "normalized_value" in data

    def test_78_import_terminology(self):
        resp = reg_client.post(
            f"{BASE}/terminology/import",
            json=[
                {
                    "raw_term": "ImportedTerm",
                    "term_type": "preferred",
                    "is_case_sensitive": False,
                    "is_blocked": False,
                    "synonyms": [],
                    "related_docs": [],
                }
            ],
        )
        assert_ok(resp)

    def test_79_list_registry_docs(self):
        resp = reg_client.get(f"{BASE}/documents")
        assert_ok(resp)
        data = resp.json()
        assert "data" in data
        assert_paginated(data)

    def test_80_get_registry_doc(self):
        resp = reg_client.get(f"{BASE}/documents/b3a8f1c2-4d5e-6f7a-8b9c-0d1e2f3a4b5c")
        assert_ok(resp)
        assert resp.json()["data"]["title"] == "Стойки установочные"

    def test_81_create_registry_doc(self):
        resp = reg_client.post(
            f"{BASE}/documents",
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
        assert resp.json()["data"]["title"] == "Test Doc"

    def test_82_update_registry_doc(self):
        resp = reg_client.put(
            f"{BASE}/documents/b3a8f1c2-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
            json={"jurisdiction": "RF"},
        )
        assert_ok(resp)

    def test_83_update_doc_status(self):
        resp = reg_client.patch(
            f"{BASE}/documents/b3a8f1c2-4d5e-6f7a-8b9c-0d1e2f3a4b5c/status",
            json={"status": "archived", "comment": "Test"},
        )
        assert_ok(resp)
        assert resp.json()["data"]["status"] == "archived"

    def test_84_export_registry_docs(self):
        resp = reg_client.get(f"{BASE}/documents/export", params={"format": "json"})
        assert_ok(resp)

    def test_85_import_registry_docs(self):
        resp = reg_client.post(
            f"{BASE}/documents/import",
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

    def test_86_delete_registry_doc(self):
        create = reg_client.post(
            f"{BASE}/documents",
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
        resp = reg_client.delete(f"{BASE}/documents/{doc_id}")
        assert_ok(resp)

    def test_87_get_stats(self):
        resp = reg_client.get(f"{BASE}/stats")
        assert_ok(resp)
        data = resp.json()["data"]
        assert "documents_total" in data

    def test_88_get_enums(self):
        resp = reg_client.get(f"{BASE}/enums")
        assert_ok(resp)
        data = resp.json()["data"]
        assert "classifier_system" in data

    def test_89_list_quarantine(self):
        resp = reg_client.get(f"{BASE}/classifiers/quarantine")
        assert_ok(resp)
        assert "data" in resp.json()

    def test_90_accept_quarantine(self):
        resp = reg_client.post(f"{BASE}/classifiers/quarantine/p-001/accept")
        assert_ok(resp)
        assert resp.json()["data"]["status"] == "accepted"

    def test_91_reject_quarantine(self):
        resp = reg_client.post(f"{BASE}/classifiers/quarantine/p-001/reject")
        assert_ok(resp)
        assert resp.json()["data"]["status"] == "rejected"

    def test_92_validate_classification(self):
        resp = reg_client.post(
            f"{BASE}/classifiers/validate",
            json={"mks_oks_code": "47.020"},
        )
        assert_ok(resp)
        data = resp.json()["data"]
        assert "mks_status" in data

    def test_93_registry_doc_history(self):
        resp = reg_client.get(f"{BASE}/documents/b3a8f1c2-4d5e-6f7a-8b9c-0d1e2f3a4b5c/history")
        assert_ok(resp)
        assert "history" in resp.json()["data"]

    def test_94_registry_doc_chain(self):
        resp = reg_client.get(f"{BASE}/documents/b3a8f1c2-4d5e-6f7a-8b9c-0d1e2f3a4b5c/succession")
        assert_ok(resp)
        data = resp.json()["data"]
        assert "chain" in data

# ===========================================================================
# 5. AUTH-ME BINDING TESTS
# ===========================================================================
class TestAuthMeBinding:
    def setup_method(self):
        reset_rate_limiter()

    def test_95_me_returns_correct_user_by_token(self):
        token = auth_client.post(
            f"{BASE}/auth/token",
            json={"username": "kuznetsov@example.com", "password": "secret789"},
        ).json()["access_token"]
        resp = auth_client.get(f"{BASE}/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert_ok(resp)
        data = resp.json()
        assert data["user_id"] == "u-004"
        assert data["full_name"] == "Кузнецов Дмитрий Олегович"

    def test_96_me_returns_admin_user(self):
        token = auth_header_admin()["Authorization"].split(" ")[1]
        resp = auth_client.get(f"{BASE}/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert_ok(resp)
        assert resp.json()["role"] == "system_admin"

    def test_97_me_401_without_token(self):
        resp = auth_client.get(f"{BASE}/auth/me")
        assert resp.status_code == 401

    def test_98_me_401_invalid_token(self):
        resp = auth_client.get(f"{BASE}/auth/me", headers={"Authorization": "Bearer invalid"})
        assert resp.status_code == 401

# ===========================================================================
# 6. RBAC TESTS
# ===========================================================================
class TestRBAC:
    def setup_method(self):
        reset_rate_limiter()

    def test_99_admin_users_401_without_token(self):
        resp = auth_client.get(f"{BASE}/admin/users")
        assert resp.status_code == 401

    def test_100_admin_users_403_for_engineer(self):
        token = auth_header_engineer()["Authorization"].split(" ")[1]
        resp = auth_client.get(f"{BASE}/admin/users", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_101_admin_users_200_for_admin(self):
        token = auth_header_admin()["Authorization"].split(" ")[1]
        resp = auth_client.get(f"{BASE}/admin/users", headers={"Authorization": f"Bearer {token}"})
        assert_ok(resp)

    def test_102_admin_endpoints_blocked_for_non_admin(self):
        token = auth_header_engineer()["Authorization"].split(" ")[1]
        headers = {"Authorization": f"Bearer {token}"}
        for method, path in [
            ("GET", f"{BASE}/admin/users"),
            ("POST", f"{BASE}/admin/users"),
            ("GET", f"{BASE}/admin/users/u-001"),
            ("PUT", f"{BASE}/admin/users/u-001"),
            ("PATCH", f"{BASE}/admin/users/u-001"),
            ("DELETE", f"{BASE}/admin/users/u-001"),
            ("GET", f"{BASE}/admin/roles"),
            ("POST", f"{BASE}/admin/roles"),
            ("GET", f"{BASE}/admin/audit"),
        ]:
            fn = getattr(auth_client, method.lower())
            resp = fn(path, headers=headers)
            assert resp.status_code in (401, 403), f"{method} {path} returned {resp.status_code}"

# ===========================================================================
# 7. ERROR FORMAT TESTS
# ===========================================================================
class TestErrorFormat:
    def setup_method(self):
        reset_rate_limiter()

    def test_103_auth_error_format(self):
        resp = auth_client.get(f"{BASE}/auth/me")
        assert resp.status_code == 401
        assert "error" in resp.json()

    def test_104_orchestrator_error_format(self):
        resp = orch_client.get(f"{BASE}/documents/nonexistent")
        assert resp.status_code == 404
        assert "error" in resp.json()

    def test_105_query_error_format(self):
        resp = query_client.get(f"{BASE}/chat/sessions/nonexistent")
        assert resp.status_code == 404
        assert "error" in resp.json()

    def test_106_registry_error_format(self):
        resp = reg_client.get(f"{BASE}/classifiers/nonexistent")
        assert resp.status_code == 404
        assert "error" in resp.json()

# ===========================================================================
# 8. LOGIN USERNAME TESTS
# ===========================================================================
class TestLoginUsername:
    def setup_method(self):
        reset_rate_limiter()

    def test_107_login_with_full_email(self):
        resp = auth_client.post(
            f"{BASE}/auth/token",
            json={"username": "ivanov@example.com", "password": "secret123"},
        )
        assert_ok(resp)

    def test_108_login_with_part(self):
        resp = auth_client.post(
            f"{BASE}/auth/token",
            json={"username": "ivanov", "password": "secret123"},
        )
        assert_ok(resp)

    def test_109_login_invalid_credentials(self):
        resp = auth_client.post(
            f"{BASE}/auth/token",
            json={"username": "ivanov@example.com", "password": "wrong"},
        )
        assert resp.status_code == 401

# ===========================================================================
# 9. RESPONSE MODELS (OpenAPI) TESTS
# ===========================================================================
class TestResponseModels:
    def setup_method(self):
        reset_rate_limiter()

    def test_110_auth_openapi(self):
        resp = auth_client.get("/openapi.json")
        assert_ok(resp)
        schemas = resp.json()["components"]["schemas"]
        assert "TokenResponse" in schemas or "HTTPValidationError" in schemas

    def test_111_orchestrator_openapi(self):
        resp = orch_client.get("/openapi.json")
        assert_ok(resp)
        paths = resp.json()["paths"]
        assert any("/api/v1/documents" in p for p in paths)

    def test_112_query_openapi(self):
        resp = query_client.get("/openapi.json")
        assert_ok(resp)

    def test_113_registry_openapi(self):
        resp = reg_client.get("/openapi.json")
        assert_ok(resp)

# ===========================================================================
# 10. REGISTRY PAGINATION TESTS
# ===========================================================================
class TestRegistryPagination:
    def setup_method(self):
        reset_rate_limiter()

    def test_114_documents_meta(self):
        resp = reg_client.get(f"{BASE}/documents")
        assert "meta" in resp.json()

    def test_115_classifiers_meta(self):
        resp = reg_client.get(f"{BASE}/classifiers")
        assert "meta" in resp.json()

    def test_116_terminology_meta(self):
        resp = reg_client.get(f"{BASE}/terminology")
        assert "meta" in resp.json()