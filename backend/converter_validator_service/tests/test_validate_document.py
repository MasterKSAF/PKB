from app.services.document_validator import _decision, _metadata_quality_ok


def test_metadata_quality_ok_good():
    """Нормальные метаданные с годом → True."""
    meta = {"doc_code": "ГОСТ 1234-56", "title": "Документ", "year": 1995}
    assert _metadata_quality_ok(meta) is True


def test_metadata_quality_ok_year_missing():
    """Год отсутствует → False."""
    meta = {"doc_code": "ГОСТ 1234-56", "title": "Документ", "year": None}
    assert _metadata_quality_ok(meta) is False


def test_metadata_quality_ok_year_out_of_range():
    """Год 174 вне диапазона → False."""
    meta = {"doc_code": "2-020101-174", "title": "Чертёж", "year": 174}
    assert _metadata_quality_ok(meta) is False


def test_metadata_quality_ok_title_empty():
    """Пустой title → False."""
    meta = {"doc_code": "ГОСТ 1234-56", "title": "", "year": 2024}
    assert _metadata_quality_ok(meta) is False


def test_metadata_quality_ok_title_too_short():
    """Title короче 5 символов → False."""
    meta = {"doc_code": "ГОСТ 1234-56", "title": "ABC", "year": 2024}
    assert _metadata_quality_ok(meta) is False


def test_metadata_quality_ok_title_is_filename():
    """Title c .pdf → False."""
    meta = {"doc_code": "2-020101-004", "title": "2-020101-004.pdf", "year": 2024}
    assert _metadata_quality_ok(meta) is False


def test_metadata_quality_ok_doc_code_is_filename():
    """doc_code c .pdf → False."""
    meta = {"doc_code": "2-020101-004.pdf", "title": "Чертёж", "year": 2024}
    assert _metadata_quality_ok(meta) is False


def test_decision_structure_false():
    """structure_valid=False → review_required."""
    assert _decision(False, {"overall_status": "CONFIRMED"}) == "review_required"


def test_decision_metadata_bad():
    """metadata_quality=False → review_required (даже при CONFIRMED)."""
    assert _decision(True, {"overall_status": "CONFIRMED"}, metadata_quality=False) == "review_required"


def test_decision_auto():
    """Всё хорошо → auto."""
    assert _decision(True, {"overall_status": "CONFIRMED"}) == "auto"


def test_decision_unclassified():
    """Не CONFIRMED → review_required."""
    assert _decision(True, {"overall_status": "UNCLASSIFIED"}) == "review_required"


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
