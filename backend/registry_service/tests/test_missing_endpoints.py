import pytest
import json
import io

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

def test_update_patch_terminology_nullify(client):
    create_response = client.post("/api/v1/registry/terminology", json={
        "raw_term": "T_NULL",
        "standard_term": "T_NULL",
        "normalized_value": "t_null",
        "term_type": "term",
        "definition": "Old Definition"
    })
    term_id = create_response.json()["data"]["id"]
    
    response = client.patch(f"/api/v1/registry/terminology/{term_id}", json={"definition": None})
    assert response.status_code == 200
    assert response.json()["data"].get("definition") is None

def test_pipeline_document_terminology_linking(client):
    pipeline_payload = {
        "document": {
            "metadata": {
                "title": "Pipeline Doc Term Test",
                "doc_code": "PIPE-TERM-01",
                "era": "USSR"
            },
            "content": [],
            "terminology": [
                {
                    "term": "test pipeline term",
                    "definition": "Pipeline Term Definition",
                    "normalized_term": "test pipeline term"
                }
            ],
            "references": []
        }
    }
    
    create_response = client.post("/api/v1/registry/documents", json=pipeline_payload)
    assert create_response.status_code == 201
    doc_id = create_response.json()["document_id"]
    
    # Fetch sections bundle and verify terminology is populated
    sections_response = client.get(f"/api/v1/registry/documents/{doc_id}/sections")
    assert sections_response.status_code == 200
    sections_data = sections_response.json()
    assert "terminology" in sections_data
    assert len(sections_data["terminology"]) == 1
    assert sections_data["terminology"][0]["term"] == "test pipeline term"

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


def test_document_mks_okstu_name_resolution(client):
    # 1. Create classifiers for MKS and OKSTU
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "MKS", "code": "MKS_RESOLVE", "full_name": "MKS Resolved Name"})
    client.post("/api/v1/registry/classifiers", json={"classifier_system": "OKSTU", "code": "OKSTU_RESOLVE", "full_name": "OKSTU Resolved Name"})

    # 2. Create document referencing both
    doc_payload = {
        "title": "Doc Resolve Name Test",
        "doc_code": "RESOLVE-01",
        "mks_oks_code": "MKS_RESOLVE",
        "okstu_code": "OKSTU_RESOLVE"
    }
    create_res = client.post("/api/v1/registry/documents", json=doc_payload)
    assert create_res.status_code == 201
    doc_id = create_res.json()["data"]["id"]

    # 3. Retrieve document and check populated fields
    get_res = client.get(f"/api/v1/registry/documents/{doc_id}")
    assert get_res.status_code == 200
    doc_data = get_res.json()["data"]
    assert doc_data.get("mks_name") == "MKS Resolved Name"
    assert doc_data.get("okstu_name") == "OKSTU Resolved Name"


def test_document_total_versions_count(client):
    # Create document
    doc_payload = {
        "title": "Doc Versions Test",
        "doc_code": "VERSIONS-01"
    }
    create_res = client.post("/api/v1/registry/documents", json=doc_payload)
    assert create_res.status_code == 201
    doc_id = create_res.json()["data"]["id"]

    # At first, total_versions should be 0 because no version is linked
    get_res = client.get(f"/api/v1/registry/documents/{doc_id}")
    assert get_res.status_code == 200
    assert get_res.json()["data"].get("total_versions") == 0

    # Create a pipeline document (which automatically saves a file version record)
    pipeline_payload = {
        "document": {
            "metadata": {
                "title": "Pipeline Doc Version Test",
                "doc_code": "PIPE-VERS-01",
                "era": "RF"
            },
            "source": {
                "file_name": "test_file.pdf",
                "file_hash_sha256": "abcdef123456",
                "page_count": 5
            },
            "content": [],
            "terminology": [],
            "references": []
        }
    }
    pipe_res = client.post("/api/v1/registry/documents", json=pipeline_payload)
    assert pipe_res.status_code == 201
    pipe_doc_id = pipe_res.json()["document_id"]

    # Check total_versions is 1 for the pipeline document
    get_pipe_res = client.get(f"/api/v1/registry/documents/{pipe_doc_id}")
    assert get_pipe_res.status_code == 200
    assert get_pipe_res.json()["data"].get("total_versions") == 1


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

