def test_convert_full_cycle(client, raw_gost_sample):
    response = client.post(
        "/api/v1/converter/convert",
        json={
            "task_id": "task-8a3f2b",
            "version_id": "c4b9f2d3-0000-0000-0000-000000000001",
            "use_llm": False,
            "raw_json": raw_gost_sample,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == "task-8a3f2b"
    assert data["metadata"]["schema"] == "validated_v3"
    assert data["document"]["content"]
    assert data["validation"]["structure_valid"] is True
    assert data["validation"]["status"] == "completed"
    assert "document_id" in data


def test_convert_with_references(client, raw_gost_sample):
    response = client.post(
        "/api/v1/converter/convert",
        json={
            "task_id": "task-ref",
            "version_id": "v-ref",
            "raw_json": raw_gost_sample,
        },
    )
    refs = response.json()["document"]["references"]
    assert len(refs) >= 1
    assert any("20862" in r["target_doc_code"] for r in refs)
