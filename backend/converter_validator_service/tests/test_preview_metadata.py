PREVIEW_METADATA_FIELDS = (
    "doc_code",
    "title",
    "mks_oks_code",
    "okstu_code",
    "udk_code",
    "pkb_codes",
    "document_type",
    "year",
    "era",
    "validity_status",
    "issuing_body",
    "jurisdiction",
    "source_type",
    "language",
)


def test_preview(client, raw_gost_sample):
    response = client.post(
        "/api/v1/converter/preview",
        json={
            "task_id": 420000,
            "version_id": 420001,
            "raw_json": raw_gost_sample,
        },
    )
    assert response.status_code == 200
    data = response.json()
    for field in PREVIEW_METADATA_FIELDS:
        assert field in data
    assert data["doc_code"] == "20868-81"
    assert data["document_type"] == "normative"
    assert data["year"] == 1981
    assert data["era"] == "USSR"
    assert data["source_type"] == "GOST"
    assert data["validity_status"] == "active"
    assert data["jurisdiction"] == "RU"
    assert data["language"] == "ru"
    assert data["pkb_codes"] == []
    assert "title_hash_sha256" not in data
    assert "title_key" not in data
    assert "revision" not in data
    assert len(data["title"]) > 10
    assert data["title"] != data["doc_code"]
    assert data["issuing_body"]


def test_preview_legacy_path(client, raw_gost_sample):
    response = client.post(
        "/api/v1/converter/preview/metadata",
        json={
            "task_id": 420000,
            "version_id": 420001,
            "raw_json": raw_gost_sample,
        },
    )
    assert response.status_code == 200
    assert response.json()["doc_code"] == "20868-81"


def test_preview_empty_raw(client):
    response = client.post(
        "/api/v1/converter/preview",
        json={
            "task_id": 1,
            "version_id": 1,
            "raw_json": {},
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "METADATA_EXTRACTION_FAILED"
