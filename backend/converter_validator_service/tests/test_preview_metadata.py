def test_preview_metadata(client, raw_gost_sample):
    response = client.post(
        "/api/v1/converter/preview/metadata",
        json={
            "task_id": "task-8a3f2b",
            "version_id": "c4b9f2d3-0000-0000-0000-000000000001",
            "raw_json": raw_gost_sample,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "20868-81" in data["doc_code"]
    assert data["document_type"] == "normative"
    assert data["year"] == "1981"
    assert len(data["title"]) > 10
    assert data["title"] != data["doc_code"]


def test_preview_metadata_empty_raw(client):
    response = client.post(
        "/api/v1/converter/preview/metadata",
        json={
            "task_id": "task-1",
            "version_id": "v1",
            "raw_json": {},
        },
    )
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "CONVERSION_FAILED"
