import pytest
from fastapi.testclient import TestClient

def test_create_draft(client):
    payload = {
        "file_key": "f-123",
        "document_key": "doc-123",
        "status": "uploaded",
        "raw_data": {"test": "data"},
        "created_by": "orchestrator"
    }
    response = client.post("/api/v1/registry/drafts", json=payload)
    assert response.status_code == 201
    data = response.json()["data"]
    assert "id" in data
    assert data["file_key"] == "f-123"
    assert data["document_key"] == "doc-123"
    assert data["status"] == "uploaded"
    assert data["raw_data"] == {"test": "data"}

def test_list_drafts(client):
    payload = {
        "file_key": "f-list",
        "document_key": "doc-list",
        "status": "uploaded",
        "created_by": "orchestrator"
    }
    client.post("/api/v1/registry/drafts", json=payload)
    
    response = client.get("/api/v1/registry/drafts?status=uploaded")
    assert response.status_code == 200
    data = response.json()["data"]
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["status"] == "uploaded"

def test_get_draft(client):
    # First create one to fetch
    payload = {
        "file_key": "f-fetch",
        "document_key": "doc-fetch",
        "status": "uploaded",
        "created_by": "orchestrator"
    }
    res = client.post("/api/v1/registry/drafts", json=payload).json()["data"]
    draft_id = res["id"]

    response = client.get(f"/api/v1/registry/drafts/{draft_id}")
    assert response.status_code == 200
    assert response.json()["data"]["id"] == draft_id
    assert response.json()["data"]["file_key"] == "f-fetch"

def test_get_draft_preview(client):
    payload = {
        "file_key": "f-prev",
        "document_key": "doc-prev",
        "status": "uploaded",
        "raw_data": {"hidden": True},
        "created_by": "orchestrator"
    }
    res = client.post("/api/v1/registry/drafts", json=payload).json()["data"]
    draft_id = res["id"]

    response = client.get(f"/api/v1/registry/drafts/{draft_id}/preview")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == draft_id
    # Ensure hidden fields are not in preview
    assert "raw_data" not in data
    assert "document_key" not in data

def test_patch_draft_status(client):
    payload = {
        "file_key": "f-stat",
        "document_key": "doc-stat",
        "status": "previewing",
        "created_by": "orchestrator"
    }
    res = client.post("/api/v1/registry/drafts", json=payload).json()["data"]
    draft_id = res["id"]

    patch_payload = {
        "status": "ready_for_approve",
        "confidence": 0.95,
        "preview_metadata": {"title": "Test Title"},
        "updated_by": "orchestrator"
    }
    response = client.patch(f"/api/v1/registry/drafts/{draft_id}/status", json=patch_payload)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "ready_for_approve"
    assert data["previous_status"] == "previewing"

def test_patch_draft_metadata(client):
    payload = {
        "file_key": "f-meta",
        "document_key": "doc-meta",
        "status": "ready_for_approve",
        "created_by": "orchestrator"
    }
    res = client.post("/api/v1/registry/drafts", json=payload).json()["data"]
    draft_id = res["id"]

    patch_payload = {
        "preview_metadata": {"title": "Updated Title"},
        "metadata_overrides": {"valid_from": "2026-01-01"},
        "updated_by": "orchestrator"
    }
    response = client.patch(f"/api/v1/registry/drafts/{draft_id}/metadata", json=patch_payload)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["preview_metadata"]["title"] == "Updated Title"
    assert data["preview_metadata"]["metadata_overrides"]["valid_from"] == "2026-01-01"

def test_delete_draft(client):
    payload = {
        "file_key": "f-del",
        "document_key": "doc-del",
        "status": "uploaded",
        "created_by": "orchestrator"
    }
    res = client.post("/api/v1/registry/drafts", json=payload).json()["data"]
    draft_id = res["id"]

    response = client.delete(f"/api/v1/registry/drafts/{draft_id}")
    assert response.status_code == 200

    # Ensure it's deleted
    get_res = client.get(f"/api/v1/registry/drafts/{draft_id}")
    assert get_res.status_code == 404
