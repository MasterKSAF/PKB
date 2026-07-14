from convertor_validator_service_lama.prompts.document_structure_extraction import (
    build_document_structure_extraction_prompt,
)
from convertor_validator_service_lama.services.document_structure_extraction_input import (
    build_document_structure_agent_input,
    build_parse_items_preview,
    extract_effective_parse_items,
)


def test_extract_effective_parse_items_uses_top_level_items_first():
    payload = {
        "items": [
            {
                "type": "text",
                "page_number": 1,
                "md": "1.1. Clause text",
            }
        ],
        "raw_response": {
            "items": {
                "pages": [
                    {
                        "page_number": 1,
                        "items": [
                            {
                                "type": "text",
                                "md": "raw item should not be used",
                            }
                        ],
                    }
                ]
            }
        },
    }

    items = extract_effective_parse_items(payload)

    assert len(items) == 1
    assert items[0]["md"] == "1.1. Clause text"


def test_extract_effective_parse_items_flattens_old_raw_response_pages():
    payload = {
        "items": [],
        "raw_response": {
            "items": {
                "pages": [
                    {
                        "page_number": 1,
                        "page_width": 1000,
                        "page_height": 2000,
                        "items": [
                            {
                                "type": "text",
                                "md": "1.1. Clause text",
                                "bbox": [100, 200, 300, 400],
                            }
                        ],
                    },
                    {
                        "page_number": 2,
                        "page_width": 1000,
                        "page_height": 2000,
                        "items": [
                            {
                                "type": "footer",
                                "md": "2 ???? TEST",
                            }
                        ],
                    },
                ]
            }
        },
    }

    items = extract_effective_parse_items(payload)

    assert len(items) == 2
    assert items[0]["page_number"] == 1
    assert items[0]["page_width"] == 1000
    assert items[0]["page_height"] == 2000
    assert items[1]["page_number"] == 2


def test_build_parse_items_preview_extracts_text_and_normalized_bbox():
    items = [
        {
            "type": "text",
            "page_number": 3,
            "page_width": 1000,
            "page_height": 2000,
            "bbox": [100, 200, 300, 400],
            "md": "2.4. Clause text",
        }
    ]

    preview = build_parse_items_preview(items)

    assert preview == [
        {
            "item_index": 0,
            "type": "text",
            "page_number": 3,
            "text": "2.4. Clause text",
            "bbox": [100.0, 200.0, 300.0, 400.0],
            "normalized_bbox": [0.1, 0.1, 0.3, 0.2],
            "page_width": 1000.0,
            "page_height": 2000.0,
        }
    ]


def test_build_document_structure_agent_input_marks_raw_flattening():
    payload = {
        "job_id": "job-1",
        "status": "COMPLETED",
        "metadata": {
            "pages": [{}, {}],
        },
        "job_metadata": {
            "pdf-pages": 2,
        },
        "items": [],
        "markdown": "## 1. Test\n1.1. Clause text",
        "raw_response": {
            "items": {
                "pages": [
                    {
                        "page_number": 1,
                        "page_width": 1000,
                        "page_height": 2000,
                        "items": [
                            {
                                "type": "text",
                                "md": "1.1. Clause text",
                                "bbox": [100, 200, 300, 400],
                            }
                        ],
                    }
                ]
            }
        },
    }

    agent_input = build_document_structure_agent_input(payload)

    assert agent_input["job_id"] == "job-1"
    assert agent_input["status"] == "COMPLETED"
    assert agent_input["page_count"] == 2
    assert agent_input["metadata_pages_count"] == 2
    assert agent_input["job_metadata_pdf_pages"] == 2
    assert agent_input["items_count"] == 1
    assert agent_input["items_preview_count"] == 1
    assert agent_input["items_were_flattened_from_raw_response"] is True
    assert agent_input["parse_items_preview"][0]["normalized_bbox"] == [
        0.1,
        0.1,
        0.3,
        0.2,
    ]


def test_agent_input_can_be_used_to_build_prompt():
    payload = {
        "job_id": "job-1",
        "status": "COMPLETED",
        "metadata": {
            "pages": [{}],
        },
        "items": [
            {
                "type": "text",
                "page_number": 1,
                "md": "750 X 50 ? 64? 16-? ???? 10054?82",
            },
            {
                "type": "text",
                "page_number": 1,
                "md": "1.1. Clause text",
            },
        ],
        "markdown": "## 1. Test\n1.1. Clause text",
    }

    agent_input = build_document_structure_agent_input(payload)
    prompt = build_document_structure_extraction_prompt(
        document_markdown=agent_input["markdown_excerpt"],
        parse_items_preview=agent_input["parse_items_preview"],
        page_count=agent_input["page_count"],
        document_hint="???? 10054-82",
    )

    assert "???? 10054-82" in prompt
    assert "750 X 50 ? 64? 16-? ???? 10054?82" in prompt
    assert "1.1. Clause text" in prompt
    assert "Supplied separately via data_schema" in prompt
    assert "DocumentStructureExtraction" not in prompt
