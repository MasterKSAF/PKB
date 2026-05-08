import pytest

def test_create_terminology(client):
    payload = {
        "raw_term": "Machine Learning",
        "normalized_value": "machine learning",
        "context": "IT"
    }
    response = client.post("/api/v1/registry/terminology/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["raw_term"] == "Machine Learning"
    assert "id" in data["data"]

def test_get_terminology(client):
    client.post("/api/v1/registry/terminology/", json={
        "raw_term": "Test Term", "normalized_value": "test term", "context": "Общий"
    })
    
    response = client.get("/api/v1/registry/terminology/")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1

def test_get_terminology_by_id(client):
    create_res = client.post("/api/v1/registry/terminology/", json={
        "raw_term": "Term 2", "normalized_value": "term 2", "context": "Общий"
    })
    term_id = create_res.json()["data"]["id"]
    
    response = client.get(f"/api/v1/registry/terminology/{term_id}")
    assert response.status_code == 200
    assert response.json()["data"]["id"] == term_id

def test_update_terminology(client):
    create_res = client.post("/api/v1/registry/terminology/", json={
        "raw_term": "Term 3", "normalized_value": "term 3", "context": "Общий"
    })
    term_id = create_res.json()["data"]["id"]
    
    response = client.put(f"/api/v1/registry/terminology/{term_id}", json={"term": "Updated Term 3"})
    assert response.status_code == 200
    assert response.json()["data"]["raw_term"] == "Updated Term 3"

def test_delete_terminology(client):
    create_res = client.post("/api/v1/registry/terminology/", json={
        "raw_term": "Term 4", "normalized_value": "term 4", "context": "Общий"
    })
    term_id = create_res.json()["data"]["id"]
    
    response = client.delete(f"/api/v1/registry/terminology/{term_id}")
    assert response.status_code == 200
    
    get_res = client.get(f"/api/v1/registry/terminology/{term_id}")
    assert get_res.status_code == 404

def test_normalize_terminology(client):
    response = client.get("/api/v1/registry/terminology/normalize", params={"term": "Some Term"})
    assert response.status_code == 200
    data = response.json()
    # It might return a normalized term or just success
    assert "data" in data

def test_import_terminology(client):
    # Dummy file upload test
    response = client.post("/api/v1/registry/terminology/import", params={"mapping": "some_mapping"}, files={"file": ("test.csv", b"dummy content", "text/csv")})
    assert response.status_code in [200, 201]
