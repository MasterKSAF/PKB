def test_validate_document_from_raw(client, raw_gost_sample):
    response = client.post(
        "/api/v1/validate/document",
        json={
            "task_id": 420000,
            "version_id": 420001,
            "raw_json": raw_gost_sample,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["structure_valid"] is True
    assert data["validation_id"].startswith("val-")
    assert data["document_id"] is None
    assert data["fingerprint"]["title_hash_sha256"]
    assert data["fingerprint"]["title_key"]


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}
