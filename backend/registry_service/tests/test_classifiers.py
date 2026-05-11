import pytest

def test_create_classifier(client):
    payload = {
        "code": "TEST_01",
        "full_name": "Test Classifier",
        "doc_type": "OKS",
        "jurisdiction": "RF",
        "language": "ru"
    }
    response = client.post("/api/v1/registry/classifiers/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["code"] == "TEST_01"
    assert data["data"]["full_name"] == "Test Classifier"

def test_get_classifiers(client):
    # Create one first
    client.post("/api/v1/registry/classifiers/", json={"code": "TEST_02", "full_name": "Test 2"})
    
    response = client.get("/api/v1/registry/classifiers/")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1
    assert data["meta"]["total"] >= 1

def test_get_classifier(client):
    client.post("/api/v1/registry/classifiers/", json={"code": "TEST_03", "full_name": "Test 3"})
    
    response = client.get("/api/v1/registry/classifiers/TEST_03")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["code"] == "TEST_03"

def test_update_classifier(client):
    client.post("/api/v1/registry/classifiers/", json={"code": "TEST_04", "full_name": "Test 4"})
    
    update_payload = {"full_name": "Updated Test 4"}
    response = client.put("/api/v1/registry/classifiers/TEST_04", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["full_name"] == "Updated Test 4"

def test_delete_classifier(client):
    client.post("/api/v1/registry/classifiers/", json={"code": "TEST_05", "full_name": "Test 5"})
    
    response = client.delete("/api/v1/registry/classifiers/TEST_05")
    assert response.status_code == 200
    
    # Verify it's gone
    get_response = client.get("/api/v1/registry/classifiers/TEST_05")
    assert get_response.status_code == 404

def test_get_classifier_tree(client):
    client.post("/api/v1/registry/classifiers/", json={"code": "ROOT_1", "full_name": "Root Classifier"})
    client.post("/api/v1/registry/classifiers/", json={"code": "CHILD_1", "full_name": "Child Classifier", "parent_code": "ROOT_1"})
    
    response = client.get("/api/v1/registry/classifiers/tree")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data.get("data"), list)

def test_patch_classifier(client):
    client.post("/api/v1/registry/classifiers/", json={"code": "TEST_PATCH", "full_name": "Original Name"})
    
    response = client.patch("/api/v1/registry/classifiers/TEST_PATCH", json={"full_name": "Patched Name"})
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["full_name"] == "Patched Name"

def test_import_classifiers(client):
    # Dummy file upload test
    response = client.post("/api/v1/registry/classifiers/import", params={"mapping": "some_mapping"}, files={"file": ("test.csv", b"dummy content", "text/csv")})
    assert response.status_code in [200, 201]
