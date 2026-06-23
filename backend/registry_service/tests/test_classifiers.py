import pytest
import json
import io

def test_create_classifier(client):
    payload = {
        "classifier_system": "MKS",
        "code": "TEST_01",
        "full_name": "Test Classifier"
    }
    response = client.post("/api/v1/registry/classifiers", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["classifier_system"] == "MKS"
    assert data["data"]["code"] == "TEST_01"
    assert data["data"]["full_name"] == "Test Classifier"

def test_create_classifier_duplicate_code(client):
    payload = {
        "classifier_system": "MKS",
        "code": "TEST_DUP",
        "full_name": "Test Classifier"
    }
    client.post("/api/v1/registry/classifiers", json=payload)
    
    # Try to create with same code
    response = client.post("/api/v1/registry/classifiers", json=payload)
    assert response.status_code == 409

def test_create_classifier_validation_error(client):
    # Missing required field
    payload = {
        "classifier_system": "MKS",
        "code": "TEST_VAL",
        # Missing full_name
    }
    response = client.post("/api/v1/registry/classifiers", json=payload)
    assert response.status_code == 422

def test_get_classifiers(client):
    # Create multiple classifiers
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "MKS", "code": "TEST_02", "full_name": "Test 2"})
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "OKSTU", "code": "TEST_03", "full_name": "Test 3"})
    
    response = client.get("/api/v1/registry/classifiers")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 2
    assert data["meta"]["total"] >= 2

def test_get_classifiers_with_filters(client):
    # Create classifiers with different attributes
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "MKS", "code": "TEST_MKS", "full_name": "Test MKS"})
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "OKSTU", "code": "TEST_OKSTU", "full_name": "Test OKSTU"})
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "MKS", "code": "TEST_ACTIVE", "full_name": "Test Active", "status": "active"})
    
    # Filter by classifier_system
    response = client.get("/api/v1/registry/classifiers?classifier_system=MKS")
    assert response.status_code == 200
    data = response.json()
    assert all(item["classifier_system"] == "MKS" for item in data["data"])
    
    # Filter by status
    response = client.get("/api/v1/registry/classifiers?status=active")
    assert response.status_code == 200
    data = response.json()
    assert all(item["status"] == "active" for item in data["data"])

def test_get_classifiers_with_search(client):
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "MKS", "code": "TEST_SEARCH", "full_name": "Machine Learning Classifier"})
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "MKS", "code": "TEST_OTHER", "full_name": "Other Classifier"})
    
    response = client.get("/api/v1/registry/classifiers?full_name=Machine")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1
    assert "Machine" in data["data"][0]["full_name"]

def test_get_classifiers_pagination(client):
    # Create multiple classifiers
    for i in range(15):
        client.post("/api/v1/registry/classifiers", json={"classifier_system": "MKS", "code": f"TEST_PAGE_{i}", "full_name": f"Test {i}"})
    
    # Test pagination
    response = client.get("/api/v1/registry/classifiers?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) <= 10
    assert data["meta"]["page"] == 1
    assert data["meta"]["page_size"] == 10

def test_get_classifier(client):
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "MKS", "code": "TEST_03", "full_name": "Test 3"})
    
    response = client.get("/api/v1/registry/classifiers/TEST_03?classifier_system=MKS")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["code"] == "TEST_03"
    assert data["data"]["classifier_system"] == "MKS"

def test_get_classifier_not_found(client):
    response = client.get("/api/v1/registry/classifiers/NONEXISTENT?classifier_system=MKS")
    assert response.status_code == 404

def test_update_classifier(client):
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "MKS", "code": "TEST_04", "full_name": "Test 4"})
    
    update_payload = {"full_name": "Updated Test 4"}
    response = client.put("/api/v1/registry/classifiers/TEST_04?classifier_system=MKS", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["full_name"] == "Updated Test 4"

def test_update_classifier_not_found(client):
    update_payload = {"full_name": "Updated Name"}
    response = client.put("/api/v1/registry/classifiers/NONEXISTENT?classifier_system=MKS", json=update_payload)
    assert response.status_code == 404

def test_delete_classifier(client):
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "MKS", "code": "TEST_05", "full_name": "Test 5"})
    
    response = client.delete("/api/v1/registry/classifiers/TEST_05?classifier_system=MKS")
    assert response.status_code == 200
    
    # Verify it's gone
    get_response = client.get("/api/v1/registry/classifiers/TEST_05?classifier_system=MKS")
    assert get_response.status_code == 404

def test_delete_classifier_with_children(client):
    # Create parent and child
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "MKS", "code": "PARENT", "full_name": "Parent"})
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "MKS", "code": "CHILD", "full_name": "Child", "parent_code": "PARENT"})
    
    # Try to delete parent without force
    response = client.delete("/api/v1/registry/classifiers/PARENT?classifier_system=MKS")
    assert response.status_code == 409
    
    # Delete with force
    response = client.delete("/api/v1/registry/classifiers/PARENT?classifier_system=MKS&force=true")
    assert response.status_code == 200

def test_delete_classifier_not_found(client):
    response = client.delete("/api/v1/registry/classifiers/NONEXISTENT?classifier_system=MKS")
    assert response.status_code == 404

def test_get_classifier_tree(client):
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "MKS", "code": "ROOT_1", "full_name": "Root Classifier"})
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "MKS", "code": "CHILD_1", "full_name": "Child Classifier", "parent_code": "ROOT_1"})
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "MKS", "code": "CHILD_2", "full_name": "Child 2", "parent_code": "ROOT_1"})
    
    response = client.get("/api/v1/registry/classifiers/tree?classifier_system=MKS")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data.get("data"), list)

def test_get_classifier_tree_with_root(client):
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "MKS", "code": "ROOT_A", "full_name": "Root A"})
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "MKS", "code": "ROOT_B", "full_name": "Root B"})
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "MKS", "code": "CHILD_A", "full_name": "Child A", "parent_code": "ROOT_A"})
    
    response = client.get("/api/v1/registry/classifiers/tree?classifier_system=MKS&root_code=ROOT_A")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1

def test_get_classifier_tree_with_search(client):
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "MKS", "code": "ROOT_SEARCH", "full_name": "Machine Learning Root"})
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "MKS", "code": "CHILD_SEARCH", "full_name": "ML Child", "parent_code": "ROOT_SEARCH"})
    
    response = client.get("/api/v1/registry/classifiers/tree?classifier_system=MKS&search=Machine")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1

def test_patch_classifier(client):
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "MKS", "code": "TEST_PATCH", "full_name": "Original Name"})
    
    response = client.patch("/api/v1/registry/classifiers/TEST_PATCH?classifier_system=MKS", json={"full_name": "Patched Name"})
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["full_name"] == "Patched Name"

def test_patch_classifier_not_found(client):
    response = client.patch("/api/v1/registry/classifiers/NONEXISTENT?classifier_system=MKS", json={"full_name": "Patched Name"})
    assert response.status_code == 404

def test_import_classifiers(client):
    # Dummy file upload test
    response = client.post("/api/v1/registry/classifiers/import?classifier_system=MKS&mapping=some_mapping", files={"file": ("test.csv", b"dummy content", "text/csv")})
    assert response.status_code in [200, 201]

def test_get_classifiers_with_parent_filter(client):
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "MKS", "code": "PARENT_FILTER", "full_name": "Parent Filter"})
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "MKS", "code": "CHILD_FILTER", "full_name": "Child Filter", "parent_code": "PARENT_FILTER"})
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "MKS", "code": "ROOT_FILTER", "full_name": "Root Filter"})
    
    response = client.get("/api/v1/registry/classifiers?parent_code=PARENT_FILTER")
    assert response.status_code == 200
    data = response.json()
    assert all(item["parent_code"] == "PARENT_FILTER" for item in data["data"])


def test_classifier_tree_hierarchical(client):
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "MKS", "code": "H_ROOT", "full_name": "Hierarchical Root"})
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "MKS", "code": "H_ROOT.CHILD1", "full_name": "Child 1", "parent_code": "H_ROOT"})
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "MKS", "code": "H_ROOT.CHILD1.GRANDCHILD", "full_name": "Grandchild", "parent_code": "H_ROOT.CHILD1"})
    
    # Test max_depth = 1 (should not include grandchild)
    response = client.get("/api/v1/registry/classifiers/tree?classifier_system=MKS&max_depth=2&root_code=H_ROOT")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["code"] == "H_ROOT"
    assert len(data[0]["children"]) == 1
    assert data[0]["children"][0]["code"] == "H_ROOT.CHILD1"
    # depth limit reached
    assert len(data[0]["children"][0]["children"]) == 0


def test_create_classifier_with_effective_date(client):
    payload = {
        "classifier_system": "MKS",
        "code": "EFF_01",
        "full_name": "Effective Date Test",
        "effective_date": "2026-06-08T00:00:00"
    }
    response = client.post("/api/v1/registry/classifiers", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["effective_date"] == "2026-06-08"


def test_delete_classifier_has_documents(client):
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "MKS", "code": "MKS_REF", "full_name": "Referenced Classifier"})
    # Create document referencing it
    client.post("/api/v1/registry/documents", json={
        "title": "Document Ref Test",
        "doc_code": "DOC_REF_01",
        "mks_oks_code": "MKS_REF"
    })
    
    # Delete should fail with HAS_DOCUMENTS
    response = client.delete("/api/v1/registry/classifiers/MKS_REF?classifier_system=MKS")
    assert response.status_code == 409
    assert response.json()["detail"]["error"]["code"] == "HAS_DOCUMENTS"


def test_pending_suggested_parent(client, db_session):
    # Setup parent classifier
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "MKS", "code": "47.020", "full_name": "Parent Section"})
    
    # Add pending quarantine item
    from api.v1.crud.classifier import create_classifier_pending
    create_classifier_pending(db_session, system="MKS", code="47.020.99")
        
    response = client.get("/api/v1/registry/classifiers/pending")
    assert response.status_code == 200
    data = response.json()["data"]
    item = next(x for x in data if x["code"] == "47.020.99")
    assert item["suggested_parent_code"] == "47.020"
    assert item["suggested_parent_name"] == "Parent Section"


def test_delete_classifier_udc_has_documents(client):
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "UDC", "code": "UDC_REF", "full_name": "Referenced UDC"})
    # Create document referencing it
    client.post("/api/v1/registry/documents", json={
        "title": "Document UDC Ref Test",
        "doc_code": "DOC_UDC_01",
        "udk_code": "UDC_REF"
    })
    
    # Delete without force should fail
    response = client.delete("/api/v1/registry/classifiers/UDC_REF?classifier_system=UDC")
    assert response.status_code == 409
    assert response.json()["detail"]["error"]["code"] == "HAS_DOCUMENTS"

    # Delete with force should succeed
    response = client.delete("/api/v1/registry/classifiers/UDC_REF?classifier_system=UDC&force=true")
    assert response.status_code == 200


def test_delete_classifier_external_has_documents(client):
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "EXTERNAL", "code": "EXT_REF", "full_name": "Referenced External"})
    # Create document referencing it
    client.post("/api/v1/registry/documents", json={
        "title": "Document External Ref Test",
        "doc_code": "DOC_EXT_01",
        "classifier_code": "EXT_REF"
    })
    
    # Delete without force should fail
    response = client.delete("/api/v1/registry/classifiers/EXT_REF?classifier_system=EXTERNAL")
    assert response.status_code == 409
    assert response.json()["detail"]["error"]["code"] == "HAS_DOCUMENTS"

    # Delete with force should succeed
    response = client.delete("/api/v1/registry/classifiers/EXT_REF?classifier_system=EXTERNAL&force=true")
    assert response.status_code == 200




def test_classifier_code_filtering(client):
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "MKS", "code": "ABC.01", "full_name": "Test ABC"})
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "MKS", "code": "XYZ.01", "full_name": "Test XYZ"})
    
    response = client.get("/api/v1/registry/classifiers?code=ABC")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["code"] == "ABC.01"



def test_classifier_tree_metadata(client):
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "MKS", "code": "T_ROOT", "full_name": "Tree Root"})
    
    response = client.get("/api/v1/registry/classifiers/tree?classifier_system=MKS")
    assert response.status_code == 200
    res = response.json()
    assert "meta" in res
    assert res["meta"]["total"] >= 1
    assert res["meta"]["max_depth_reached"] is False



def test_classifier_get_children(client):
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "MKS", "code": "P_NODE", "full_name": "Parent Node"})
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "MKS", "code": "C_NODE", "full_name": "Child Node", "parent_code": "P_NODE"})
    
    response = client.get("/api/v1/registry/classifiers/P_NODE?classifier_system=MKS")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "children" in data
    assert len(data["children"]) == 1
    assert data["children"][0]["code"] == "C_NODE"



def test_create_classifier_parent_not_found(client):
    payload = {
        "classifier_system": "MKS",
        "code": "TEST_INVALID_PARENT",
        "full_name": "Invalid Parent",
        "parent_code": "NON_EXISTENT_PARENT"
    }
    response = client.post("/api/v1/registry/classifiers", json=payload)
    assert response.status_code == 404
    assert response.json()["detail"]["error"]["code"] == "PARENT_NOT_FOUND"



def test_update_patch_classifier_nullify(client):
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "MKS", "code": "PARENT_X", "full_name": "Parent X"})
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "MKS", "code": "NODE_Y", "full_name": "Node Y", "parent_code": "PARENT_X"})
    
    # Nullify parent_code using PATCH
    response = client.patch("/api/v1/registry/classifiers/NODE_Y?classifier_system=MKS", json={"parent_code": None})
    assert response.status_code == 200
    assert response.json()["data"].get("parent_code") is None



def test_csv_imports(client):
    # Test classifier CSV import
    csv_data = "Code,Name,Parent\nIMP_01,Imported 1,\nIMP_02,Imported 2,IMP_01\n"
    mapping = json.dumps({"code": "Code", "full_name": "Name", "parent_code": "Parent"})
    response = client.post(
        "/api/v1/registry/classifiers/import?classifier_system=MKS&mapping=" + mapping,
        files={"file": ("test.csv", io.BytesIO(csv_data.encode('utf-8')), "text/csv")}
    )
    assert response.status_code == 200
    res = response.json()["data"]
    assert res["inserted"] == 2
    assert res["updated"] == 0
    assert len(res["errors"]) == 0




def test_create_classifier_cross_system_parent(client):
    # 1. Create a parent classifier in OKSTU system
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "OKSTU", "code": "OKSTU_P", "full_name": "OKSTU Parent"})

    # 2. Try creating a classifier in MKS system with parent_code referencing the OKSTU parent
    payload = {
        "classifier_system": "MKS",
        "code": "MKS_C",
        "full_name": "MKS Child",
        "parent_code": "OKSTU_P"
    }
    response = client.post("/api/v1/registry/classifiers", json=payload)
    assert response.status_code == 409
    assert response.json()["detail"]["error"]["code"] == "CROSS_SYSTEM_PARENT"

