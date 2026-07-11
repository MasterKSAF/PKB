from __future__ import annotations

from convertor_validator_service_lama.services.document_structure_assembler import (
    assemble_document_structure_from_parse_items,
)


def _heading(md: str, page: int, index: int) -> dict:
    return {
        "type": "heading",
        "md": md,
        "page_number": page,
        "page_width": 100.0,
        "page_height": 200.0,
        "bbox": [{"x": 10.0, "y": float(index), "w": 80.0, "h": 10.0}],
    }


def _text(text: str, page: int, index: int) -> dict:
    return {
        "type": "text",
        "md": text,
        "page_number": page,
        "page_width": 100.0,
        "page_height": 200.0,
        "bbox": [{"x": 20.0, "y": float(index), "w": 70.0, "h": 8.0}],
    }


def _list(text: str, page: int, index: int) -> dict:
    return {
        "type": "list",
        "md": text,
        "page_number": page,
        "page_width": 100.0,
        "page_height": 200.0,
        "bbox": [{"x": 25.0, "y": float(index), "w": 60.0, "h": 8.0}],
    }


def _table(text: str, page: int, index: int) -> dict:
    return {
        "type": "table",
        "md": text,
        "page_number": page,
        "page_width": 100.0,
        "page_height": 200.0,
        "bbox": [{"x": 15.0, "y": float(index), "w": 80.0, "h": 30.0}],
    }


def test_assembles_namespaces_and_disambiguates_repeated_paths() -> None:
    items = [
        _heading("# \u0421\u041e\u0414\u0415\u0420\u0416\u0410\u041d\u0418\u0415", 3, 0),
        _text("toc line", 3, 1),
        _heading("# \u0412\u0412\u0415\u0414\u0415\u041d\u0418\u0415", 7, 2),
        _text("intro text", 7, 3),
        _heading("# \u0427\u0410\u0421\u0422\u042c I \u00ab\u041a\u041b\u0410\u0421\u0421\u0418\u0424\u0418\u041a\u0410\u0426\u0418\u042f\u00bb", 9, 4),
        _heading("# 1. \u041e\u0431\u0449\u0438\u0435 \u043f\u043e\u043b\u043e\u0436\u0435\u043d\u0438\u044f", 10, 5),
        _heading("## 1.1. \u041e\u043f\u0440\u0435\u0434\u0435\u043b\u0435\u043d\u0438\u044f", 10, 6),
        _text("classification 1.1 text", 10, 7),
        _heading("# \u041f\u0420\u0410\u0412\u0418\u041b\u0410 \u0422\u0415\u0425\u041d\u0418\u0427\u0415\u0421\u041a\u041e\u0413\u041e \u041d\u0410\u0414\u0417\u041e\u0420\u0410 \u0417\u0410 \u0421\u0423\u0414\u0410\u041c\u0418 \u0412 \u042d\u041a\u0421\u041f\u041b\u0423\u0410\u0422\u0410\u0426\u0418\u0418 (\u041f\u0422\u041d\u042d)", 67, 8),
        _heading("# 1. \u041e\u0431\u0449\u0438\u0435 \u043f\u043e\u043b\u043e\u0436\u0435\u043d\u0438\u044f", 68, 9),
        _heading("## 1.1. \u041e\u0431\u043b\u0430\u0441\u0442\u044c \u0440\u0430\u0441\u043f\u0440\u043e\u0441\u0442\u0440\u0430\u043d\u0435\u043d\u0438\u044f", 68, 10),
        _text("ptne 1.1 text", 68, 11),
        _heading("# \u041f\u0420\u0410\u0412\u0418\u041b\u0410 \u0422\u0415\u0425\u041d\u0418\u0427\u0415\u0421\u041a\u041e\u0413\u041e \u041d\u0410\u0414\u0417\u041e\u0420\u0410 \u0417\u0410 \u041f\u041e\u0421\u0422\u0420\u041e\u0419\u041a\u041e\u0419 \u0421\u0423\u0414\u041e\u0412 (\u041f\u0422\u041d\u041f)", 93, 12),
        _heading("# 1. \u041e\u0431\u0449\u0438\u0435 \u043f\u043e\u043b\u043e\u0436\u0435\u043d\u0438\u044f", 94, 13),
        _heading("## 1.1. \u041e\u0431\u043b\u0430\u0441\u0442\u044c \u0440\u0430\u0441\u043f\u0440\u043e\u0441\u0442\u0440\u0430\u043d\u0435\u043d\u0438\u044f", 94, 14),
        _text("ptnp 1.1 text", 94, 15),
    ]

    structure = assemble_document_structure_from_parse_items(items, page_count=139)

    assert [namespace["namespace_id"] for namespace in structure["namespaces"]] == [
        "front_matter",
        "toc",
        "introduction",
        "classification",
        "ptne",
        "ptnp",
    ]

    by_path = {
        section["namespaced_path"]: section
        for section in structure["sections"]
    }

    assert by_path["classification/1/1"]["content_text"] == "classification 1.1 text"
    assert by_path["ptne/1/1"]["content_text"] == "ptne 1.1 text"
    assert by_path["ptnp/1/1"]["content_text"] == "ptnp 1.1 text"

    assert by_path["classification/1/1"]["parent_id"] is not None
    assert by_path["ptne/1/1"]["parent_id"] is not None
    assert by_path["ptnp/1/1"]["parent_id"] is not None


def test_section_content_blocks_and_source_spans_are_preserved() -> None:
    items = [
        _heading("# \u0427\u0410\u0421\u0422\u042c I \u00ab\u041a\u041b\u0410\u0421\u0421\u0418\u0424\u0418\u041a\u0410\u0426\u0418\u042f\u00bb", 9, 0),
        _heading("# 3. \u0420\u0430\u0437\u0434\u0435\u043b", 10, 1),
        _heading("## 3.1. \u041e\u0431\u0449\u0438\u0435 \u0443\u043a\u0430\u0437\u0430\u043d\u0438\u044f", 10, 2),
        _text("first paragraph", 10, 3),
        _list("* item one\n* item two", 10, 4),
        _table("| A | B |\n| - | - |\n| 1 | 2 |", 10, 5),
        {"type": "footer", "md": "10", "page_number": 10},
    ]

    structure = assemble_document_structure_from_parse_items(items, page_count=10)

    by_path = {
        section["namespaced_path"]: section
        for section in structure["sections"]
    }

    section = by_path["classification/3/1"]

    assert section["content_blocks_count"] == 3
    assert [block["type"] for block in section["content_blocks"]] == ["text", "list", "table"]
    assert "first paragraph" in section["content_text"]
    assert "item one" in section["content_text"]
    assert "| A | B |" in section["content_text"]

    assert len(section["source_spans"]) == 4
    assert section["source_spans"][0]["item_type"] == "heading"
    assert section["source_spans"][1]["normalized_bbox"] == {
        "x": 0.2,
        "y": 0.015,
        "w": 0.7,
        "h": 0.04,
    }

    assert structure["diagnostics"]["sections_with_tables"] == 1
    assert structure["diagnostics"]["sections_with_lists"] == 1

def test_assembler_preserves_repeated_table_of_contents_namespaces() -> None:
    items = [
        _heading("# \u0421\u041e\u0414\u0415\u0420\u0416\u0410\u041d\u0418\u0415", 1, 0),
        _text("main toc line", 1, 1),
        _heading("# \u0412\u0412\u0415\u0414\u0415\u041d\u0418\u0415", 2, 2),
        _text("intro text", 2, 3),
        _heading("# \u0421\u041e\u0414\u0415\u0420\u0416\u0410\u041d\u0418\u0415", 5, 4),
        _text("appendix toc line", 5, 5),
        _heading("# \u0427\u0410\u0421\u0422\u042c I \u00ab\u041a\u041b\u0410\u0421\u0421\u0418\u0424\u0418\u041a\u0410\u0426\u0418\u042f\u00bb", 7, 6),
        _heading("# 1. \u041e\u0431\u0449\u0438\u0435 \u043f\u043e\u043b\u043e\u0436\u0435\u043d\u0438\u044f", 8, 7),
        _text("classification text", 8, 8),
    ]

    structure = assemble_document_structure_from_parse_items(items, page_count=12)

    assert [namespace["namespace_id"] for namespace in structure["namespaces"]] == [
        "front_matter",
        "toc",
        "introduction",
        "toc_2",
        "classification",
    ]

    assert structure["namespaces"][1]["page_start"] == 1
    assert structure["namespaces"][3]["page_start"] == 5
