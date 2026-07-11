from convertor_validator_service_lama.models.extract_job import (
    ExtractJobPollingConfig,
    ExtractJobResult,
    ExtractJobStatus,
    ExtractJobSubmitResponse,
    ExtractPassRequest,
)
from convertor_validator_service_lama.services.lama_validator_service import (
    build_extract_pass_plan_response,
    run_all_extract_passes_with_polling,
)


class FakeLlamaExtractRestClient:
    def __init__(self) -> None:
        self.submit_requests: list[ExtractPassRequest] = []
        self.poll_calls: list[dict[str, object]] = []
        self.closed = False

    def start_extract_job(self, request: ExtractPassRequest) -> ExtractJobSubmitResponse:
        self.submit_requests.append(request)
        return ExtractJobSubmitResponse(
            job_id=f"extract-job-{request.pass_name}",
            pass_name=request.pass_name,
            status=ExtractJobStatus.pending,
            raw_response={"job": {"id": f"extract-job-{request.pass_name}", "status": "PENDING"}},
        )

    def poll_extract_job(
        self,
        job_id: str,
        pass_name: str,
        project_id: str,
        expand: list[str] | None = None,
        config: ExtractJobPollingConfig | None = None,
    ) -> ExtractJobResult:
        self.poll_calls.append(
            {
                "job_id": job_id,
                "pass_name": pass_name,
                "project_id": project_id,
                "expand": expand,
                "config": config,
            }
        )
        return ExtractJobResult(
            job_id=job_id,
            pass_name=pass_name,
            status=ExtractJobStatus.completed,
            result={"pass_name": pass_name},
            raw_response={"job": {"id": job_id, "status": "COMPLETED"}},
        )

    def close(self) -> None:
        self.closed = True


def test_run_all_extract_passes_with_polling_runs_all_planned_passes(monkeypatch) -> None:
    monkeypatch.setenv("LAMA_EXTRACT_PROJECT_ID", "project-123")

    client = FakeLlamaExtractRestClient()
    polling_config = ExtractJobPollingConfig(max_attempts=3, interval_seconds=0.0)

    expected_passes = [item.name for item in build_extract_pass_plan_response().passes]

    results = run_all_extract_passes_with_polling(
        parse_job_id="parse-job-123",
        extraction_schemas={
            "sections": {"type": "object", "properties": {"sections": {"type": "array"}}},
        },
        instructions_by_pass={
            "sections": "Extract document sections.",
        },
        schema_names_by_pass={
            "sections": "sections_schema",
        },
        expand=["extract_result"],
        polling_config=polling_config,
        client=client,
    )

    assert list(results.keys()) == expected_passes
    assert [request.pass_name for request in client.submit_requests] == expected_passes
    assert [call["pass_name"] for call in client.poll_calls] == expected_passes

    sections_request = next(request for request in client.submit_requests if request.pass_name == "sections")
    assert sections_request.parse_job_id == "parse-job-123"
    assert sections_request.project_id == "project-123"
    assert sections_request.schema_name == "sections_schema"
    assert sections_request.extraction_schema == {
        "type": "object",
        "properties": {"sections": {"type": "array"}},
    }
    assert sections_request.instructions == "Extract document sections."

    nested_documents_request = next(
        request for request in client.submit_requests if request.pass_name == "nested_documents"
    )
    assert nested_documents_request.extraction_schema["properties"]["nested_documents"]["type"] == "array"
    assert nested_documents_request.extraction_schema["required"] == ["nested_documents"]
    assert "Do not flatten" in (nested_documents_request.instructions or "")

    toc_blocks_request = next(
        request for request in client.submit_requests if request.pass_name == "table_of_contents_blocks"
    )
    assert toc_blocks_request.extraction_schema["properties"]["table_of_contents_blocks"]["type"] == "array"
    assert toc_blocks_request.extraction_schema["required"] == ["table_of_contents_blocks"]
    assert "Do not merge" in (toc_blocks_request.instructions or "")

    notes_request = next(
        request for request in client.submit_requests if request.pass_name == "notes"
    )
    assert notes_request.extraction_schema["properties"]["notes"]["type"] == "array"
    assert notes_request.extraction_schema["required"] == ["notes"]
    assert "Extract notes" in (notes_request.instructions or "")

    references_request = next(
        request for request in client.submit_requests if request.pass_name == "references"
    )
    assert references_request.extraction_schema["properties"]["references"]["type"] == "array"
    assert references_request.extraction_schema["required"] == ["references"]
    assert "GOST 20862-81 - GOST 20867-81" in (references_request.instructions or "")

    assert results["sections"].result == {"pass_name": "sections"}
    assert client.closed is False