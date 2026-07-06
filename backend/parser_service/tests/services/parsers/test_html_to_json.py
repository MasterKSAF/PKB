"""Unit-тесты для html_to_json.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent
                       / "app" / "services" / "parsers" / "docling"))
from html_to_json import html_to_json_blocks, html_to_document_json, parse_table_from_html


def test_heading_block():
    html = "<div class='page'><h1>Title</h1><h2>Section 1</h2></div>"
    blocks = html_to_json_blocks(html, page_number=1)
    assert len(blocks) == 2
    assert blocks[0]["type"] == "heading"
    assert blocks[0]["heading level"] == 1
    assert blocks[0]["content"] == "Title"
    assert blocks[1]["type"] == "heading"
    assert blocks[1]["heading level"] == 2
    assert blocks[1]["content"] == "Section 1"


def test_paragraph_block():
    html = "<div class='page'><p>Simple paragraph text.</p></div>"
    blocks = html_to_json_blocks(html, page_number=1)
    assert len(blocks) == 1
    assert blocks[0]["type"] == "paragraph"
    assert blocks[0]["content"] == "Simple paragraph text."


def test_multiple_paragraphs():
    html = "<div class='page'><p>First para.</p><p>Second para.</p></div>"
    blocks = html_to_json_blocks(html, page_number=1)
    assert len(blocks) == 2
    assert blocks[0]["content"] == "First para."
    assert blocks[1]["content"] == "Second para."


def test_heading_then_paragraph():
    html = "<div class='page'><h1>Title</h1><p>Content text.</p></div>"
    blocks = html_to_json_blocks(html, page_number=1)
    assert len(blocks) == 2
    assert blocks[0]["type"] == "heading"
    assert blocks[0]["content"] == "Title"
    assert blocks[1]["type"] == "paragraph"
    assert blocks[1]["content"] == "Content text."


def test_heading_h1_to_h6():
    html = "<div class='page'>"
    for i in range(1, 7):
        html += f"<h{i}>Level {i}</h{i}>"
    html += "</div>"
    blocks = html_to_json_blocks(html, page_number=1)
    assert len(blocks) == 6
    for i in range(6):
        assert blocks[i]["heading level"] == i + 1
        assert blocks[i]["content"] == f"Level {i + 1}"


def test_image_with_figcaption():
    html = "<div class='page'><figure><img alt='test image'/><figcaption>Рис. 1 — Пример</figcaption></figure></div>"
    blocks = html_to_json_blocks(html, page_number=1)
    assert len(blocks) == 1
    assert blocks[0]["type"] == "image"
    assert blocks[0]["content"] == "Рис. 1 — Пример"


def test_image_without_figcaption():
    html = "<div class='page'><figure><img alt='just image'/></figure></div>"
    blocks = html_to_json_blocks(html, page_number=1)
    assert len(blocks) == 1
    assert blocks[0]["type"] == "image"
    assert blocks[0]["content"] == ""


def test_image_with_img_alt():
    html = "<div class='page'><figure><img alt='Image description'/></figure></div>"
    blocks = html_to_json_blocks(html, page_number=1)
    assert len(blocks) == 1
    assert blocks[0]["content"] == ""


def test_bullet_list():
    html = "<div class='page'><ul><li>Item 1</li><li>Item 2</li><li>Item 3</li></ul></div>"
    blocks = html_to_json_blocks(html, page_number=1)
    assert len(blocks) == 1
    assert blocks[0]["type"] == "list"
    assert blocks[0]["list_type"] == "bullet"
    assert len(blocks[0]["items"]) == 3
    assert blocks[0]["items"][0]["content"] == "Item 1"
    assert blocks[0]["items"][1]["content"] == "Item 2"
    assert blocks[0]["items"][2]["content"] == "Item 3"


def test_numbered_list():
    html = "<div class='page'><ol><li>First</li><li>Second</li></ol></div>"
    blocks = html_to_json_blocks(html, page_number=1)
    assert len(blocks) == 1
    assert blocks[0]["type"] == "list"
    assert blocks[0]["list_type"] == "numbered"
    assert len(blocks[0]["items"]) == 2
    assert blocks[0]["items"][0]["content"] == "First"


def test_simple_table():
    html = ("<div class='page'><table><tr><th>Col1</th><th>Col2</th></tr>"
            "<tr><td>A</td><td>B</td></tr></table></div>")
    blocks = html_to_json_blocks(html, page_number=1)
    assert len(blocks) == 1
    assert blocks[0]["type"] == "table"
    assert blocks[0]["number of rows"] == 1
    assert blocks[0]["number of columns"] == 2
    assert blocks[0]["content"] == "Col1 | Col2"


def test_table_multirow():
    html = ("<div class='page'><table><tr><th>X</th><th>Y</th></tr>"
            "<tr><td>1</td><td>2</td></tr>"
            "<tr><td>3</td><td>4</td></tr></table></div>")
    blocks = html_to_json_blocks(html, page_number=1)
    assert len(blocks) == 1
    assert blocks[0]["number of rows"] == 2
    assert blocks[0]["number of columns"] == 2
    assert len(blocks[0]["rows"]) == 2


def test_table_cell_content():
    html = ("<div class='page'><table><tr><td>Cell A</td><td>Cell B</td></tr></table></div>")
    blocks = html_to_json_blocks(html, page_number=1)
    cells = blocks[0]["rows"][0]["cells"]
    assert cells[0]["kids"][0]["content"] == "Cell A"
    assert cells[1]["kids"][0]["content"] == "Cell B"


def test_mixed_blocks():
    html = ("<div class='page'>"
            "<h1>Title</h1>"
            "<p>Intro text.</p>"
            "<p>More text.</p>"
            "</div>")
    blocks = html_to_json_blocks(html, page_number=1)
    assert len(blocks) == 3
    assert blocks[0]["type"] == "heading"
    assert blocks[1]["type"] == "paragraph"
    assert blocks[2]["type"] == "paragraph"


def test_page_number():
    html = "<div class='page'><p>Page 5 content.</p></div>"
    blocks = html_to_json_blocks(html, page_number=5)
    assert blocks[0]["page number"] == 5


def test_ignores_style_and_head():
    html = ("<html><head><style>body{color:red}</style></head>"
            "<body><div class='page'><p>Real content.</p></div></body></html>")
    blocks = html_to_json_blocks(html, page_number=1)
    assert len(blocks) == 1
    assert blocks[0]["content"] == "Real content."


def test_empty_html():
    html = "<div class='page'></div>"
    blocks = html_to_json_blocks(html, page_number=1)
    assert blocks == []


def test_no_page_div():
    html = "<p>Text without page div</p>"
    blocks = html_to_json_blocks(html, page_number=1)
    assert blocks == []


def test_parse_table_from_html_empty():
    result = parse_table_from_html([])
    assert result["number of rows"] == 0
    assert result["number of columns"] == 0


def test_parse_table_from_html_basic():
    rows = [["H1", "H2"], ["A", "B"]]
    result = parse_table_from_html(rows)
    assert result["number of rows"] == 1
    assert result["number of columns"] == 2
    assert result["content"] == "H1 | H2"
    assert result["rows"][0]["cells"][0]["kids"][0]["content"] == "A"


def test_html_to_document_json_basic():
    page_htmls = [(1, "<div class='page'><h1>Doc 1</h1></div>"),
                  (2, "<div class='page'><p>Page two.</p></div>")]
    result = html_to_document_json(page_htmls, "test.pdf")
    assert result["content"]["document"]["source"]["file_name"] == "test.pdf"
    assert result["content"]["document"]["source"]["page_count"] == 2
    blocks = result["content"]["document"]["block"]
    assert len(blocks) == 2
    assert blocks[0]["type"] == "heading"
    assert blocks[0]["page number"] == 1
    assert blocks[1]["type"] == "paragraph"
    assert blocks[1]["page number"] == 2
    assert result["content"]["quality"]["pages_processed"] == 2
    assert result["content"]["status"] == "completed"


def test_html_to_document_json_has_tables():
    html = "<div class='page'><table><tr><td>A</td></tr></table></div>"
    result = html_to_document_json([(1, html)], "t.pdf")
    assert result["content"]["metadata"]["has_tables"] is True


def test_html_to_document_json_no_tables():
    result = html_to_document_json([(1, "<div class='page'><p>No table</p></div>")], "t.pdf")
    assert result["content"]["metadata"]["has_tables"] is False


def test_bounding_box_default():
    html = "<div class='page'><p>Content</p></div>"
    blocks = html_to_json_blocks(html, page_number=1)
    assert blocks[0]["bounding box"] == [0, 0, 0, 0]


def test_paragraph_with_nested_inline():
    html = "<div class='page'><p>Text with <strong>bold</strong> and <em>emphasis</em>.</p></div>"
    blocks = html_to_json_blocks(html, page_number=1)
    assert len(blocks) == 1
    assert blocks[0]["type"] == "paragraph"
    assert "bold" in blocks[0]["content"]
    assert "emphasis" in blocks[0]["content"]


def test_nbsp_in_text():
    html = "<div class='page'><p>Text\u00a0with\u00a0non-breaking\u00a0spaces.</p></div>"
    blocks = html_to_json_blocks(html, page_number=1)
    assert "\u00a0" in blocks[0]["content"]


def test_page_number_in_all_blocks():
    html = ("<div class='page'>"
            "<p>Para</p><h1>Head</h1>"
            "</div>")
    blocks = html_to_json_blocks(html, page_number=7)
    for b in blocks:
        assert b["page number"] == 7
