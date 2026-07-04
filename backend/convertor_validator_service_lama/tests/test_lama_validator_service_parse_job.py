from convertor_validator_service_lama.models.parse_job import (
    ParseJobPollingConfig,
    ParseJobResult,
    ParseJobStatus,
    ParseJobSubmitResponse,
)
from convertor_validator_service_lama.services.lama_validator_service import (
    run_parse_job_with_polling,
)


class FakeLlamaParseRestClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []
        self.closed = False

    def upload_file(self, source_pdf_path: str) -> str:
        self.calls.append(("upload_file", source_pdf_path))
        return "file-123"

    def start_parse_job(self, file_id: str) -> ParseJobSubmitResponse:
        self.calls.append(("start_parse_job", file_id))
        return ParseJobSubmitResponse(
            job_id="job-123",
            status=ParseJobStatus.pending,
            raw_response={"job": {"id": "job-123", "status": "PENDING"}},
        )

    def poll_parse_job(
        self,
        job_id: str,
        expand: list[str] | None = None,
        config: ParseJobPollingConfig | None = None,
    ) -> ParseJobResult:
        self.calls.append(("poll_parse_job", {"job_id": job_id, "expand": expand, "config": config}))
        return ParseJobResult(
            job_id=job_id,
            status=ParseJobStatus.completed,
            markdown="# Parsed document",
            raw_response={"job": {"id": job_id, "status": "COMPLETED"}},
        )

    def close(self) -> None:
        self.closed = True


def test_run_parse_job_with_polling_orchestrates_upload_submit_and_poll() -> None:
    client = FakeLlamaParseRestClient()
    polling_config = ParseJobPollingConfig(max_attempts=3, interval_seconds=0.0)

    result = run_parse_job_with_polling(
        source_pdf_path="document.pdf",
        expand=["markdown"],
        polling_config=polling_config,
        client=client,
    )

    assert result.job_id == "job-123"
    assert result.status == ParseJobStatus.completed
    assert result.markdown == "# Parsed document"
    assert client.calls == [
        ("upload_file", "document.pdf"),
        ("start_parse_job", "file-123"),
        ("poll_parse_job", {"job_id": "job-123", "expand": ["markdown"], "config": polling_config}),
    ]
    assert client.closed is False