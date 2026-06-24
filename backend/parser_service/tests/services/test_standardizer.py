"""
Тесты для стандартизатора JSON (standardizer.py)
"""
import pytest
from app.services.standardizer import JsonStandardizer
from app.config import settings


def test_standardizer_transform_raw_paragraph():
    raw = {
        "kids": [
            {"type": "paragraph", "page number": 1, "content": "Hello world", "bounding box": [0,0,100,50]}
        ],
        "number of pages": 1,
        "file name": "doc.pdf"
    }
    standardizer = JsonStandardizer()
    result = standardizer.transform(raw, file_name="override.pdf")
    doc = result["document"]
    assert doc["source"]["file_name"] == "override.pdf"
    assert doc["source"]["page_count"] == 1
    assert len(doc["block"]) == 1
    block = doc["block"][0]
    assert block["type"] == "paragraph"
    assert block["content"] == "Hello world"
    assert block["bbox"] == [0,0,100,50]
    assert block["page"] == 1


def test_standardizer_transform_heading():
    raw = {
        "kids": [
            {"type": "heading", "page number": 2, "content": "Chapter 1", "heading level": 1}
        ],
        "number of pages": 2
    }
    standardizer = JsonStandardizer()
    result = standardizer.transform(raw)
    block = result["document"]["block"][0]
    assert block["type"] == "heading"
    assert block["heading_level"] == 1
    assert block["content"] == "Chapter 1"


def test_standardizer_transform_list():
    raw = {
        "kids": [
            {
                "type": "list",
                "page number": 1,
                "numbering style": "decimal",
                "list items": [
                    {"content": "Item 1", "page number": 1, "bounding box": [0,0,10,10]},
                    {"content": "Item 2", "page number": 1, "bounding box": [0,10,10,20]}
                ]
            }
        ],
        "number of pages": 1
    }
    standardizer = JsonStandardizer()
    result = standardizer.transform(raw)
    block = result["document"]["block"][0]
    assert block["type"] == "list"
    assert block["numbering_style"] == "decimal"
    assert len(block["block"]) == 2
    assert block["block"][0]["content"] == "Item 1"
    assert block["block"][0]["type"] == "paragraph"


def test_standardizer_transform_table():
    raw = {
        "kids": [
            {
                "type": "table",
                "page number": 1,
                "number of rows": 2,
                "number of columns": 2,
                "rows": [
                    {
                        "row number": 0,
                        "cells": [
                            {"row number": 0, "column number": 0, "content": "A", "kids": []},
                            {"row number": 0, "column number": 1, "content": "B", "kids": []}
                        ]
                    },
                    {
                        "row number": 1,
                        "cells": [
                            {"row number": 1, "column number": 0, "content": "C", "kids": []},
                            {"row number": 1, "column number": 1, "content": "D", "kids": []}
                        ]
                    }
                ]
            }
        ],
        "number of pages": 1
    }
    standardizer = JsonStandardizer()
    result = standardizer.transform(raw)
    block = result["document"]["block"][0]
    assert block["type"] == "table"
    assert block["number_of_rows"] == 2
    assert block["number_of_columns"] == 2
    assert len(block["rows"]) == 2
    assert block["rows"][0]["cells"][0]["type"] == "table cell"


def test_standardizer_transform_image():
    raw = {
        "kids": [
            {
                "type": "image",
                "page number": 1,
                "source": "1d_images/fig.png",
                "width": 200,
                "height": 150
            }
        ],
        "number of pages": 1
    }
    standardizer = JsonStandardizer()
    result = standardizer.transform(raw)
    block = result["document"]["block"][0]
    assert block["type"] == "image"
    assert block["image_key"] == "fig.png"
    assert block["width"] == 200
    assert block["height"] == 150


def test_standardizer_transform_formula():
    raw = {
        "kids": [
            {"type": "formula", "page number": 1, "content": "E=mc^2"}
        ],
        "number of pages": 1
    }
    standardizer = JsonStandardizer()
    result = standardizer.transform(raw)
    block = result["document"]["block"][0]
    assert block["type"] == "formula"
    assert block["latex"] == "E=mc^2"
    assert block["meaning"] == ""


def test_standardizer_transform_font():
    raw = {
        "kids": [
            {
                "type": "paragraph",
                "page number": 1,
                "content": "Text",
                "font": "Arial",
                "font size": 12.0,
                "text color": "[0.5,0.5,0.5]"
            }
        ],
        "number of pages": 1
    }
    standardizer = JsonStandardizer()
    result = standardizer.transform(raw)
    block = result["document"]["block"][0]
    assert block["font"]["size"] == 12.0
    assert block["font"]["color"] == "#808080"  # 0.5*255=128
    assert block["font"]["bold"] is False
    assert block["font"]["italic"] is False


def test_standardizer_transform_container():
    """На входе контейнер (от нормализатора) – оборачивает content."""
    input_data = {
        "document_info": {"task_id": 123},
        "content": {
            "kids": [{"type": "paragraph", "page number": 1, "content": "Hi"}],
            "number of pages": 1
        },
        "metadata": {"some": "meta"}
    }
    standardizer = JsonStandardizer()
    result = standardizer.transform(input_data, file_name="test.pdf")
    assert result["document_info"] == {"task_id": 123}
    assert result["metadata"]["some"] == "meta"
    assert result["content"]["document"]["block"][0]["content"] == "Hi"
    assert result["content"]["metadata"]["total_pages"] == 1
    assert "has_tables" in result["content"]["metadata"]


def test_standardizer_pages_calculation():
    """Проверка расчёта страниц (ширина/высота в пикселях)."""
    raw = {
        "kids": [
            {"type": "paragraph", "page number": 2, "content": "Page2"},
            {"type": "paragraph", "page number": 5, "content": "Page5"}
        ],
        "number of pages": 5
    }
    standardizer = JsonStandardizer()
    result = standardizer.transform(raw)
    pages = result["document"]["pages"]
    assert len(pages) == 2
    assert pages[0]["page"] == 2
    assert pages[1]["page"] == 5
    # Проверяем размеры (A4, dpi=72)
    expected_width = int(210 * 72 / 25.4)   # ~595
    expected_height = int(297 * 72 / 25.4)  # ~842
    assert pages[0]["width"] == expected_width
    assert pages[0]["height"] == expected_height