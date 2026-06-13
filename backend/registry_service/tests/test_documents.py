import pytest

def test_create_document(client):
    payload = {
        "title": "Test Document",
        "doc_code": "DOC-123",
        "status": "draft",
        "classifier_system": "MKS",
        "mks_oks_code": "01.01.01"
    }
    response = client.post("/api/v1/registry/documents/", json=payload)
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["data"]["title"] == "Test Document"
    assert "id" in data["data"]

def test_create_document_with_classifier(client):
    client.post("/api/v1/registry/classifiers/", json={"classifier_system": "MKS", "code": "CLS_001", "full_name": "Test Classifier"})
    
    payload = {
        "title": "Document with Classifier",
        "doc_code": "DOC-CLS",
        "classifier_system": "MKS",
        "mks_oks_code": "CLS_001"
    }
    response = client.post("/api/v1/registry/documents/", json=payload)
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["data"]["mks_oks_code"] == "CLS_001"

def test_create_document_validation_error(client):
    payload = {"doc_code": "DOC-VAL"}
    response = client.post("/api/v1/registry/documents/", json=payload)
    assert response.status_code == 422

def test_get_documents(client):
    client.post("/api/v1/registry/documents/", json={"title": "Doc 1", "classifier_system": "MKS"})
    client.post("/api/v1/registry/documents/", json={"title": "Doc 2", "classifier_system": "MKS"})
    
    response = client.get("/api/v1/registry/documents/")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 2

def test_get_documents_with_filters(client):
    client.post("/api/v1/registry/documents/", json={"title": "Draft Doc", "status": "draft", "classifier_system": "MKS"})
    client.post("/api/v1/registry/documents/", json={"title": "Active Doc", "status": "active", "classifier_system": "MKS"})
    
    response = client.get("/api/v1/registry/documents/?status=draft")
    assert response.status_code == 200
    data = response.json()
    assert all(item["status"] == "draft" for item in data["data"])

def test_get_documents_with_search(client):
    client.post("/api/v1/registry/documents/", json={"title": "Machine Learning Document", "classifier_system": "MKS"})
    
    response = client.get("/api/v1/registry/documents/?title=Machine")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1

def test_get_documents_with_classifier_filter(client):
    client.post("/api/v1/registry/classifiers/", json={"classifier_system": "MKS", "code": "CLS_FILTER", "full_name": "Filter Classifier"})
    
    client.post("/api/v1/registry/documents/", json={"title": "Doc 1", "classifier_system": "MKS", "mks_oks_code": "CLS_FILTER"})
    
    response = client.get("/api/v1/registry/documents/?mks_oks_code=CLS_FILTER")
    assert response.status_code == 200
    data = response.json()
    assert all(item["mks_oks_code"] == "CLS_FILTER" for item in data["data"])

def test_get_documents_pagination(client):
    for i in range(15):
        client.post("/api/v1/registry/documents/", json={"title": f"Doc {i}", "classifier_system": "MKS"})
    
    response = client.get("/api/v1/registry/documents/?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) <= 10
    assert data["meta"]["page"] == 1

def test_get_document_by_id(client):
    create_res = client.post("/api/v1/registry/documents/", json={"title": "Doc 2", "classifier_system": "MKS"})
    doc_id = create_res.json()["data"]["id"]
    
    response = client.get(f"/api/v1/registry/documents/{doc_id}/")
    assert response.status_code == 200
    assert response.json()["data"]["id"] == doc_id

def test_get_document_not_found(client):
    response = client.get("/api/v1/registry/documents/00000000-0000-0000-0000-000000000000/")
    assert response.status_code == 404

def test_update_document(client):
    create_res = client.post("/api/v1/registry/documents/", json={"title": "Doc 3", "classifier_system": "MKS"})
    doc_id = create_res.json()["data"]["id"]
    
    response = client.put(f"/api/v1/registry/documents/{doc_id}/", json={"title": "Updated Doc 3"})
    assert response.status_code == 200
    assert response.json()["data"]["title"] == "Updated Doc 3"

def test_update_document_not_found(client):
    response = client.put("/api/v1/registry/documents/00000000-0000-0000-0000-000000000000/", json={"title": "Updated"})
    assert response.status_code == 404

def test_delete_document(client):
    create_res = client.post("/api/v1/registry/documents/", json={"title": "Doc 4", "classifier_system": "MKS"})
    doc_id = create_res.json()["data"]["id"]
    
    response = client.delete(f"/api/v1/registry/documents/{doc_id}/")
    assert response.status_code == 200
    
    get_res = client.get(f"/api/v1/registry/documents/{doc_id}/")
    assert get_res.status_code == 404

def test_delete_document_not_found(client):
    response = client.delete("/api/v1/registry/documents/00000000-0000-0000-0000-000000000000/")
    assert response.status_code == 404

def test_patch_document_status(client):
    create_res = client.post("/api/v1/registry/documents/", json={"title": "Doc Patch Status", "classifier_system": "MKS", "status": "draft"})
    doc_id = create_res.json()["data"]["id"]
    
    # Valid transition: draft -> uploaded
    response = client.patch(f"/api/v1/registry/documents/{doc_id}/status/", json={"status": "uploaded", "comment": "moving to uploaded", "changed_by": "test_user"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "uploaded"
    assert data["previous_status"] == "draft"
    assert "history_id" in data
    
    # Invalid transition: uploaded -> approved
    response_invalid = client.patch(f"/api/v1/registry/documents/{doc_id}/status/", json={"status": "approved"})
    assert response_invalid.status_code == 400
    
    # Invalid status
    response_bad_status = client.patch(f"/api/v1/registry/documents/{doc_id}/status/", json={"status": "unknown_status"})
    assert response_bad_status.status_code == 400


def test_patch_document_status_not_found(client):
    response = client.patch("/api/v1/registry/documents/00000000-0000-0000-0000-000000000000/status/", json={"status": "approved"})
    assert response.status_code == 404

def test_export_documents(client):
    client.post("/api/v1/registry/documents/", json={"title": "Export Doc 1", "classifier_system": "MKS"})
    
    response = client.get("/api/v1/registry/documents/export/")
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")

def test_import_documents(client):
    response = client.post("/api/v1/registry/documents/import/?mapping=some_mapping", files={"file": ("test.csv", b"dummy content", "text/csv")})
    assert response.status_code in [200, 201]

def test_get_document_history(client):
    create_res = client.post("/api/v1/registry/documents/", json={"title": "History Doc", "classifier_system": "MKS"})
    doc_id = create_res.json()["data"]["id"]
    
    response = client.get(f"/api/v1/registry/documents/{doc_id}/history/")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data

def test_get_document_succession(client):
    create_res = client.post("/api/v1/registry/documents/", json={"title": "Succession Doc", "classifier_system": "MKS"})
    doc_id = create_res.json()["data"]["id"]
    
    response = client.get(f"/api/v1/registry/documents/{doc_id}/succession/")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data


def test_create_pipeline_document(client):
    payload = {
        "document": {
            "metadata": {
                "title": "Pipeline Test Doc",
                "doc_code": "PL-001",
                "source_type": "GOST",
                "mks_oks_code": "01.01.01",
                "era": "RF",
                "status": "uploaded"
            },
            "source": {
                "file_hash_sha256": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
            },
            "content": [
                {
                    "clause": "1",
                    "title": "Introduction",
                    "level": 1,
                    "type": "text",
                    "content": "This is a pipeline section"
                }
            ],
            "terminology": [
                {
                    "term": "PipelineTerm",
                    "normalized_term": "pipelineterm",
                    "definition": "A term created via pipeline"
                }
            ],
            "references": [
                {
                    "target_doc_code": "REF-001",
                    "type": "replaces",
                    "context": "replaces some older doc",
                    "current_status": "active"
                }
            ]
        }
    }
    
    response = client.post("/api/v1/registry/documents/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "document_id" in data
    assert data["registry"]["sections_count"] == 1
    assert data["registry"]["references_count"] == 1
    
    # Test duplicate detection
    dup_response = client.post("/api/v1/registry/documents/", json=payload)
    assert dup_response.status_code == 409


def test_get_documents_with_additional_filters(client):
    # Create doc
    client.post("/api/v1/registry/documents/", json={
        "title": "Filtered Doc Alpha",
        "doc_code": "FDA-01",
        "classifier_system": "MKS",
        "era": "USSR",
        "source_type": "GOST_R",
        "validity_status": "superseded",
        "jurisdiction": "RU"
    })
    
    # Query with filters
    response = client.get("/api/v1/registry/documents/?era=USSR&source_type=GOST_R&validity_status=superseded&jurisdiction=RU")
    assert response.status_code == 200
    res_data = response.json()
    assert len(res_data["data"]) >= 1
    assert any(doc["doc_code"] == "FDA-01" for doc in res_data["data"])

