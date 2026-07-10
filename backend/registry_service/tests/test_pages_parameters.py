import pytest

def test_document_pages_and_parameters(client):
    # 1. Create a document with page count and sections of type formula
    pipeline_payload = {
        "document": {
            "metadata": {
                "title": "Pages and Parameters Test Doc",
                "doc_code": "PAGES-PARAMS-01",
                "era": "RF",
                "source_type": "GOST"
            },
            "source": {
                "file_hash_sha256": "abcdef1234567890",
                "file_name": "test_doc_pages.pdf",
                "page_count": 5  # This becomes the file_size_bytes in version, serving as pages count
            },
            "content": [
                {
                    "clause": "1.1",
                    "title": "Introduction",
                    "level": 1,
                    "path": "1.1",
                    "page": 1,
                    "bbox": [10, 20, 100, 50],
                    "type": "text",
                    "content": {"text": "This is page 1 introduction text."}
                },
                {
                    "clause": "2.1",
                    "title": "Formula Clause",
                    "level": 2,
                    "path": "2.1",
                    "page": 2,
                    "bbox": [15, 30, 120, 60],
                    "type": "formula",
                    "content": {
                        "latex": "E = mc^2",
                        "meaning": "Mass-energy equivalence",
                        "parameters": [
                            {
                                "symbol": "E",
                                "description": "Energy",
                                "unit": "J",
                                "value": 100.0
                            },
                            {
                                "symbol": "m",
                                "description": "Mass",
                                "unit": "kg",
                                "value": 1.0
                            }
                        ]
                    }
                },
                {
                    "clause": "3.5",
                    "title": "Thickness parameters",
                    "level": 2,
                    "path": "3.5",
                    "page": 4,
                    "bbox": [20, 40, 200, 80],
                    "type": "formula",
                    "content": {
                        "latex": "t = 12.5mm",
                        "meaning": "Thickness formula",
                        "parameters": [
                            {
                                "symbol": "t",
                                "description": "Thickness",
                                "unit": "mm",
                                "value": 12.5
                            }
                        ]
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

    # 2. Test GET /registry/documents/{id}/pages
    pages_res = client.get(f"/api/v1/registry/documents/{doc_id}/pages")
    assert pages_res.status_code == 200
    pages_data = pages_res.json()["data"]
    assert pages_data["document_id"] == doc_id
    assert pages_data["pages_total"] == 5
    assert len(pages_data["pages"]) == 5
    assert pages_data["pages"][0]["page"] == 1
    assert pages_data["pages"][0]["width"] == 595.0
    assert pages_data["pages"][0]["height"] == 842.0

    # 3. Test GET /registry/documents/{id}/pages/{page_num}
    page2_res = client.get(f"/api/v1/registry/documents/{doc_id}/pages/2")
    assert page2_res.status_code == 200
    page2_data = page2_res.json()["data"]
    assert page2_data["page"] == 2
    assert len(page2_data["blocks"]) == 1
    assert page2_data["blocks"][0]["type"] == "formula"
    # Raw structure — content is the original JSONB object
    assert isinstance(page2_data["blocks"][0]["content"], dict)
    assert page2_data["blocks"][0]["content"]["latex"] == "E = mc^2"
    assert page2_data["blocks"][0]["content"]["meaning"] == "Mass-energy equivalence"
    # Confidence is 0 (no data)
    assert page2_data["blocks"][0]["confidence"] == 0

    # 4. Test GET /registry/documents/{id}/pages/{page_num}/text
    page2_text_res = client.get(f"/api/v1/registry/documents/{doc_id}/pages/2/text")
    assert page2_text_res.status_code == 200
    page2_text_data = page2_text_res.json()["data"]
    assert page2_text_data["page"] == 2
    assert len(page2_text_data["blocks"]) == 1
    # /text returns plain text (latex extracted)
    assert page2_text_data["blocks"][0]["content"] == "E = mc^2"

    # 5. Test GET /registry/documents/{id}/pages/{page_num}/preview
    page2_prev_res = client.get(f"/api/v1/registry/documents/{doc_id}/pages/2/preview")
    assert page2_prev_res.status_code == 200
    page2_prev_data = page2_prev_res.json()["data"]
    assert page2_prev_data["page"] == 2
    assert "image_key" in page2_prev_data
    assert "p2.png" in page2_prev_data["image_key"]
    # Preview text_layer uses markdown-formatted content
    assert page2_prev_data["text_layer"] == "$$E = mc^2$$\n*Физический смысл: Mass-energy equivalence*"

    # 6. Test GET /registry/documents/{id}/parameters
    params_res = client.get(f"/api/v1/registry/documents/{doc_id}/parameters")
    assert params_res.status_code == 200
    params_data = params_res.json()["data"]
    assert params_data["document_id"] == doc_id
    assert len(params_data["parameters"]) == 3
    
    # Check parameter fields mapping
    p0 = params_data["parameters"][0]
    assert p0["symbol"] == "E"
    assert p0["source_clause"] == "2.1"
    assert p0["source_page"] == 2

    p2 = params_data["parameters"][2]
    assert p2["symbol"] == "t"
    assert p2["source_clause"] == "3.5"
    assert p2["source_page"] == 4

    # 7. Test invalid page 404
    invalid_page_res = client.get(f"/api/v1/registry/documents/{doc_id}/pages/99")
    assert invalid_page_res.status_code == 404
