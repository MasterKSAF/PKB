from app.services.metadata_extractor import extract_preview_metadata


def test_extract_from_gost_header(raw_gost_sample):
    meta = extract_preview_metadata(raw_gost_sample)
    assert "ГОСТ" in meta["doc_code"]
    assert meta["document_type"] == "normative"
    assert meta["year"] == "1981"
