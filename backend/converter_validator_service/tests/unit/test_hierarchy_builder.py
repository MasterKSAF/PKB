from app.services.hierarchy_builder import build_hierarchy, _build_page_size_cache


def test_build_content_from_blocks(raw_gost_sample):
    doc = build_hierarchy(raw_gost_sample)
    assert doc["source"]["page_count"] == 2
    assert len(doc["content"]) >= 3
    types = {item["type"] for item in doc["content"]}
    assert "text" in types or "headerFooter" in types


def test_page_size_cache_builds_mapping(raw_gost_sample):
    """_build_page_size_cache creates {page: (width, height)}."""
    cache = _build_page_size_cache(raw_gost_sample)
    assert len(cache) == 2
    assert cache[1] == (210.0, 297.0)
    assert cache[2] == (210.0, 297.0)


def test_page_size_cache_empty():
    """_build_page_size_cache handles missing pages."""
    cache = _build_page_size_cache({"document": {}})
    assert cache == {}


def test_page_size_cache_ignores_invalid_pages():
    """_build_page_size_cache skips pages without page number."""
    raw = {"document": {"pages": [{"width": 300}, {"page": 1, "width": 210}]}}
    cache = _build_page_size_cache(raw)
    assert len(cache) == 1
    assert cache[1][0] == 210.0


def test_build_hierarchy_no_deepcopy_mutation():
    """build_hierarchy does not require deepcopy - reads fields directly."""
    raw = {
        "document": {
            "source": {"file_name": "test.pdf", "file_hash_sha256": "abc", "page_count": 5},
            "block": [],
        }
    }
    doc = build_hierarchy(raw)
    assert doc["source"]["file_name"] == "test.pdf"
    assert doc["source"]["file_hash_sha256"] == "abc"
    assert doc["source"]["page_count"] == 5
    assert doc["content"] == []


def test_build_hierarchy_inline_references(raw_gost_sample):
    """GOST references are extracted inline during the main loop."""
    doc = build_hierarchy(raw_gost_sample)
    refs = doc["references"]
    assert len(refs) >= 1
    assert any("20862" in r["target_doc_code"] for r in refs), \
        f"Expected ГОСТ 20862 reference, got: {refs}"


def test_build_hierarchy_preserves_existing_references():
    """When document already has references, inline extraction is skipped."""
    existing_ref = {"target_doc_code": "ГОСТ 1234", "type": "single"}
    raw = {
        "document": {
            "source": {"file_name": "x.pdf", "file_hash_sha256": "x", "page_count": 1},
            "block": [
                {"type": "paragraph", "content": "text with ГОСТ 20862-81", "page": 1},
            ],
            "references": [existing_ref],
        }
    }
    doc = build_hierarchy(raw)
    # Should NOT extract ГОСТ 20862 because references were already present
    assert len(doc["references"]) == 1
    assert doc["references"][0]["target_doc_code"] == "ГОСТ 1234"


def test_build_hierarchy_without_source():
    """build_hierarchy handles missing source gracefully."""
    raw = {"document": {"block": []}}
    doc = build_hierarchy(raw)
    assert doc["source"]["file_name"] == ""
    assert doc["source"]["file_hash_sha256"] == ""
    assert doc["source"]["page_count"] == 1
