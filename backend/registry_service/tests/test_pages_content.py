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

    # Page 2 (Table block)
    res_p2_md = client.get(f"/api/v1/registry/documents/{doc_id}/pages/2/content_md")
    assert res_p2_md.status_code == 200
    p2_md_data = res_p2_md.json()["data"]
    assert p2_md_data["page"] == 2
    assert "| Col 1 | Col 2 |" in p2_md_data["blocks"][0]["content"]

    # 3. Test GET /registry/documents/{id}/pages/{page_num}/content_html
    # Page 1 (Text block wrapped in <p>)
    res_p1_html = client.get(f"/api/v1/registry/documents/{doc_id}/pages/1/content_html")
    assert res_p1_html.status_code == 200
    p1_html_data = res_p1_html.json()["data"]
    assert p1_html_data["page"] == 1
    assert p1_html_data["blocks"][0]["content"] == "<p>This is **bold** text.</p>"

    # Page 2 (Table block converted to <table>)
    res_p2_html = client.get(f"/api/v1/registry/documents/{doc_id}/pages/2/content_html")
    assert res_p2_html.status_code == 200
    p2_html_data = res_p2_html.json()["data"]
    assert p2_html_data["page"] == 2
    html_content = p2_html_data["blocks"][0]["content"]
    assert "<table>" in html_content
    assert "<th>Col 1</th>" in html_content
    assert "<td>val 1</td>" in html_content

    # 4. Test 404 for invalid page and invalid document
    res_invalid_page = client.get(f"/api/v1/registry/documents/{doc_id}/pages/99/content_md")
    assert res_invalid_page.status_code == 404

    res_invalid_doc = client.get("/api/v1/registry/documents/999999/pages/1/content_md")
    assert res_invalid_doc.status_code == 404
