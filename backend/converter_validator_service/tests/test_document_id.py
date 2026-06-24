def test_convert_with_explicit_document_id(client, raw_gost_sample):
    response = client.post(
        "/api/v1/converter/convert",
        json={
            "task_id": 420000,
            "version_id": 420001,
            "document_id": 1001,
            "raw_json": raw_gost_sample,
        },
    )
    assert response.status_code == 200
    assert response.json()["document_id"] == 1001
