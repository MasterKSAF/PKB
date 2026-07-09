import pytest

def test_document_pages_content_md_and_html(client):
    # 1. Create a document with page count and sections of type text and table
    pipeline_payload = {
        "document": {
            "metadata": {
                "title": "Content Format Test Doc",
                "doc_code": "CONTENT-FORMAT-01",
                "era": "RF",
                "source_type": "GOST"
            },
            "source": {
                "file_hash_sha256": "aabbccddeeff0011",
                "file_name": "test_doc_formats.pdf",
                "page_count": 3
            },
            "content": [
                {
                    "clause": "1.1",
                    "title": "Intro",
                    "level": 1,
                    "path": "1.1",
                    "page": 1,
                    "bbox": [10, 20, 100, 50],
                    "type": "text",
                    "content": {
                        "markdown": "This is **bold** text.",
                        "text": "This is bold text."
                    }
                },
                {
                    "clause": "2.1",
                    "title": "Table Clause",
                    "level": 2,
                    "path": "2.1",
                    "page": 2,
                    "bbox": [15, 30, 120, 60],
                    "type": "table",
                    "content": {
                        "markdown": "| Col 1 | Col 2 |\n|---|---|\n| val 1 | val 2 |"
                    }
                }
            ],
            "terminology": [],
            "references": []
        }
    }

    create_response = client.post("/api/v1/registry/documents", json=pipeline_payload)
    assert create_response.status_code == 201
    doc_id = create_response.json()["document_id"]

    # 2. Test GET /registry/documents/{id}/pages/{page_num}/content_md
    # Page 1 (Text block)
    res_p1_md = client.get(f"/api/v1/registry/documents/{doc_id}/pages/1/content_md")
    assert res_p1_md.status_code == 200
    p1_md_data = res_p1_md.json()["data"]
    assert p1_md_data["page"] == 1
    assert p1_md_data["blocks"][0]["content"] == "This is **bold** text."
    assert p1_md_data["markdown"] == "\n\nThis is **bold** text."
    assert p1_md_data["content"] == "\n\nThis is **bold** text."

    # Page 2 (Table block)
    res_p2_md = client.get(f"/api/v1/registry/documents/{doc_id}/pages/2/content_md")
    assert res_p2_md.status_code == 200
    p2_md_data = res_p2_md.json()["data"]
    assert p2_md_data["page"] == 2
    assert "| Col 1 | Col 2 |" in p2_md_data["blocks"][0]["content"]
    assert "| Col 1 | Col 2 |" in p2_md_data["markdown"]
    assert "| Col 1 | Col 2 |" in p2_md_data["content"]

    # 3. Test GET /registry/documents/{id}/pages/{page_num}/content_html
    # Page 1 (Text block wrapped in <p>)
    res_p1_html = client.get(f"/api/v1/registry/documents/{doc_id}/pages/1/content_html")
    assert res_p1_html.status_code == 200
    p1_html_data = res_p1_html.json()["data"]
    assert p1_html_data["page"] == 1
    assert p1_html_data["blocks"][0]["content"] == "<p>This is **bold** text.</p>"
    assert p1_html_data["html"] == '<p data-type="text">This is **bold** text.</p>'
    assert p1_html_data["content"] == '<p data-type="text">This is **bold** text.</p>'

    # Page 2 (Table block converted to <table>)
    res_p2_html = client.get(f"/api/v1/registry/documents/{doc_id}/pages/2/content_html")
    assert res_p2_html.status_code == 200
    p2_html_data = res_p2_html.json()["data"]
    assert p2_html_data["page"] == 2
    html_content = p2_html_data["blocks"][0]["content"]
    assert "<table>" in html_content
    assert "<th>Col 1</th>" in html_content
    assert "<td>val 1</td>" in html_content
    assert '<table data-type="table">' in p2_html_data["html"]
    assert '<th>Col 1</th>' in p2_html_data["html"]
    assert '<td>val 1</td>' in p2_html_data["html"]
    assert p2_html_data["content"] == p2_html_data["html"]

    # 4. Test 404 for invalid page and invalid document
    res_invalid_page = client.get(f"/api/v1/registry/documents/{doc_id}/pages/99/content_md")
    assert res_invalid_page.status_code == 404

    res_invalid_doc = client.get("/api/v1/registry/documents/999999/pages/1/content_md")
    assert res_invalid_doc.status_code == 404


def test_document_pages_content_table_padding(client):
    # Create document with a table where columns list has 2 items, but row 1 has 3 items
    pipeline_payload = {
        "document": {
            "metadata": {
                "title": "Padding Test Doc",
                "doc_code": "PADDING-TEST-01",
                "era": "RF",
                "source_type": "GOST"
            },
            "source": {
                "file_hash_sha256": "1122334455667788",
                "file_name": "padding_test.pdf",
                "page_count": 1
            },
            "content": [
                {
                    "clause": "1.1",
                    "title": "Mismatched Table",
                    "level": 1,
                    "path": "1.1",
                    "page": 1,
                    "bbox": [10, 20, 100, 50],
                    "type": "table",
                    "content": {
                        "caption": "Mismatched Table Caption",
                        "columns": ["Header A", "Header B"],
                        "rows": [
                            ["Val A1", "Val B1", "Val C1"],
                            ["Val A2"]
                        ],
                        "footnotes": ["Note 1"]
                    }
                }
            ],
            "terminology": [],
            "references": []
        }
    }
    
    create_response = client.post("/api/v1/registry/documents", json=pipeline_payload)
    assert create_response.status_code == 201
    doc_id = create_response.json()["document_id"]
    
    # 1. Test markdown padding
    res_md = client.get(f"/api/v1/registry/documents/{doc_id}/pages/1/content_md")
    assert res_md.status_code == 200
    md_str = res_md.json()["data"]["markdown"]
    
    # Header should contain 3 columns (Header A, Header B, and padded "")
    assert "| Header A | Header B |  |" in md_str
    # Delimiter should contain 3 columns
    assert "| :--- | :--- | :--- |" in md_str
    # Row 1 should have Val C1
    assert "| Val A1 | Val B1 | Val C1 |" in md_str
    # Row 2 should be padded to 3 columns
    assert "| Val A2 |   |   |" in md_str
    
    # 2. Test HTML padding
    res_html = client.get(f"/api/v1/registry/documents/{doc_id}/pages/1/content_html")
    assert res_html.status_code == 200
    html_str = res_html.json()["data"]["html"]
    
    # Check headers padded to 3
    assert "<tr><th>Header A</th><th>Header B</th><th></th></tr>" in html_str
    # Check Row 1
    assert "<tr><td>Val A1</td><td>Val B1</td><td>Val C1</td></tr>" in html_str
    # Check Row 2 padded to 3
    assert "<tr><td>Val A2</td><td>&nbsp;</td><td>&nbsp;</td></tr>" in html_str
    # Check footnotes colspan spans 3 columns
    assert '<tr><td colspan="3">Note 1</td></tr>' in html_str

