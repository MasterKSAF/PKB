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

def test_create_terminology_duplicate(client):
    payload = {
        "raw_term": "Duplicate Term",
        "normalized_value": "duplicate term",
        "context": "IT"
    }
    client.post("/api/v1/registry/terminology/", json=payload)
    
    # Try to create with same raw_term and context
    response = client.post("/api/v1/registry/terminology/", json=payload)
    assert response.status_code == 409

def test_create_terminology_validation_error(client):
    # Missing required field
    payload = {
        # Missing raw_term
        "normalized_value": "test term",
        "context": "IT"
    }
    response = client.post("/api/v1/registry/terminology/", json=payload)
    assert response.status_code == 422

def test_get_terminology(client):
    client.post("/api/v1/registry/terminology/", json={
        "raw_term": "Test Term", "normalized_value": "test term", "context": "Общий"
    })
    client.post("/api/v1/registry/terminology/", json={
        "raw_term": "Another Term", "normalized_value": "another term", "context": "Общий"
    })
    
    response = client.get("/api/v1/registry/terminology/")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 2
    assert data["meta"]["total"] >= 2

def test_get_terminology_with_filters(client):
    client.post("/api/v1/registry/terminology/", json={
        "raw_term": "IT Term 1",
        "normalized_value": "it term 1",
        "context": "IT"
    })
    client.post("/api/v1/registry/terminology/", json={
        "raw_term": "Building Term",
        "normalized_value": "building term",
        "context": "Строительство"
    })
    client.post("/api/v1/registry/terminology/", json={
        "raw_term": "IT Term 2",
        "normalized_value": "it term 2",
        "context": "IT"
    })
    
    # Filter by context
    response = client.get("/api/v1/registry/terminology/?context=IT")
    assert response.status_code == 200
    data = response.json()
    assert all(item["context"] == "IT" for item in data["data"])

def test_get_terminology_with_search(client):
    client.post("/api/v1/registry/terminology/", json={
        "raw_term": "Machine Learning",
        "normalized_value": "machine learning",
        "context": "IT"
    })
    client.post("/api/v1/registry/terminology/", json={
        "raw_term": "Deep Learning",
        "normalized_value": "deep learning",
        "context": "IT"
    })
    client.post("/api/v1/registry/terminology/", json={
        "raw_term": "Other Concept",
        "normalized_value": "other concept",
        "context": "IT"
    })
    
    response = client.get("/api/v1/registry/terminology/?term=Machine")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1
    assert "Machine" in data["data"][0]["raw_term"]

def test_get_terminology_with_normalized_filter(client):
    client.post("/api/v1/registry/terminology/", json={
        "raw_term": "ML",
        "normalized_value": "machine learning",
        "context": "IT"
    })
    client.post("/api/v1/registry/terminology/", json={
        "raw_term": "AI",
        "normalized_value": "artificial intelligence",
        "context": "IT"
    })
    
    response = client.get("/api/v1/registry/terminology/?normalized_term=machine learning")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1

def test_get_terminology_pagination(client):
    # Create multiple terms
    for i in range(15):
        client.post("/api/v1/registry/terminology/", json={
            "raw_term": f"Term {i}",
            "normalized_value": f"term {i}",
            "context": "Общий"
        })
    
    response = client.get("/api/v1/registry/terminology/?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) <= 10
    assert data["meta"]["page"] == 1
    assert data["meta"]["page_size"] == 10

def test_get_terminology_by_id(client):
    create_res = client.post("/api/v1/registry/terminology/", json={
        "raw_term": "Term 2", "normalized_value": "term 2", "context": "Общий"
    })
    term_id = create_res.json()["data"]["id"]
    
    response = client.get(f"/api/v1/registry/terminology/{term_id}")
    assert response.status_code == 200
    assert response.json()["data"]["id"] == term_id

def test_get_terminology_not_found(client):
    response = client.get("/api/v1/registry/terminology/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404

def test_update_terminology(client):
    create_res = client.post("/api/v1/registry/terminology/", json={
        "raw_term": "Term 3", "normalized_value": "term 3", "context": "Общий"
    })
    term_id = create_res.json()["data"]["id"]
    
    response = client.put(f"/api/v1/registry/terminology/{term_id}", json={"term": "Updated Term 3"})
    assert response.status_code == 200
    assert response.json()["data"]["raw_term"] == "Updated Term 3"

def test_update_terminology_not_found(client):
    response = client.put("/api/v1/registry/terminology/00000000-0000-0000-0000-000000000000", json={"term": "Updated"})
    assert response.status_code == 404

def test_update_terminology_multiple_fields(client):
    create_res = client.post("/api/v1/registry/terminology/", json={
        "raw_term": "Original Term",
        "normalized_value": "original term",
        "context": "IT"
    })
    term_id = create_res.json()["data"]["id"]
    
    update_payload = {
        "term": "Updated Term",
        "normalized_term": "updated term",
        "context": "Строительство",
        "source": "manual"
    }
    response = client.put(f"/api/v1/registry/terminology/{term_id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["raw_term"] == "Updated Term"

def test_delete_terminology(client):
    create_res = client.post("/api/v1/registry/terminology/", json={
        "raw_term": "Term 4", "normalized_value": "term 4", "context": "Общий"
    })
    term_id = create_res.json()["data"]["id"]
    
    response = client.delete(f"/api/v1/registry/terminology/{term_id}")
    assert response.status_code == 200
    
    get_res = client.get(f"/api/v1/registry/terminology/{term_id}")
    assert get_res.status_code == 404

def test_delete_terminology_not_found(client):
    response = client.delete("/api/v1/registry/terminology/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404

def test_normalize_terminology(client):
    # First create a term
    client.post("/api/v1/registry/terminology/", json={
        "raw_term": "ML",
        "normalized_value": "machine learning",
        "context": "IT"
    })
    
    response = client.get("/api/v1/registry/terminology/normalize", params={"term": "ML", "context": "IT"})
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert data["data"]["normalized_term"] == "machine learning"

def test_normalize_terminology_not_found(client):
    response = client.get("/api/v1/registry/terminology/normalize", params={"term": "Nonexistent Term"})
    assert response.status_code == 200
    data = response.json()
    # Should return the original term if not found
    assert "data" in data

def test_normalize_terminology_with_context(client):
    # Create term with specific context
    client.post("/api/v1/registry/terminology/", json={
        "raw_term": "CPU",
        "normalized_value": "central processing unit",
        "context": "IT"
    })
    client.post("/api/v1/registry/terminology/", json={
        "raw_term": "CPU",
        "normalized_value": "chemical processing unit",
        "context": "Химия"
    })
    
    # Test with IT context
    response = client.get("/api/v1/registry/terminology/normalize", params={"term": "CPU", "context": "IT"})
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["normalized_term"] == "central processing unit"

def test_import_terminology(client):
    response = client.post("/api/v1/registry/terminology/import", params={"mapping": "some_mapping"}, files={"file": ("test.csv", b"dummy content", "text/csv")})
    assert response.status_code in [200, 201]

def test_get_terminology_with_source_filter(client):
    client.post("/api/v1/registry/terminology/", json={
        "raw_term": "Source Term 1",
        "normalized_value": "source term 1",
        "context": "IT",
        "source": "internal"
    })
    client.post("/api/v1/registry/terminology/", json={
        "raw_term": "Source Term 2",
        "normalized_value": "source term 2",
        "context": "IT",
        "source": "external"
    })
    
    response = client.get("/api/v1/registry/terminology/?source=internal")
    assert response.status_code == 200
    # The test is to ensure the endpoint accepts the parameter

def test_create_terminology_with_all_fields(client):
    payload = {
        "raw_term": "Comprehensive Term",
        "normalized_value": "comprehensive term",
        "context": "IT",
        "source": "manual"
    }
    response = client.post("/api/v1/registry/terminology/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["raw_term"] == "Comprehensive Term"
    assert data["data"]["context"] == "IT"
