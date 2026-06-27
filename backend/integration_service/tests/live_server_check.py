"""
Docker-зависимые интеграционные тесты Integration Service.
Запускаются только через recheck.bat (не собираются pytest по умолчанию).

Целевой сервер задаётся через LIVE_SERVER_URL.
По умолчанию: http://localhost:8100 (поднят в Docker).
"""

import os
import httpx
from io import BytesIO

LIVE_SERVER_URL = os.getenv("LIVE_SERVER_URL", "http://localhost:8100")
BASE_URL = f"{LIVE_SERVER_URL.rstrip('/')}/api/v1"


def test_live_upload_and_lifecycle():
    """
    Полный цикл файла на живом сервере:
    1. Upload
    2. Get Info
    3. Download
    4. Delete
    5. Verify Deletion
    """
    file_content = b"hello from live test"
    files = {"file": ("livetest.txt", BytesIO(file_content), "text/plain")}
    data = {"related_document_id": "doc-live-test"}

    with httpx.Client() as client:
        upload_resp = client.post(f"{BASE_URL}/files/upload", files=files, data=data)
        assert upload_resp.status_code == 201, f"Upload failed: {upload_resp.text}"

        upload_data = upload_resp.json()
        assert "file_id" in upload_data
        file_id = upload_data["file_id"]

        info_resp = client.get(f"{BASE_URL}/files/{file_id}/info")
        assert info_resp.status_code == 200, f"Get info failed: {info_resp.text}"
        info_data = info_resp.json()
        assert info_data["filename"] == "livetest.txt"
        assert info_data["size"] == len(file_content)

        dl_resp = client.get(f"{BASE_URL}/files/{file_id}")
        assert dl_resp.status_code == 200, f"Download failed: {dl_resp.text}"
        assert dl_resp.content == file_content

        del_resp = client.delete(f"{BASE_URL}/files/{file_id}")
        assert del_resp.status_code == 200, f"Delete failed: {del_resp.text}"

        verify_resp = client.get(f"{BASE_URL}/files/{file_id}/info")
        assert verify_resp.status_code == 404, "File should be deleted"


def test_live_meridian_export():
    payload = {
        "document_id": "doc-live-export",
        "data": {
            "designation": "LIVE-TEST",
            "title": "Live Test Title",
            "materials": ["Material 1"],
            "dimensions": "10x10",
            "specification_items": [{"position": 1, "name": "Test Item", "quantity": 1}],
        },
    }

    with httpx.Client() as client:
        resp = client.post(f"{BASE_URL}/meridian/export", json=payload)
        assert resp.status_code == 200, f"Export failed: {resp.text}"
        data = resp.json()
        assert "export_id" in data
        assert data["status"] == "sent"


def test_live_external_status():
    with httpx.Client() as client:
        resp = client.get(f"{BASE_URL}/external/status")
        assert resp.status_code == 200, f"Status failed: {resp.text}"
        data = resp.json()
        assert "systems" in data
        assert len(data["systems"]) > 0
        assert data["systems"][0]["api_name"] == "meridian"
