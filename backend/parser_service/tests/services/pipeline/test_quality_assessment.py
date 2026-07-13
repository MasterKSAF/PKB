"""
Тесты для модуля оценки качества документа (quality_assessment.py)
"""
import pytest
from app.services.pipeline.quality_assessment import assess_document_quality


def test_empty_document():
    result = assess_document_quality({}, quality_code=None)
    assert result["verdict"] == "needs_ocr"
    assert result["needs_ocr"] is True
    assert result["confidence"] == 0.0
    assert result["total_blocks"] == 0


def test_good_document():
    doc = {
        "document": {
            "pages": [{"page": 1}, {"page": 2}],
            "block": [
                {"type": "paragraph", "page": 1, "content": "Some meaningful text here"},
                {"type": "heading", "page": 1, "content": "Introduction"},
                {"type": "paragraph", "page": 2, "content": "More content on page two"},
            ],
        }
    }
    result = assess_document_quality(doc, quality_code="GOOD", total_pages=2)
    assert result["verdict"] == "good"
    assert result["needs_ocr"] is False
    assert result["page_coverage_ratio"] == 1.0
    assert result["total_blocks"] == 3


def test_bad_text_layer():
    doc = {
        "document": {
            "pages": [{"page": 1}],
            "block": [{"type": "paragraph", "page": 1, "content": "Some text"}],
        }
    }
    result = assess_document_quality(doc, quality_code="BAD", total_pages=1)
    assert result["verdict"] == "needs_ocr"
    assert result["needs_ocr"] is True
    assert "bad text layer" in result["reasons"]


def test_suspect_text_layer():
    doc = {
        "document": {
            "pages": [{"page": 1}, {"page": 2}],
            "block": [
                {"type": "paragraph", "page": 1, "content": "Text"},
            ],
        }
    }
    result = assess_document_quality(doc, quality_code="SUSPECT", total_pages=2)
    assert result["verdict"] == "partial"
    assert result["needs_ocr"] is True
    assert result["page_coverage_ratio"] == 0.5


def test_low_page_coverage():
    doc = {
        "document": {
            "pages": [{"page": 1}, {"page": 2}, {"page": 3}, {"page": 4}, {"page": 5}],
            "block": [{"type": "paragraph", "page": 1, "content": "Only page 1"}],
        }
    }
    result = assess_document_quality(doc, quality_code="GOOD", total_pages=5)
    assert result["verdict"] == "needs_ocr", f"Expected needs_ocr, got {result['verdict']}"
    assert result["needs_ocr"] is True
    assert result["page_coverage_ratio"] == 0.2
    assert "low page coverage" in result["reasons"]


def test_partial_coverage_with_good_text():
    """33% coverage with GOOD text layer → partial (not needs_ocr)."""
    doc = {
        "document": {
            "pages": [{"page": 1}, {"page": 2}, {"page": 3}],
            "block": [{"type": "paragraph", "page": 1, "content": "Only page 1 has text"}],
        }
    }
    result = assess_document_quality(doc, quality_code="GOOD", total_pages=3)
    assert result["verdict"] == "partial"
    assert result["needs_ocr"] is True


def test_mostly_empty_blocks():
    doc = {
        "document": {
            "pages": [{"page": 1}],
            "block": [
                {"type": "paragraph", "page": 1, "content": ""},
                {"type": "paragraph", "page": 1, "content": "  "},
                {"type": "heading", "page": 1, "content": ""},
            ],
        }
    }
    result = assess_document_quality(doc, quality_code="GOOD", total_pages=1)
    assert result["verdict"] == "needs_ocr"
    assert result["needs_ocr"] is True
    assert result["empty_blocks"] == 3
    assert "mostly empty blocks" in result["reasons"]


def test_formula_flag_in_blocks():
    doc = {
        "document": {
            "pages": [{"page": 1}],
            "block": [
                {"type": "paragraph", "page": 1, "content": "Text"},
                {"type": "formula", "page": 1, "content": ""},
                {"type": "table", "page": 1, "content": ""},
            ],
        }
    }
    result = assess_document_quality(doc, quality_code="GOOD", total_pages=1)
    assert result["block_types"].get("formula") == 1
    assert result["block_types"].get("table") == 1
    assert result["block_types"].get("paragraph") == 1


def test_per_page_breakdown():
    doc = {
        "document": {
            "pages": [{"page": 1}, {"page": 2}, {"page": 3}],
            "block": [
                {"type": "paragraph", "page": 1, "content": "P1"},
                {"type": "paragraph", "page": 3, "content": "P3"},
            ],
        }
    }
    result = assess_document_quality(doc, quality_code="GOOD", total_pages=3)
    assert len(result["per_page"]) == 3
    assert result["per_page"][0] == {"page": 1, "status": "ok", "blocks": 1}
    assert result["per_page"][1] == {"page": 2, "status": "empty", "blocks": 0}
    assert result["per_page"][2] == {"page": 3, "status": "ok", "blocks": 1}
