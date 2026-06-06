import pytest

def test_create_terminology(client):
    payload = {
        "raw_term": "Machine Learning",
        "standard_term": "Machine Learning",
        "normalized_value": "machine learning",
        "term_type": "term"
    }
    response = client.post("/api/v1/registry/terminology/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["raw_term"] == "Machine Learning"
    assert data["data"]["standard_term"] == "Machine Learning"
    assert "id" in data["data"]

def test_create_terminology_duplicate(client):
    payload = {
        "raw_term": "Duplicate Term",
        "standard_term": "Duplicate Term",
        "normalized_value": "duplicate term",
        "term_type": "term"
    }
    client.post("/api/v1/registry/terminology/", json=payload)
    
    # Try to create with same raw_term
    response = client.post("/api/v1/registry/terminology/", json=payload)
    assert response.status_code == 409

def test_create_terminology_validation_error(client):
    # Missing required field
    payload = {
        # Missing raw_term
        "standard_term": "Test Term",
        "normalized_value": "test term",
        "term_type": "term"
    }
    response = client.post("/api/v1/registry/terminology/", json=payload)
    assert response.status_code == 422

def test_get_terminology(client):
    client.post("/api/v1/registry/terminology/", json={
        "raw_term": "Test Term", "standard_term": "Test Term", "normalized_value": "test term", "term_type": "term"
    })
    client.post("/api/v1/registry/terminology/", json={
        "raw_term": "Another Term", "standard_term": "Another Term", "normalized_value": "another term", "term_type": "term"
    })
    
    response = client.get("/api/v1/registry/terminology/")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 2
    assert data["meta"]["total"] >= 2

def test_get_terminology_with_filters(client):
    client.post("/api/v1/registry/terminology/", json={
        "raw_term": "IT Term 1", "standard_term": "IT Term 1", "normalized_value": "it term 1", "term_type": "acronym"
    })
    client.post("/api/v1/registry/terminology/", json={
        "raw_term": "Building Term", "standard_term": "Building Term", "normalized_value": "building term", "term_type": "term"
    })
    client.post("/api/v1/registry/terminology/", json={
        "raw_term": "IT Term 2", "standard_term": "IT Term 2", "normalized_value": "it term 2", "term_type": "acronym"
    })
    
    # Filter by term_type
    response = client.get("/api/v1/registry/terminology/?term_type=acronym")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 2

def test_get_terminology_with_search(client):
    client.post("/api/v1/registry/terminology/", json={
        "raw_term": "Machine Learning", "standard_term": "Machine Learning", "normalized_value": "machine learning", "term_type": "term"
    })
    client.post("/api/v1/registry/terminology/", json={
        "raw_term": "Deep Learning", "standard_term": "Deep Learning", "normalized_value": "deep learning", "term_type": "term"
    })
    client.post("/api/v1/registry/terminology/", json={
        "raw_term": "Other Concept", "standard_term": "Other Concept", "normalized_value": "other concept", "term_type": "term"
    })
    
    response = client.get("/api/v1/registry/terminology/?raw_term=Machine")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1
    assert "Machine" in data["data"][0]["raw_term"]

def test_get_terminology_with_normalized_filter(client):
    client.post("/api/v1/registry/terminology/", json={
        "raw_term": "ML", "standard_term": "ML", "normalized_value": "ml", "term_type": "acronym"
    })
    client.post("/api/v1/registry/terminology/", json={
        "raw_term": "AI", "standard_term": "AI", "normalized_value": "ai", "term_type": "acronym"
    })
    
    response = client.get("/api/v1/registry/terminology/?normalized_term=ml")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1
    assert data["data"][0]["normalized_value"] == "ml"

def test_get_terminology_with_is_blocked_filter(client):
    client.post("/api/v1/registry/terminology/", json={
        "raw_term": "Active Term", "standard_term": "Active Term", "normalized_value": "active term", "term_type": "term", "is_blocked": False
    })
    client.post("/api/v1/registry/terminology/", json={
        "raw_term": "Blocked Term", "standard_term": "Blocked Term", "normalized_value": "blocked term", "term_type": "term", "is_blocked": True
    })
    
    response = client.get("/api/v1/registry/terminology/?is_blocked=false")
    assert response.status_code == 200
    data = response.json()
    assert all(item["is_blocked"] == False for item in data["data"])

def test_get_terminology_pagination(client):
    # Create multiple terms
    for i in range(15):
        client.post("/api/v1/registry/terminology/", json={
            "raw_term": f"Term {i}", "standard_term": f"Term {i}", "normalized_value": f"term {i}", "term_type": "term"
        })
    
    # Test pagination
    response = client.get("/api/v1/registry/terminology/?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) <= 10
    assert data["meta"]["page"] == 1
    assert data["meta"]["page_size"] == 10

def test_get_terminology_by_id(client):
    create_response = client.post("/api/v1/registry/terminology/", json={
        "raw_term": "Specific Term", "standard_term": "Specific Term", "normalized_value": "specific term", "term_type": "term"
    })
    term_id = create_response.json()["data"]["id"]
    
    response = client.get(f"/api/v1/registry/terminology/{term_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["raw_term"] == "Specific Term"

def test_get_terminology_not_found(client):
    response = client.get("/api/v1/registry/terminology/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404

def test_update_terminology(client):
    create_response = client.post("/api/v1/registry/terminology/", json={
        "raw_term": "Original Term", "standard_term": "Original Term", "normalized_value": "original term", "term_type": "term"
    })
    term_id = create_response.json()["data"]["id"]
    
    update_payload = {"standard_term": "Updated Term"}
    response = client.put(f"/api/v1/registry/terminology/{term_id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["standard_term"] == "Updated Term"

def test_update_terminology_not_found(client):
    update_payload = {"standard_term": "Updated Term"}
    response = client.put("/api/v1/registry/terminology/00000000-0000-0000-0000-000000000000", json=update_payload)
    assert response.status_code == 404

def test_delete_terminology(client):
    create_response = client.post("/api/v1/registry/terminology/", json={
        "raw_term": "To Delete", "standard_term": "To Delete", "normalized_value": "to delete", "term_type": "term"
    })
    term_id = create_response.json()["data"]["id"]
    
    response = client.delete(f"/api/v1/registry/terminology/{term_id}")
    assert response.status_code == 200
    
    # Verify it's gone
    get_response = client.get(f"/api/v1/registry/terminology/{term_id}")
    assert get_response.status_code == 404

def test_delete_terminology_not_found(client):
    response = client.delete("/api/v1/registry/terminology/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404

def test_normalize_terminology(client):
    client.post("/api/v1/registry/terminology/", json={
        "raw_term": "CPU", "standard_term": "CPU", "normalized_value": "cpu", "term_type": "acronym"
    })
    
    response = client.get("/api/v1/registry/terminology/normalize?term=CPU")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["raw_term"] == "CPU"
    assert data["data"]["normalized_value"] == "cpu"
    assert data["data"]["term_type"] == "acronym"

def test_normalize_terminology_not_found(client):
    response = client.get("/api/v1/registry/terminology/normalize?term=NonExistent")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["raw_term"] == "NonExistent"
    assert data["data"]["term_type"] == "unknown"

def test_patch_terminology(client):
    create_response = client.post("/api/v1/registry/terminology/", json={
        "raw_term": "Patch Term", "standard_term": "Patch Term", "normalized_value": "patch term", "term_type": "term"
    })
    term_id = create_response.json()["data"]["id"]
    
    response = client.patch(f"/api/v1/registry/terminology/{term_id}", json={"definition": "This is a patch test"})
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["definition"] == "This is a patch test"

def test_import_terminology(client):
    # Dummy file upload test
    response = client.post("/api/v1/registry/terminology/import?mapping=some_mapping", files={"file": ("test.csv", b"dummy content", "text/csv")})
    assert response.status_code in [200, 201]
