import pytest

def test_get_enums(client):
    response = client.get("/api/v1/registry/enums")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "classifier_system" in data["data"]
    assert "source_type" in data["data"]
    assert "document_status" in data["data"]
    assert "era" in data["data"]

def test_get_enums_structure(client):
    response = client.get("/api/v1/registry/enums")
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data["data"]["classifier_system"], list)
    assert isinstance(data["data"]["jurisdiction"], list)
    assert "MKS" in data["data"]["classifier_system"]
    assert "RU" in data["data"]["jurisdiction"]
    assert "draft" in data["data"]["document_status"]

def test_get_stats_empty(client):
    response = client.get("/api/v1/registry/stats")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "classifiers_total" in data["data"]
    assert "terminology_total" in data["data"]
    assert "documents_total" in data["data"]
    assert "documents_by_status" in data["data"]

    assert data["data"]["classifiers_total"] == {}
    assert data["data"]["terminology_total"] == 0
    assert data["data"]["documents_total"] == 0

def test_get_stats_with_data(client):
    client.post("/api/v1/registry/classifiers/", json={
        "classifier_system": "MKS",
        "code": "STATS_01",
        "full_name": "Stats Classifier"
    })
    client.post("/api/v1/registry/classifiers/", json={
        "classifier_system": "MKS",
        "code": "STATS_02",
        "full_name": "Stats Classifier 2"
    })

    client.post("/api/v1/registry/terminology/", json={
        "raw_term": "Stats Term",
        "standard_term": "Stats Term",
        "normalized_value": "stats term",
        "term_type": "term"
    })

    client.post("/api/v1/registry/documents/", json={
        "title": "Stats Document",
        "status": "draft",
        "classifier_system": "MKS"
    })
    client.post("/api/v1/registry/documents/", json={
        "title": "Stats Document 2",
        "status": "approved",
        "classifier_system": "MKS"
    })

    response = client.get("/api/v1/registry/stats")
    assert response.status_code == 200
    data = response.json()

    assert data["data"]["classifiers_total"]["MKS"] == 2
    assert data["data"]["terminology_total"] == 1
    assert data["data"]["documents_total"] == 2
    assert isinstance(data["data"]["documents_by_status"], dict)

def test_get_stats_status_breakdown(client):
    client.post("/api/v1/registry/documents/", json={"title": "Draft Doc Status", "status": "draft", "classifier_system": "MKS"})
    client.post("/api/v1/registry/documents/", json={"title": "Draft Doc Status 2", "status": "draft", "classifier_system": "MKS"})
    client.post("/api/v1/registry/documents/", json={"title": "Approved Doc Status", "status": "approved", "classifier_system": "MKS"})
    client.post("/api/v1/registry/documents/", json={"title": "Processing Doc Status", "status": "processing", "classifier_system": "MKS"})

    response = client.get("/api/v1/registry/stats")
    assert response.status_code == 200
    data = response.json()

    status_breakdown = data["data"]["documents_by_status"]
    assert status_breakdown["draft"] >= 2
    assert status_breakdown["approved"] >= 1
    assert status_breakdown["processing"] >= 1
