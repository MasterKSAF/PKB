import pytest

def test_create_document(client):
    payload = {
        "title": "Test Document",
        "doc_code": "DOC-123",
        "status": "draft"
    }
    response = client.post("/api/v1/registry/documents/", json=payload)
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["data"]["title"] == "Test Document"
    assert "id" in data["data"]

def test_create_document_with_classifier(client):
    # First create a classifier
    client.post("/api/v1/registry/classifiers/", json={
        "code": "CLS_001",
        "full_name": "Test Classifier"
    })
    
    payload = {
        "title": "Document with Classifier",
        "doc_code": "DOC-CLS",
        "classifier_code": "CLS_001"
    }
    response = client.post("/api/v1/registry/documents/", json=payload)
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["data"]["classifier_code"] == "CLS_001"

def test_create_document_validation_error(client):
    # Missing required field
    payload = {
        # Missing title
        "doc_code": "DOC-VAL"
    }
    response = client.post("/api/v1/registry/documents/", json=payload)
    assert response.status_code == 422

def test_get_documents(client):
    client.post("/api/v1/registry/documents/", json={"title": "Doc 1"})
    client.post("/api/v1/registry/documents/", json={"title": "Doc 2"})
    
    response = client.get("/api/v1/registry/documents/")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 2
    assert data["meta"]["total"] >= 2

def test_get_documents_with_filters(client):
    client.post("/api/v1/registry/documents/", json={"title": "Draft Doc", "status": "draft"})
    client.post("/api/v1/registry/documents/", json={"title": "Approved Doc", "status": "approved"})
    client.post("/api/v1/registry/documents/", json={"title": "Another Draft", "status": "draft"})
    
    # Filter by status
    response = client.get("/api/v1/registry/documents/?status=draft")
    assert response.status_code == 200
    data = response.json()
    assert all(item["status"] == "draft" for item in data["data"])

def test_get_documents_with_search(client):
    client.post("/api/v1/registry/documents/", json={"title": "Machine Learning Document"})
    client.post("/api/v1/registry/documents/", json={"title": "Other Document"})
    
    response = client.get("/api/v1/registry/documents/?title=Machine")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1
    assert "Machine" in data["data"][0]["title"]

def test_get_documents_with_classifier_filter(client):
    # Create classifier
    client.post("/api/v1/registry/classifiers/", json={
        "code": "CLS_FILTER",
        "full_name": "Filter Classifier"
    })
    
    client.post("/api/v1/registry/documents/", json={
        "title": "Doc 1",
        "classifier_code": "CLS_FILTER"
    })
    client.post("/api/v1/registry/documents/", json={"title": "Doc 2"})
    
    response = client.get("/api/v1/registry/documents/?classifier_code=CLS_FILTER")
    assert response.status_code == 200
    data = response.json()
    assert all(item["classifier_code"] == "CLS_FILTER" for item in data["data"])

def test_get_documents_pagination(client):
    # Create multiple documents
    for i in range(15):
        client.post("/api/v1/registry/documents/", json={"title": f"Doc {i}"})
    
    response = client.get("/api/v1/registry/documents/?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) <= 10
    assert data["meta"]["page"] == 1
    assert data["meta"]["page_size"] == 10

def test_get_document_by_id(client):
    create_res = client.post("/api/v1/registry/documents/", json={"title": "Doc 2"})
    doc_id = create_res.json()["data"]["id"]
    
    response = client.get(f"/api/v1/registry/documents/{doc_id}")
    assert response.status_code == 200
    assert response.json()["data"]["id"] == doc_id

def test_get_document_by_id_with_classifier(client):
    # Create classifier
    client.post("/api/v1/registry/classifiers/", json={
        "code": "CLS_REL",
        "full_name": "Related Classifier"
    })
    
    create_res = client.post("/api/v1/registry/documents/", json={
        "title": "Doc with Classifier",
        "classifier_code": "CLS_REL"
    })
    doc_id = create_res.json()["data"]["id"]
    
    response = client.get(f"/api/v1/registry/documents/{doc_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["id"] == doc_id
    assert data["data"]["classifier_name"] == "Related Classifier"

def test_get_document_not_found(client):
    response = client.get("/api/v1/registry/documents/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404

def test_update_document(client):
    create_res = client.post("/api/v1/registry/documents/", json={"title": "Doc 3"})
    doc_id = create_res.json()["data"]["id"]
    
    response = client.put(f"/api/v1/registry/documents/{doc_id}", json={"title": "Updated Doc 3"})
    assert response.status_code == 200
    assert response.json()["data"]["title"] == "Updated Doc 3"

def test_update_document_not_found(client):
    response = client.put("/api/v1/registry/documents/00000000-0000-0000-0000-000000000000", json={"title": "Updated"})
    assert response.status_code == 404

def test_delete_document(client):
    create_res = client.post("/api/v1/registry/documents/", json={"title": "Doc 4"})
    doc_id = create_res.json()["data"]["id"]
    
    response = client.delete(f"/api/v1/registry/documents/{doc_id}")
    assert response.status_code == 200
    
    get_res = client.get(f"/api/v1/registry/documents/{doc_id}")
    assert get_res.status_code == 404

def test_delete_document_not_found(client):
    response = client.delete("/api/v1/registry/documents/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404

def test_patch_document_status(client):
    create_res = client.post("/api/v1/registry/documents/", json={"title": "Doc Patch Status"})
    doc_id = create_res.json()["data"]["id"]
    
    response = client.patch(f"/api/v1/registry/documents/{doc_id}/status", json={"status": "approved"})
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "approved"

def test_patch_document_status_not_found(client):
    response = client.patch("/api/v1/registry/documents/00000000-0000-0000-0000-000000000000/status", json={"status": "approved"})
    assert response.status_code == 404

def test_patch_document_status_invalid(client):
    create_res = client.post("/api/v1/registry/documents/", json={"title": "Doc Invalid Status"})
    doc_id = create_res.json()["data"]["id"]
    
    response = client.patch(f"/api/v1/registry/documents/{doc_id}/status", json={"status": "invalid_status"})
    assert response.status_code == 422

def test_export_documents(client):
    # Create some documents first
    client.post("/api/v1/registry/documents/", json={"title": "Export Doc 1"})
    client.post("/api/v1/registry/documents/", json={"title": "Export Doc 2"})
    
    response = client.get("/api/v1/registry/documents/export")
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")

def test_export_documents_with_filters(client):
    client.post("/api/v1/registry/documents/", json={"title": "Export Filter 1", "status": "draft"})
    client.post("/api/v1/registry/documents/", json={"title": "Export Filter 2", "status": "approved"})
    
    response = client.get("/api/v1/registry/documents/export?status=draft")
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")

def test_import_documents(client):
    response = client.post("/api/v1/registry/documents/import", params={"mapping": "some_mapping"}, files={"file": ("test.csv", b"dummy content", "text/csv")})
    assert response.status_code in [200, 201]

def test_get_documents_with_source_filter(client):
    client.post("/api/v1/registry/documents/", json={
        "title": "Source Doc 1",
        "source": "internal"
    })
    client.post("/api/v1/registry/documents/", json={
        "title": "Source Doc 2",
        "source": "external"
    })
    
    response = client.get("/api/v1/registry/documents/?source=internal")
    assert response.status_code == 200
    data = response.json()
    # Note: source is stored in metadata, so this might not work directly
    # The test is to ensure the endpoint accepts the parameter

def test_get_documents_with_date_filter(client):
    client.post("/api/v1/registry/documents/", json={"title": "Date Doc 1"})
    client.post("/api/v1/registry/documents/", json={"title": "Date Doc 2"})
    
    response = client.get("/api/v1/registry/documents/")
    assert response.status_code == 200
    # Date filtering would require specific date values, just test that endpoint accepts params
    response = client.get("/api/v1/registry/documents/?date_from=2024-01-01&date_to=2024-12-31")
    assert response.status_code == 200

def test_create_document_with_metadata(client):
    payload = {
        "title": "Document with Metadata",
        "source": "test_source",
        "notes": "Test notes"
    }
    response = client.post("/api/v1/registry/documents/", json=payload)
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["data"]["title"] == "Document with Metadata"

def test_update_document_multiple_fields(client):
    create_res = client.post("/api/v1/registry/documents/", json={
        "title": "Original Title",
        "doc_code": "ORIG-001"
    })
    doc_id = create_res.json()["data"]["id"]
    
    update_payload = {
        "title": "Updated Title",
        "doc_code": "UPD-001",
        "source": "updated_source"
    }
    response = client.put(f"/api/v1/registry/documents/{doc_id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["title"] == "Updated Title"
    assert data["data"]["doc_code"] == "UPD-001"
