import pytest

def test_create_document(client):
    # Depending on your specific API payload requirements
    payload = {
        "title": "Test Document",
        "doc_code": "DOC-123",
        "status": "draft"
    }
    response = client.post("/api/v1/registry/documents/", json=payload)
    # The API might be returning 200 or 201 based on how it's written.
    # We will accept either 200 or 201.
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["data"]["title"] == "Test Document"
    assert "id" in data["data"]

def test_get_documents(client):
    client.post("/api/v1/registry/documents/", json={"title": "Doc 1"})
    
    response = client.get("/api/v1/registry/documents/")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1

def test_get_document_by_id(client):
    create_res = client.post("/api/v1/registry/documents/", json={"title": "Doc 2"})
    doc_id = create_res.json()["data"]["id"]
    
    response = client.get(f"/api/v1/registry/documents/{doc_id}")
    assert response.status_code == 200
    assert response.json()["data"]["id"] == doc_id

def test_update_document(client):
    create_res = client.post("/api/v1/registry/documents/", json={"title": "Doc 3"})
    doc_id = create_res.json()["data"]["id"]
    
    response = client.put(f"/api/v1/registry/documents/{doc_id}", json={"title": "Updated Doc 3"})
    assert response.status_code == 200
    assert response.json()["data"]["title"] == "Updated Doc 3"

def test_delete_document(client):
    create_res = client.post("/api/v1/registry/documents/", json={"title": "Doc 4"})
    doc_id = create_res.json()["data"]["id"]
    
    response = client.delete(f"/api/v1/registry/documents/{doc_id}")
    assert response.status_code == 200
    
    get_res = client.get(f"/api/v1/registry/documents/{doc_id}")
    assert get_res.status_code == 404

def test_patch_document_status(client):
    create_res = client.post("/api/v1/registry/documents/", json={"title": "Doc Patch Status"})
    doc_id = create_res.json()["data"]["id"]
    
    response = client.patch(f"/api/v1/registry/documents/{doc_id}/status", json={"status": "approved"})
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "approved"

def test_export_documents(client):
    response = client.get("/api/v1/registry/documents/export")
    assert response.status_code == 200

def test_import_documents(client):
    response = client.post("/api/v1/registry/documents/import", params={"mapping": "some_mapping"}, files={"file": ("test.csv", b"dummy content", "text/csv")})
    assert response.status_code in [200, 201]
