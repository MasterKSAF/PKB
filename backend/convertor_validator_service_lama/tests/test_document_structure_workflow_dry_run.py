from convertor_validator_service_lama.models.contracts import (
    DocumentStructureWorkflowDryRunRequest,
)
from convertor_validator_service_lama.services.document_structure_workflow_dry_run import (
    build_document_structure_workflow_dry_run_response,
)


def make_payload(*, pages: int = 2, items_count: int = 3) -> dict:
    return {
        "job_id": "parse-job-123",
        "status": "COMPLETED",
        "job_metadata": {"pdf-pages": pages},
        "items": [
            {
                "type": "text",
                "page_number": min(index + 1, pages),
                "md": f"{index + 1}. Test item",
            }
            for index in range(items_count)
        ],
        "markdown": "test document",
    }


def test_document_structure_workflow_dry_run_waits_for_overview_output():
    response = build_document_structure_workflow_dry_run_response(
        DocumentStructureWorkflowDryRunRequest(
            parse_result_payload=make_payload(),
        )
    )

    assert response.mode == "document_structure_workflow_dry_run"
    assert response.parse_job_id == "parse-job-123"
    assert response.page_count == 2
    assert response.items_count == 3
    assert response.stages_count == 1
    assert response.requires_overview_agent_output is True
    assert response.overview_items_preview_count == 3
    assert response.overview_page_overview_count == 2
    assert response.scope_inputs_count == 0
    assert response.scope_stage_summaries == []


def test_document_structure_workflow_dry_run_builds_scope_window_summaries():
    response = build_document_structure_workflow_dry_run_response(
        DocumentStructureWorkflowDryRunRequest(
            parse_result_payload=make_payload(pages=7, items_count=7),
            numbering_scopes=[
                {
                    "namespace_id": "main_document",
                    "title": "Main document",
                    "scope_type": "MAIN_DOCUMENT",
                    "page_start": 1,
                    "page_end": 7,
                    "confidence": 0.95,
                    "reason": "Fake overview.",
                }
            ],
            scope_max_window_items=3,
            scope_overlap_items=1,
        )
    )

    assert response.requires_overview_agent_output is False
    assert response.stages_count == 4
    assert response.scope_inputs_count == 3

    assert [
        item.stage_id
        for item in response.scope_stage_summaries
    ] == [
        "scope_main_document_p1_3_w01",
        "scope_main_document_p3_5_w02",
        "scope_main_document_p5_7_w03",
    ]

    assert [
        item.window_index
        for item in response.scope_stage_summaries
    ] == [1, 2, 3]

    assert [
        item.windows_count
        for item in response.scope_stage_summaries
    ] == [3, 3, 3]


def test_document_structure_workflow_dry_run_accepts_minimal_payload():
    response = build_document_structure_workflow_dry_run_response(
        DocumentStructureWorkflowDryRunRequest(
            parse_result_payload={},
        )
    )

    assert response.parse_job_id is None
    assert response.page_count is None
    assert response.items_count == 0
    assert response.stages_count == 1
    assert response.requires_overview_agent_output is True
