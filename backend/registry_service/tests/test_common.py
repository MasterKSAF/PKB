import pytest

def test_get_enums(client):
    response = client.get("/api/v1/registry/enums")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "doc_type" in data["data"]
    assert "jurisdiction" in data["data"]
    assert "language" in data["data"]
    assert "document_status" in data["data"]
    assert "context" in data["data"]

def test_get_enums_structure(client):
    response = client.get("/api/v1/registry/enums")
    assert response.status_code == 200
    data = response.json()
    
    # Verify enum values are lists
    assert isinstance(data["data"]["doc_type"], list)
    assert isinstance(data["data"]["jurisdiction"], list)
    assert isinstance(data["data"]["language"], list)
    
    # Verify expected enum values exist
    assert "OKS" in data["data"]["doc_type"]
    assert "RF" in data["data"]["jurisdiction"]
    assert "ru" in data["data"]["language"]

def test_get_stats_empty(client):
    response = client.get("/api/v1/registry/stats")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "classifiers_total" in data["data"]
    assert "terminology_total" in data["data"]
    assert "documents_total" in data["data"]
    assert "documents_by_status" in data["data"]
    
    # Should be 0 when empty
    assert data["data"]["classifiers_total"] == 0
    assert data["data"]["terminology_total"] == 0
    assert data["data"]["documents_total"] == 0

def test_get_stats_with_data(client):
    # Create some data
    client.post("/api/v1/registry/classifiers/", json={
        "code": "STATS_01",
        "full_name": "Stats Classifier"
    })
    client.post("/api/v1/registry/classifiers/", json={
        "code": "STATS_02",
        "full_name": "Stats Classifier 2"
    })
    
    client.post("/api/v1/registry/terminology/", json={
        "raw_term": "Stats Term",
        "normalized_value": "stats term",
        "context": "IT"
    })
    
    client.post("/api/v1/registry/documents/", json={
        "title": "Stats Document",
        "status": "draft"
    })
    client.post("/api/v1/registry/documents/", json={
        "title": "Stats Document 2",
        "status": "approved"
    })
    
    response = client.get("/api/v1/registry/stats")
    assert response.status_code == 200
    data = response.json()
    
    # Verify counts
    assert data["data"]["classifiers_total"] == 2
    assert data["data"]["terminology_total"] == 1
    assert data["data"]["documents_total"] == 2
    
    # Verify status breakdown
    assert "documents_by_status" in data["data"]
    assert isinstance(data["data"]["documents_by_status"], dict)

def test_get_stats_status_breakdown(client):
    # Create documents with different statuses
    client.post("/api/v1/registry/documents/", json={"title": "Draft Doc", "status": "draft"})
    client.post("/api/v1/registry/documents/", json={"title": "Draft Doc 2", "status": "draft"})
    client.post("/api/v1/registry/documents/", json={"title": "Approved Doc", "status": "approved"})
    client.post("/api/v1/registry/documents/", json={"title": "Processing Doc", "status": "processing"})
    
    response = client.get("/api/v1/registry/stats")
    assert response.status_code == 200
    data = response.json()
    
    # Verify status breakdown
    status_breakdown = data["data"]["documents_by_status"]
    assert "draft" in status_breakdown
    assert status_breakdown["draft"] == 2
    assert "approved" in status_breakdown
    assert status_breakdown["approved"] == 1
    assert "processing" in status_breakdown
    assert status_breakdown["processing"] == 1
