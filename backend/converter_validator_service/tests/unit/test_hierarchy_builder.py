from app.services.hierarchy_builder import build_hierarchy


def test_build_content_from_blocks(raw_gost_sample):
    doc = build_hierarchy(raw_gost_sample)
    assert doc["source"]["page_count"] == 2
    assert len(doc["content"]) >= 3
    types = {item["type"] for item in doc["content"]}
    assert "text" in types or "headerFooter" in types
