from fastapi.testclient import TestClient

from convertor_validator_service_lama.api.app import app


client = TestClient(app)


def test_document_structure_workflow_dry_run_endpoint_returns_plan():
    response = client.post(
        "/document-structure-workflow/dry-run",
        json={
            "parse_result_payload": {
                "job_id": "parse-job-123",
                "status": "COMPLETED",
                "job_metadata": {"pdf-pages": 2},
                "items": [
                    {
                        "type": "text",
                        "page_number": 1,
                        "md": "1. Test item",
                    }
                ],
                "markdown": "test document",
            }
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["mode"] == "document_structure_workflow_dry_run"
    assert body["parse_job_id"] == "parse-job-123"
    assert body["page_count"] == 2
    assert body["items_count"] == 1
    assert body["stages_count"] == 1
    assert body["requires_overview_agent_output"] is True
    assert body["scope_inputs_count"] == 0


def test_document_structure_workflow_dry_run_endpoint_returns_windowed_scope_plan():
    response = client.post(
        "/document-structure-workflow/dry-run",
        json={
            "parse_result_payload": {
                "job_id": "parse-job-123",
                "status": "COMPLETED",
                "job_metadata": {"pdf-pages": 7},
                "items": [
                    {
                        "type": "text",
                        "page_number": index + 1,
                        "md": f"{index + 1}. Test item",
                    }
                    for index in range(7)
                ],
                "markdown": "test document",
            },
            "numbering_scopes": [
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
            "scope_max_window_items": 3,
            "scope_overlap_items": 1,
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["requires_overview_agent_output"] is False
    assert body["scope_inputs_count"] == 3
    assert [
        item["stage_id"]
        for item in body["scope_stage_summaries"]
    ] == [
        "scope_main_document_p1_3_w01",
        "scope_main_document_p3_5_w02",
        "scope_main_document_p5_7_w03",
    ]
