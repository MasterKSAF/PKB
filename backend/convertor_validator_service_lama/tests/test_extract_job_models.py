import pytest
from pydantic import ValidationError

from convertor_validator_service_lama.models.extract_job import (
    ExtractJobPollingConfig,
    ExtractJobResult,
    ExtractJobStatus,
    ExtractJobSubmitResponse,
    ExtractPassRequest,
)


def test_extract_job_status_values_match_expected_job_statuses() -> None:
    assert {status.value for status in ExtractJobStatus} == {
        "PENDING",
        "RUNNING",
        "COMPLETED",
        "FAILED",
        "CANCELLED",
    }


def test_extract_pass_request_uses_parse_job_id_as_input() -> None:
    request = ExtractPassRequest(
        parse_job_id="pjb-123",
        pass_name="sections",
        project_id="project-123",
        schema_name="sections_schema",
        extraction_schema={"type": "object"},
        instructions="Extract document sections.",
    )

    assert request.parse_job_id == "pjb-123"
    assert request.pass_name == "sections"
    assert request.project_id == "project-123"
    assert request.schema_name == "sections_schema"
    assert request.extraction_schema == {"type": "object"}
    assert request.instructions == "Extract document sections."


def test_extract_job_submit_response_accepts_raw_response() -> None:
    response = ExtractJobSubmitResponse(
        job_id="extract-job-123",
        pass_name="tables",
        status=ExtractJobStatus.pending,
        raw_response={"id": "extract-job-123", "status": "PENDING"},
    )

    assert response.job_id == "extract-job-123"
    assert response.pass_name == "tables"
    assert response.status == ExtractJobStatus.pending
    assert response.raw_response == {"id": "extract-job-123", "status": "PENDING"}


def test_extract_job_result_defaults_result_payload() -> None:
    result = ExtractJobResult(
        job_id="extract-job-123",
        pass_name="images",
        status=ExtractJobStatus.completed,
    )

    assert result.result == {}
    assert result.raw_response == {}


def test_extract_job_polling_config_defaults() -> None:
    config = ExtractJobPollingConfig()

    assert config.max_attempts == 60
    assert config.interval_seconds == 2.0


def test_extract_job_polling_config_rejects_invalid_values() -> None:
    with pytest.raises(ValidationError):
        ExtractJobPollingConfig(max_attempts=0)

    with pytest.raises(ValidationError):
        ExtractJobPollingConfig(interval_seconds=-1)