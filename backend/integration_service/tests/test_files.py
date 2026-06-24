import pytest
from io import BytesIO

def test_upload_file(test_client):
    file_content = b"test content"
    response = test_client.post(
        "/api/v1/files/upload",
        files={"file": ("test.txt", BytesIO(file_content), "text/plain")},
        data={"related_document_id": "doc-123"}
    )
    assert response.status_code == 201
    data = response.json()
    assert "file_id" in data
    assert data["filename"] == "test.txt"
    assert data["mime_type"] == "text/plain"
    assert data["size"] == len(file_content)
    assert "url" in data
    assert "uploaded_at" in data

def test_get_file_info(test_client):
    file_content = b"test content"
    upload_resp = test_client.post(
        "/api/v1/files/upload",
        files={"file": ("test2.txt", BytesIO(file_content), "text/plain")}
    )
    file_id = upload_resp.json()["file_id"]
    
    info_resp = test_client.get(f"/api/v1/files/{file_id}/info")
    assert info_resp.status_code == 200
    data = info_resp.json()
    assert data["file_id"] == file_id
    assert data["filename"] == "test2.txt"

def test_get_file_info_not_found(test_client):
    info_resp = test_client.get("/api/v1/files/non-existent-file/info")
    assert info_resp.status_code == 404
    assert info_resp.json()["detail"]["error"]["code"] == "FILE_NOT_FOUND"

def test_get_file_content(test_client):
    file_content = b"test content"
    upload_resp = test_client.post(
        "/api/v1/files/upload",
        files={"file": ("test3.txt", BytesIO(file_content), "text/plain")}
    )
    file_id = upload_resp.json()["file_id"]
    
    get_resp = test_client.get(f"/api/v1/files/{file_id}")
    assert get_resp.status_code == 200
    assert get_resp.content == file_content
    assert get_resp.headers["content-type"] == "text/plain; charset=utf-8"

def test_get_file_content_not_found(test_client):
    get_resp = test_client.get("/api/v1/files/non-existent-file")
    assert get_resp.status_code == 404
    assert get_resp.json()["detail"]["error"]["code"] == "FILE_NOT_FOUND"

def test_delete_file(test_client):
    file_content = b"test content"
    upload_resp = test_client.post(
        "/api/v1/files/upload",
        files={"file": ("test4.txt", BytesIO(file_content), "text/plain")}
    )
    file_id = upload_resp.json()["file_id"]
    
    del_resp = test_client.delete(f"/api/v1/files/{file_id}")
    assert del_resp.status_code == 200
    data = del_resp.json()
    assert data["file_id"] == file_id
    assert "deleted_at" in data
    
    # Verify it's gone
    info_resp = test_client.get(f"/api/v1/files/{file_id}/info")
    assert info_resp.status_code == 404

def test_delete_file_not_found(test_client):
    del_resp = test_client.delete("/api/v1/files/non-existent-file")
    assert del_resp.status_code == 404
    assert del_resp.json()["detail"]["error"]["code"] == "FILE_NOT_FOUND"

def test_get_physical_file_not_found(test_client, tmp_path):
    import os
    
    # Upload file
    file_content = b"test content"
    upload_resp = test_client.post(
        "/api/v1/files/upload",
        files={"file": ("test5.txt", BytesIO(file_content), "text/plain")}
    )
    file_id = upload_resp.json()["file_id"]
    
    # Manually remove it physically to simulate error
    from config import settings
    for d in settings.STORAGE_DIRECTORIES:
        p = d / file_id
        if p.exists():
            os.remove(str(p))
            
    # Try to GET it
    get_resp = test_client.get(f"/api/v1/files/{file_id}")
    assert get_resp.status_code == 404
    assert get_resp.json()["detail"]["error"]["code"] == "FILE_NOT_FOUND"
    assert get_resp.json()["detail"]["error"]["message"] == "Физический файл не найден"
