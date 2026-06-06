def test_validate_document_from_raw(client, raw_gost_sample):
    response = client.post(
        "/api/v1/validate/document",
        json={
            "task_id": "task-8a3f2b",
            "version_id": "c4b9f2d3-0000-0000-0000-000000000001",
            "raw_json": raw_gost_sample,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["structure_valid"] is True
    assert data["validation_id"].startswith("val-")
    assert data["document_id"]
    assert data["fingerprint"]["title_hash_sha256"]


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}
