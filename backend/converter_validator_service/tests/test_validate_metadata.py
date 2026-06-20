import hashlib


def test_validate_metadata_success(client):
    response = client.post(
        "/api/v1/validate/metadata",
        json={
            "era": "USSR",
            "source_type": "GOST",
            "mks_oks_code": "47.020",
            "okstu_code": None,
            "doc_code": "20868-81",
            "title": "СТОЙКИ УСТАНОВОЧНЫЕ КРЕПЕЖНЫЕ",
        },
    )
    assert response.status_code == 200
    data = response.json()
    expected_key = (
        "USSR|gost|47.020||20868-81|стойки установочные крепежные"
    )
    assert data["title_key"] == expected_key
    assert data["normalized_title"] == "стойки установочные крепежные"
    assert data["source_type_normalized"] == "gost"
    assert data["era_normalized"] == "ussr"
    assert data["title_hash_sha256"] == hashlib.sha256(
        expected_key.encode("utf-8")
    ).hexdigest()


def test_validate_metadata_invalid_era(client):
    response = client.post(
        "/api/v1/validate/metadata",
        json={
            "era": "WRONG",
            "source_type": "GOST",
            "doc_code": "20868-81",
            "title": "Test",
        },
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_validate_metadata_missing_fields(client):
    response = client.post(
        "/api/v1/validate/metadata",
        json={
            "era": "USSR",
            "source_type": "GOST",
            "doc_code": "20868-81",
        },
    )
    assert response.status_code == 422
