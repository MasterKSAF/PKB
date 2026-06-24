from app.services.metadata_extractor import extract_preview_metadata


def test_extract_from_gost_header(raw_gost_sample):
    meta = extract_preview_metadata(raw_gost_sample)
    assert meta["doc_code"] == "20868-81"
    assert meta["document_type"] == "normative"
    assert meta["year"] == 1981
    assert meta["era"] == "USSR"
    assert meta["source_type"] == "GOST"
    assert meta["validity_status"] == "active"
    assert meta["jurisdiction"] == "RU"
    assert meta["language"] == "ru"
    assert meta["pkb_codes"] == []
    assert meta["issuing_body"]
