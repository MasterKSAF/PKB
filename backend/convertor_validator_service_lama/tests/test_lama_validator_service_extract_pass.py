import pytest

from convertor_validator_service_lama.clients.llama_extract_rest_client import (
    MissingLlamaExtractProjectIdError,
)
from convertor_validator_service_lama.models.extract_job import (
    ExtractJobPollingConfig,
    ExtractJobResult,
    ExtractJobStatus,
    ExtractJobSubmitResponse,
    ExtractPassRequest,
)
from convertor_validator_service_lama.services.lama_validator_service import (
    run_extract_pass_with_polling,
)


class FakeLlamaExtractRestClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []
        self.closed = False

    def start_extract_job(self, request: ExtractPassRequest) -> ExtractJobSubmitResponse:
        self.calls.append(("start_extract_job", request))
        return ExtractJobSubmitResponse(
            job_id="extract-job-123",
            pass_name=request.pass_name,
            status=ExtractJobStatus.pending,
            raw_response={"job": {"id": "extract-job-123", "status": "PENDING"}},
        )

    def poll_extract_job(
        self,
        job_id: str,
        pass_name: str,
        project_id: str,
        expand: list[str] | None = None,
        config: ExtractJobPollingConfig | None = None,
    ) -> ExtractJobResult:
        self.calls.append(
            (
                "poll_extract_job",
                {
                    "job_id": job_id,
                    "pass_name": pass_name,
                    "project_id": project_id,
                    "expand": expand,
                    "config": config,
                },
            )
        )
        return ExtractJobResult(
            job_id=job_id,
            pass_name=pass_name,
            status=ExtractJobStatus.completed,
            result={"sections": [{"title": "1. Scope"}]},
            raw_response={"job": {"id": job_id, "status": "COMPLETED"}},
        )

    def close(self) -> None:
        self.closed = True


def test_run_extract_pass_with_polling_orchestrates_submit_and_poll(monkeypatch) -> None:
    monkeypatch.setenv("LAMA_EXTRACT_PROJECT_ID", "project-123")

    client = FakeLlamaExtractRestClient()
    polling_config = ExtractJobPollingConfig(max_attempts=3, interval_seconds=0.0)

    result = run_extract_pass_with_polling(
        parse_job_id="parse-job-123",
        pass_name="sections",
        extraction_schema={"type": "object"},
        instructions="Extract sections.",
        schema_name="sections_schema",
        expand=["extract_result"],
        polling_config=polling_config,
        client=client,
    )

    assert result.job_id == "extract-job-123"
    assert result.status == ExtractJobStatus.completed
    assert result.result == {"sections": [{"title": "1. Scope"}]}

    submit_call = client.calls[0]
    assert submit_call[0] == "start_extract_job"
    request = submit_call[1]
    assert request == ExtractPassRequest(
        parse_job_id="parse-job-123",
        pass_name="sections",
        project_id="project-123",
        schema_name="sections_schema",
        extraction_schema={"type": "object"},
        instructions="Extract sections.",
    )

    assert client.calls[1] == (
        "poll_extract_job",
        {
            "job_id": "extract-job-123",
            "pass_name": "sections",
            "project_id": "project-123",
            "expand": ["extract_result"],
            "config": polling_config,
        },
    )
    assert client.closed is False


def test_run_extract_pass_with_polling_requires_project_id(monkeypatch) -> None:
    monkeypatch.delenv("LAMA_EXTRACT_PROJECT_ID", raising=False)

    with pytest.raises(MissingLlamaExtractProjectIdError):
        run_extract_pass_with_polling(
            parse_job_id="parse-job-123",
            pass_name="sections",
            client=FakeLlamaExtractRestClient(),
        )