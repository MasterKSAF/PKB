from convertor_validator_service_lama.services.document_structure_extraction_input import (
    build_parse_items_preview,
)
from convertor_validator_service_lama.services.document_structure_extraction_stages import (
    build_document_structure_overview_agent_input,
    build_document_structure_stage_plan,
    build_markdown_excerpt_from_preview,
    build_page_overview,
    build_scope_extraction_agent_inputs,
    filter_items_by_page_range,
    select_overview_items,
)


def test_build_parse_items_preview_preserves_source_item_index():
    preview = build_parse_items_preview(
        [
            {
                "_source_item_index": 42,
                "type": "text",
                "page_number": 3,
                "md": "2.4. Clause text",
            }
        ]
    )

    assert preview[0]["item_index"] == 42


def test_filter_items_by_page_range_preserves_original_indexes():
    items = [
        {"type": "text", "page_number": 1, "md": "page 1"},
        {"type": "text", "page_number": 2, "md": "page 2"},
        {"type": "text", "page_number": 3, "md": "page 3"},
    ]

    result = filter_items_by_page_range(items, page_start=2, page_end=3)

    assert [item["_source_item_index"] for item in result] == [1, 2]
    assert [item["md"] for item in result] == ["page 2", "page 3"]


def test_build_page_overview_counts_items_and_headings():
    items = [
        {"type": "heading", "page_number": 1, "md": "# Title"},
        {"type": "text", "page_number": 1, "md": "body"},
        {"type": "heading", "page_number": 2, "md": "## 1. Section"},
    ]

    overview = build_page_overview(items)

    assert overview[0]["page_number"] == 1
    assert overview[0]["items_count"] == 2
    assert overview[0]["types"] == {"heading": 1, "text": 1}
    assert overview[0]["headings"][0]["item_index"] == 0
    assert overview[1]["page_number"] == 2
    assert overview[1]["headings"][0]["text"] == "## 1. Section"


def test_select_overview_items_keeps_structural_items_across_pages():
    items = [
        {"type": "text", "page_number": 1, "md": "front"},
        {"type": "text", "page_number": 2, "md": "body"},
        {"type": "heading", "page_number": 20, "md": "# Late heading"},
        {"type": "text", "page_number": 21, "md": "tail"},
    ]

    selected = select_overview_items(items, max_items=10)

    selected_indexes = [item["_source_item_index"] for item in selected]
    assert 0 in selected_indexes
    assert 2 in selected_indexes
    assert 3 in selected_indexes


def test_build_overview_agent_input_is_compact_and_has_page_map():
    payload = {
        "job_id": "job-1",
        "status": "COMPLETED",
        "job_metadata": {"pdf-pages": 3},
        "items": [
            {"type": "heading", "page_number": 1, "md": "# Title"},
            {"type": "text", "page_number": 2, "md": "body"},
            {"type": "heading", "page_number": 3, "md": "## 1. Section"},
        ],
        "markdown": "# Title\n\n## 1. Section",
    }

    overview_input = build_document_structure_overview_agent_input(
        payload,
        max_preview_items=2,
    )

    assert overview_input["stage_id"] == "overview"
    assert overview_input["stage_type"] == "overview"
    assert overview_input["page_count"] == 3
    assert overview_input["items_count"] == 3
    assert overview_input["items_preview_count"] == 2
    assert len(overview_input["page_overview"]) == 3
    assert "numbering_scopes" in overview_input["goal"]


def test_build_scope_extraction_agent_inputs_split_by_numbering_scopes():
    payload = {
        "job_id": "job-1",
        "status": "COMPLETED",
        "job_metadata": {"pdf-pages": 4},
        "items": [
            {"type": "heading", "page_number": 1, "md": "# Part A"},
            {"type": "text", "page_number": 1, "md": "1.1. A"},
            {"type": "heading", "page_number": 3, "md": "# Part B"},
            {"type": "text", "page_number": 4, "md": "1.1. B"},
        ],
        "markdown": "# Part A\n# Part B",
    }

    scopes = [
        {
            "namespace_id": "part_a",
            "title": "Part A",
            "scope_type": "part",
            "page_start": 1,
            "page_end": 2,
        },
        {
            "namespace_id": "part_b",
            "title": "Part B",
            "scope_type": "part",
            "page_start": 3,
            "page_end": 4,
        },
    ]

    scope_inputs = build_scope_extraction_agent_inputs(
        payload,
        numbering_scopes=scopes,
    )

    assert len(scope_inputs) == 2
    assert scope_inputs[0]["stage_id"] == "scope_part_a_p1_2"
    assert scope_inputs[0]["namespace_id"] == "part_a"
    assert scope_inputs[0]["items_count"] == 2
    assert [item["item_index"] for item in scope_inputs[0]["parse_items_preview"]] == [
        0,
        1,
    ]

    assert scope_inputs[1]["stage_id"] == "scope_part_b_p3_4"
    assert scope_inputs[1]["namespace_id"] == "part_b"
    assert scope_inputs[1]["items_count"] == 2
    assert [item["item_index"] for item in scope_inputs[1]["parse_items_preview"]] == [
        2,
        3,
    ]


def test_build_document_structure_stage_plan_without_scopes_waits_for_overview():
    payload = {
        "job_id": "job-1",
        "status": "COMPLETED",
        "job_metadata": {"pdf-pages": 1},
        "items": [
            {"type": "heading", "page_number": 1, "md": "# Title"},
        ],
        "markdown": "# Title",
    }

    plan = build_document_structure_stage_plan(payload)

    assert plan["stages_count"] == 1
    assert plan["requires_overview_agent_output"] is True
    assert plan["overview_input"]["stage_type"] == "overview"
    assert plan["scope_inputs"] == []


def test_build_document_structure_stage_plan_with_scopes_has_scope_inputs():
    payload = {
        "job_id": "job-1",
        "status": "COMPLETED",
        "job_metadata": {"pdf-pages": 2},
        "items": [
            {"type": "heading", "page_number": 1, "md": "# Main"},
            {"type": "text", "page_number": 2, "md": "1.1. Clause"},
        ],
        "markdown": "# Main\n1.1. Clause",
    }

    plan = build_document_structure_stage_plan(
        payload,
        numbering_scopes=[
            {
                "namespace_id": "main_document",
                "title": "Main document",
                "page_start": 1,
                "page_end": 2,
            }
        ],
    )

    assert plan["stages_count"] == 2
    assert plan["requires_overview_agent_output"] is False
    assert len(plan["scope_inputs"]) == 1
    assert plan["scope_inputs"][0]["namespace_id"] == "main_document"


def test_build_markdown_excerpt_from_preview_limits_output():
    preview = [
        {
            "item_index": 1,
            "page_number": 1,
            "type": "text",
            "text": "A" * 100,
        }
    ]

    excerpt = build_markdown_excerpt_from_preview(preview, limit=30)

    assert len(excerpt) <= 30
    assert excerpt.endswith("?")

def test_split_scope_items_into_windows_uses_overlap():
    from convertor_validator_service_lama.services.document_structure_extraction_stages import (
        split_scope_items_into_windows,
    )

    items = [
        {"_source_item_index": index, "type": "text", "page_number": index + 1}
        for index in range(7)
    ]

    windows = split_scope_items_into_windows(
        items,
        max_items_per_window=3,
        overlap_items=1,
    )

    assert [
        [item["_source_item_index"] for item in window]
        for window in windows
    ] == [
        [0, 1, 2],
        [2, 3, 4],
        [4, 5, 6],
    ]


def test_build_scope_extraction_agent_inputs_creates_windows_for_large_scope():
    payload = {
        "job_id": "job-1",
        "status": "COMPLETED",
        "job_metadata": {"pdf-pages": 7},
        "items": [
            {
                "type": "text",
                "page_number": index + 1,
                "md": f"{index + 1}. Window item",
            }
            for index in range(7)
        ],
        "markdown": "large scope",
    }

    scope_inputs = build_scope_extraction_agent_inputs(
        payload,
        numbering_scopes=[
            {
                "namespace_id": "main_document",
                "title": "Main document",
                "page_start": 1,
                "page_end": 7,
            }
        ],
        max_preview_items=10,
        max_scope_items_per_window=3,
        overlap_items=1,
    )

    assert len(scope_inputs) == 3
    assert [scope["window_index"] for scope in scope_inputs] == [0, 1, 2]
    assert [scope["windows_count"] for scope in scope_inputs] == [3, 3, 3]
    assert [scope["items_count"] for scope in scope_inputs] == [3, 3, 3]
    assert [scope["source_item_index_start"] for scope in scope_inputs] == [0, 2, 4]
    assert [scope["source_item_index_end"] for scope in scope_inputs] == [2, 4, 6]
    assert [scope["stage_id"] for scope in scope_inputs] == [
        "scope_main_document_p1_3_w01",
        "scope_main_document_p3_5_w02",
        "scope_main_document_p5_7_w03",
    ]


def test_build_document_structure_stage_plan_counts_windowed_scope_inputs():
    payload = {
        "job_id": "job-1",
        "status": "COMPLETED",
        "job_metadata": {"pdf-pages": 7},
        "items": [
            {
                "type": "text",
                "page_number": index + 1,
                "md": f"{index + 1}. Window item",
            }
            for index in range(7)
        ],
        "markdown": "large scope",
    }

    plan = build_document_structure_stage_plan(
        payload,
        numbering_scopes=[
            {
                "namespace_id": "main_document",
                "title": "Main document",
                "page_start": 1,
                "page_end": 7,
            }
        ],
        scope_max_window_items=3,
        scope_overlap_items=1,
    )

    assert plan["requires_overview_agent_output"] is False
    assert plan["stages_count"] == 4
    assert len(plan["scope_inputs"]) == 3
