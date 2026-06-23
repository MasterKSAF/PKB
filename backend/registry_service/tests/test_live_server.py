import io
import json
import uuid
import httpx
import pytest

BASE_URL = "http://127.0.0.1:8084/api/v1"

# Check if live server is running to dynamically skip tests
server_running = False
try:
    with httpx.Client() as client:
        r = client.get(f"{BASE_URL}/health")
        if r.status_code == 200:
            server_running = True
except Exception:
    pass

pytestmark = pytest.mark.skipif(not server_running, reason="Live server not running on port 8084")

def test_live_server_endpoints():
    print("Starting End-to-End Tests against live server...")
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        # Generate unique suffix for names to run in absolute isolation
        suffix = uuid.uuid4().hex[:8].upper()
        
        cat_name = f"LIVE_CAT_{suffix}"
        clf_code = f"LIVE_CLF_{suffix}"
        term_raw = f"live_term_{suffix.lower()}"
        term_std = f"Live Term {suffix}"
        doc_code = f"LIVE-DOC-{suffix}"
        doc_std_code = f"LIVE-DOC-STD-{suffix}"
        
        # 1. Health check
        print("\nTesting: GET /health")
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}
        
        # 2. Enums
        print("\nTesting: GET /registry/enums")
        r = client.get("/registry/enums")
        assert r.status_code == 200
        
        # 3. Stats
        print("\nTesting: GET /registry/stats")
        r = client.get("/registry/stats")
        assert r.status_code == 200

        # 4. Search (BM25)
        print("\nTesting: GET /registry/search")
        r = client.get("/registry/search?q=test")
        assert r.status_code == 200

        # 5. Create Category
        print("\nTesting: POST /registry/categories")
        r = client.post("/registry/categories", json={"name": cat_name})
        assert r.status_code == 201
        cat_id = r.json()["data"]["id"]

        # 6. List Categories
        print("\nTesting: GET /registry/categories")
        r = client.get("/registry/categories")
        assert r.status_code == 200
        
        # 7. Get Category
        print("\nTesting: GET /registry/categories/{category_id}")
        r = client.get(f"/registry/categories/{cat_id}")
        assert r.status_code == 200
        assert r.json()["data"]["name"] == cat_name

        # 8. Update Category
        print("\nTesting: PUT /registry/categories/{category_id}")
        r = client.put(f"/registry/categories/{cat_id}", json={"name": f"{cat_name}_UPDATED"})
        assert r.status_code == 200
        assert r.json()["data"]["name"] == f"{cat_name}_UPDATED"

        # 9. Create Classifier
        print("\nTesting: POST /registry/classifiers")
        clf_payload = {
            "classifier_system": "MKS",
            "code": clf_code,
            "full_name": f"Test Live Classifier {suffix}",
            "status": "active"
        }
        r = client.post("/registry/classifiers", json=clf_payload)
        assert r.status_code == 201
        
        # 10. List Classifiers
        print("\nTesting: GET /registry/classifiers")
        r = client.get("/registry/classifiers")
        assert r.status_code == 200

        # 11. Get Classifier
        print("\nTesting: GET /registry/classifiers/{code}")
        r = client.get(f"/registry/classifiers/{clf_code}?classifier_system=MKS")
        assert r.status_code == 200
        assert r.json()["data"]["code"] == clf_code

        # 12. Put Classifier
        print("\nTesting: PUT /registry/classifiers/{code}")
        r = client.put(f"/registry/classifiers/{clf_code}?classifier_system=MKS", json={"full_name": f"Test Live Classifier Updated {suffix}"})
        assert r.status_code == 200
        assert r.json()["data"]["full_name"] == f"Test Live Classifier Updated {suffix}"

        # 13. Patch Classifier
        print("\nTesting: PATCH /registry/classifiers/{code}")
        r = client.patch(f"/registry/classifiers/{clf_code}?classifier_system=MKS", json={"full_name": f"Test Live Classifier Patched {suffix}"})
        assert r.status_code == 200
        assert r.json()["data"]["full_name"] == f"Test Live Classifier Patched {suffix}"

        # 14. Classifiers Tree
        print("\nTesting: GET /registry/classifiers/tree")
        r = client.get("/registry/classifiers/tree?classifier_system=MKS")
        assert r.status_code == 200

        # 15. Validate Classifiers
        print("\nTesting: POST /registry/classifiers/validate")
        r = client.post("/registry/classifiers/validate", json={"classification": {"MKS": clf_code}})
        assert r.status_code == 200

        # 16. Import Classifiers (CSV)
        print("\nTesting: POST /registry/classifiers/import")
        imp_clf_code = f"TEST_IMP_{suffix}"
        csv_clf_data = f"CSV_Code,CSV_Name\n{imp_clf_code},Test Imported Classifier {suffix}\n"
        files = {"file": ("classifiers.csv", io.BytesIO(csv_clf_data.encode("utf-8")), "text/csv")}
        mapping = json.dumps({"code": "CSV_Code", "full_name": "CSV_Name"})
        r = client.post(f"/registry/classifiers/import?classifier_system=MKS&mapping={mapping}", files=files)
        assert r.status_code == 200
        assert r.json()["data"]["inserted"] == 1
        # Clean up imported classifier
        client.delete(f"/registry/classifiers/{imp_clf_code}?classifier_system=MKS&force=true")

        # 17. Classifiers Pending (Quarantine)
        print("\nTesting: GET /registry/classifiers/pending")
        r = client.get("/registry/classifiers/pending")
        assert r.status_code == 200

        # 18. Create Terminology
        print("\nTesting: POST /registry/terminology")
        term_payload = {
            "raw_term": term_raw,
            "standard_term": term_std,
            "normalized_value": term_raw,
            "term_type": "acronym",
            "definition": f"Term created for live testing {suffix}",
            "is_blocked": False
        }
        r = client.post("/registry/terminology", json=term_payload)
        assert r.status_code == 201
        term_id = r.json()["data"]["id"]

        # 19. List Terminology
        print("\nTesting: GET /registry/terminology")
        r = client.get("/registry/terminology")
        assert r.status_code == 200

        # 20. Get Terminology
        print("\nTesting: GET /registry/terminology/{term_id}")
        r = client.get(f"/registry/terminology/{term_id}")
        assert r.status_code == 200
        assert r.json()["data"]["raw_term"] == term_raw

        # 21. Normalize Terminology
        print("\nTesting: GET /registry/terminology/normalize")
        r = client.get(f"/registry/terminology/normalize?term={term_raw}")
        assert r.status_code == 200
        assert r.json()["data"]["standard_term"] == term_std

        # 22. Put Terminology
        print("\nTesting: PUT /registry/terminology/{term_id}")
        r = client.put(f"/registry/terminology/{term_id}", json={
            "raw_term": term_raw,
            "standard_term": f"{term_std} Updated",
            "normalized_value": term_raw,
            "term_type": "acronym"
        })
        assert r.status_code == 200
        assert r.json()["data"]["standard_term"] == f"{term_std} Updated"

        # 23. Patch Terminology
        print("\nTesting: PATCH /registry/terminology/{term_id}")
        r = client.patch(f"/registry/terminology/{term_id}", json={
            "standard_term": f"{term_std} Patched"
        })
        assert r.status_code == 200
        assert r.json()["data"]["standard_term"] == f"{term_std} Patched"

        # 24. Import Terminology (CSV)
        print("\nTesting: POST /registry/terminology/import")
        imp_term_raw = f"live_imp_{suffix.lower()}"
        csv_term_data = f"CSV_Raw,CSV_Std,CSV_Type\n{imp_term_raw},Live Imported Term {suffix},acronym\n"
        files = {"file": ("terminology.csv", io.BytesIO(csv_term_data.encode("utf-8")), "text/csv")}
        mapping = json.dumps({"raw_term": "CSV_Raw", "standard_term": "CSV_Std", "term_type": "CSV_Type"})
        r = client.post(f"/registry/terminology/import?mapping={mapping}", files=files)
        assert r.status_code == 200
        assert r.json()["data"]["inserted"] == 1
        # Cleanup imported terminology
        r_list = client.get(f"/registry/terminology?raw_term={imp_term_raw}")
        if r_list.status_code == 200 and r_list.json().get("data"):
            imp_term_id = r_list.json()["data"][0]["id"]
            client.delete(f"/registry/terminology/{imp_term_id}")

        # 25. Create Document (Pipeline Flow)
        print("\nTesting: POST /registry/documents (Pipeline flow)")
        doc_payload_pipeline = {
            "document": {
                "metadata": {
                    "title": f"Live Test Document {suffix}",
                    "doc_code": doc_code,
                    "source_type": "GOST",
                    "mks_oks_code": clf_code,
                    "era": "RF",
                    "status": "uploaded"
                },
                "source": {
                    "file_hash_sha256": "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
                    "file_name": f"test_doc_file_key_{suffix}",
                    "page_count": 10
                },
                "content": [
                    {
                        "clause": "1",
                        "title": "Introduction",
                        "level": 1,
                        "type": "text",
                        "content": "Live test document section body"
                    }
                ],
                "terminology": [],
                "references": []
            }
        }
        r = client.post("/registry/documents", json=doc_payload_pipeline)
        assert r.status_code == 201
        doc_id = r.json()["document_id"]

        # 26. Create Document (Standard Flow)
        print("\nTesting: POST /registry/documents (Standard flow)")
        doc_payload_std = {
            "title": f"Live Test Document Standard {suffix}",
            "doc_code": doc_std_code,
            "source_type": "GOST",
            "era": "RF"
        }
        r = client.post("/registry/documents", json=doc_payload_std)
        assert r.status_code == 201
        doc_std_id = r.json()["data"]["id"]

        # 27. List Documents (with filters)
        print("\nTesting: GET /registry/documents")
        r = client.get(f"/registry/documents?doc_code={doc_code}")
        assert r.status_code == 200
        assert len(r.json()["data"]) >= 1

        # 28. Get Document
        print("\nTesting: GET /registry/documents/{document_id}")
        r = client.get(f"/registry/documents/{doc_id}")
        assert r.status_code == 200
        assert r.json()["data"]["title"] == f"Live Test Document {suffix}"

        # 29. Get Document Sections
        print("\nTesting: GET /registry/documents/{document_id}/sections")
        r = client.get(f"/registry/documents/{doc_id}/sections")
        assert r.status_code == 200
        assert len(r.json()["sections"]) >= 1

        # 30. Put Document
        print("\nTesting: PUT /registry/documents/{document_id}")
        r = client.put(f"/registry/documents/{doc_id}", json={
            "title": f"Live Test Document Updated {suffix}",
            "doc_code": doc_code
        })
        assert r.status_code == 200
        assert r.json()["data"]["title"] == f"Live Test Document Updated {suffix}"

        # 31. Patch Document (Valid fields)
        print("\nTesting: PATCH /registry/documents/{document_id}")
        r = client.patch(f"/registry/documents/{doc_id}", json={
            "title": f"Live Test Document Patched {suffix}",
            "valid_until": None,
            "category_ids": [int(cat_id)]
        })
        assert r.status_code == 200
        assert "title" in r.json()["data"]["updated_fields"]

        # 32. Patch Document Status (Orchestrator required)
        print("\nTesting: PATCH /registry/documents/{document_id}/status")
        r = client.patch(
            f"/registry/documents/{doc_id}/status", 
            json={"status": "validating", "comment": "Verified by test suite", "changed_by": "test"},
            headers={"X-Service-Id": "orchestrator"}
        )
        assert r.status_code == 200

        # 33. Get Document History
        print("\nTesting: GET /registry/documents/{document_id}/history")
        r = client.get(f"/registry/documents/{doc_id}/history")
        assert r.status_code == 200

        # 34. Get Document Succession
        print("\nTesting: GET /registry/documents/{document_id}/succession")
        r = client.get(f"/registry/documents/{doc_id}/succession")
        assert r.status_code == 200

        # 35. Export Documents
        print("\nTesting: GET /registry/documents/export")
        r = client.get("/registry/documents/export")
        assert r.status_code == 200
        assert "text/csv" in r.headers["content-type"]

        # 36. Check Uniqueness
        print("\nTesting: POST /registry/documents/check-uniqueness")
        r = client.post("/registry/documents/check-uniqueness", json={
            "title": f"Live Test Document Patched {suffix}",
            "doc_code": doc_code,
            "era": "RF",
            "source_type": "GOST"
        })
        assert r.status_code == 200

        # 37. Import Documents (CSV)
        print("\nTesting: POST /registry/documents/import")
        imp_doc_code = f"LIVE-IMP-{suffix}"
        csv_doc_data = f"CSV_Title,CSV_Code\nLive Import Doc {suffix},{imp_doc_code}\n"
        files = {"file": ("documents.csv", io.BytesIO(csv_doc_data.encode("utf-8")), "text/csv")}
        mapping = json.dumps({"title": "CSV_Title", "doc_code": "CSV_Code"})
        r = client.post(f"/registry/documents/import?mapping={mapping}", files=files)
        assert r.status_code == 200
        assert r.json()["data"]["inserted"] == 1
        # Cleanup imported document
        r_list = client.get(f"/registry/documents?doc_code={imp_doc_code}")
        if r_list.status_code == 200 and r_list.json().get("data"):
            imp_doc_id = r_list.json()["data"][0]["id"]
            client.delete(f"/registry/documents/{imp_doc_id}")

        # 38. List Document Files
        print("\nTesting: GET /registry/documents/{document_id}/files")
        r = client.get(f"/registry/documents/{doc_id}/files")
        assert r.status_code == 200
        
        # 39. List Document Versions
        print("\nTesting: GET /registry/documents/{document_id}/versions")
        r = client.get(f"/registry/documents/{doc_id}/versions")
        assert r.status_code == 200
        versions_list = r.json().get("data", [])
        version_id = None
        if versions_list:
            version_id = versions_list[0]["id"]

        # 40. Get Specific Version
        if version_id:
            print(f"\nTesting: GET /registry/versions/{{version_id}} with ID: {version_id}")
            r = client.get(f"/registry/versions/{version_id}")
            assert r.status_code == 200
        else:
            print("\nSkipping: GET /registry/versions/{version_id} (No version found)")

        # 41. Get Specific File Metadata (Using a nonexistent file_id to verify route matches)
        print("\nTesting: GET /registry/files/{file_id}")
        r = client.get("/registry/files/nonexistent_file_id")
        assert r.status_code == 404
        assert r.json()["detail"]["error"]["code"] == "FILE_NOT_FOUND"

        # 42. Create Draft
        print("\nTesting: POST /registry/drafts")
        draft_file_key = f"live_draft_file_{suffix.lower()}"
        draft_doc_key = f"live_draft_doc_{suffix.lower()}"
        draft_payload = {
            "file_key": draft_file_key,
            "document_key": draft_doc_key,
            "status": "new",
            "raw_data": {"title": f"Live Draft Doc {suffix}"},
            "created_by": "test-suite"
        }
        r = client.post("/registry/drafts", json=draft_payload)
        assert r.status_code == 201
        draft_id = r.json()["data"]["id"]

        # 43. List Drafts
        print("\nTesting: GET /registry/drafts")
        r = client.get("/registry/drafts")
        assert r.status_code == 200

        # 44. Get Draft Details
        print("\nTesting: GET /registry/drafts/{draft_id}")
        r = client.get(f"/registry/drafts/{draft_id}")
        assert r.status_code == 200

        # 45. Get Draft Preview
        print("\nTesting: GET /registry/drafts/{draft_id}/preview")
        r = client.get(f"/registry/drafts/{draft_id}/preview")
        assert r.status_code == 200

        # 46. Patch Draft Status
        print("\nTesting: PATCH /registry/drafts/{draft_id}/status")
        r = client.patch(f"/registry/drafts/{draft_id}/status", json={
            "status": "processing",
            "confidence": 0.99,
            "preview_metadata": {"title": f"Live Draft Doc Preview {suffix}"},
            "updated_by": "test-suite"
        })
        assert r.status_code == 200

        # 47. Patch Draft Metadata
        print("\nTesting: PATCH /registry/drafts/{draft_id}/metadata")
        r = client.patch(f"/registry/drafts/{draft_id}/metadata", json={
            "preview_metadata": {"title": f"Live Draft Doc Preview Updated {suffix}"},
            "metadata_overrides": {"status_note": "overridden metadata"},
            "updated_by": "test-suite"
        })
        assert r.status_code == 200

        # 48. Delete Draft
        print("\nTesting: DELETE /registry/drafts/{draft_id}")
        r = client.delete(f"/registry/drafts/{draft_id}")
        assert r.status_code == 200

        # 49. Quarantine (Classifier Pending) Accept and Reject tests
        print("\nTesting: Quarantine flow (Accept/Reject pending classifiers)")
        
        # We need unique codes for quarantine tests to prevent overlaps
        quar_suffix = uuid.uuid4().hex[:4].upper()
        missing_code_rej = f"99.{quar_suffix}"
        missing_code_acc = f"88.{quar_suffix}"

        # Create a document referencing a missing classifier code (Reject test)
        doc_payload_quarantine = {
            "title": f"Quarantine Live Test Doc {suffix}",
            "doc_code": f"LIVE-DOC-QUAR-{suffix}",
            "mks_oks_code": missing_code_rej  # Missing code -> should go to quarantine
        }
        r_create = client.post("/registry/documents", json=doc_payload_quarantine)
        assert r_create.status_code == 201
        quar_doc_id = r_create.json()["data"]["id"]

        # Fetch pending classifiers
        r_pend = client.get(f"/registry/classifiers/pending?system=MKS&status=new")
        assert r_pend.status_code == 200
        pending_items = r_pend.json().get("data", [])
        target_pending = None
        for item in pending_items:
            if item["code"] == missing_code_rej:
                target_pending = item
                break
        
        assert target_pending is not None, "Classifier pending record was not created for missing code"
        pending_id = target_pending["id"]

        # Reject it
        print(f"\nTesting: POST /registry/classifiers/pending/{{pending_id}}/reject for code {missing_code_rej}")
        r_rej = client.post(f"/registry/classifiers/pending/{pending_id}/reject", json={"admin_comment": "Rejection from live test"})
        assert r_rej.status_code == 200
        assert r_rej.json()["data"]["status"] == "rejected"

        # Create another document to test Accept
        doc_payload_quarantine_acc = {
            "title": f"Quarantine Accept Live Test Doc {suffix}",
            "doc_code": f"LIVE-DOC-QUAR-ACC-{suffix}",
            "mks_oks_code": missing_code_acc  # Missing code -> should go to quarantine
        }
        r_create_acc = client.post("/registry/documents", json=doc_payload_quarantine_acc)
        assert r_create_acc.status_code == 201
        quar_doc_id_acc = r_create_acc.json()["data"]["id"]

        # Fetch pending
        r_pend = client.get(f"/registry/classifiers/pending?system=MKS&status=new")
        target_pending_acc = None
        for item in r_pend.json().get("data", []):
            if item["code"] == missing_code_acc:
                target_pending_acc = item
                break
        
        assert target_pending_acc is not None
        pending_id_acc = target_pending_acc["id"]

        # Accept it
        print(f"\nTesting: POST /registry/classifiers/pending/{{pending_id}}/accept for code {missing_code_acc}")
        r_acc = client.post(f"/registry/classifiers/pending/{pending_id_acc}/accept", json={
            "full_name": f"Accepted Classifier from Live Test {suffix}",
            "admin_comment": "Acceptance from live test"
        })
        assert r_acc.status_code == 200
        assert r_acc.json()["data"]["status"] == "mapped"

        # Cleanup accepted classifier from database
        client.delete(f"/registry/classifiers/{missing_code_acc}?classifier_system=MKS&force=true")

        # Cleanup quarantine docs
        client.delete(f"/registry/documents/{quar_doc_id}")
        client.delete(f"/registry/documents/{quar_doc_id_acc}")

        # 50. Clean up Document (Pipeline flow created)
        print("\nTesting: DELETE /registry/documents/{document_id}")
        r = client.delete(f"/registry/documents/{doc_id}")
        assert r.status_code == 200

        # 51. Clean up Document (Standard flow created)
        r = client.delete(f"/registry/documents/{doc_std_id}")
        assert r.status_code == 200

        # 52. Clean up Category
        print("\nTesting: DELETE /registry/categories/{category_id}")
        r = client.delete(f"/registry/categories/{cat_id}")
        assert r.status_code == 200

        # 53. Clean up Classifier
        print("\nTesting: DELETE /registry/classifiers/{code}")
        r = client.delete(f"/registry/classifiers/{clf_code}?classifier_system=MKS&force=true")
        assert r.status_code == 200

        # 54. Clean up Terminology
        print("\nTesting: DELETE /registry/terminology/{term_id}")
        r = client.delete(f"/registry/terminology/{term_id}")
        assert r.status_code == 200

        print("\n===============================")
        print("All live server tests PASSED successfully!")
        print("===============================")

if __name__ == "__main__":
    import sys
    try:
        test_live_server_endpoints()
    except AssertionError as e:
        print(f"\nTEST FAILURE: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUNEXPECTED EXCEPTION: {e}")
        sys.exit(1)
