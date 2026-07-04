import pytest
from pydantic import ValidationError

from convertor_validator_service_lama.models.parse_job import (
    ParseJobPollingConfig,
    ParseJobResult,
    ParseJobStatus,
    ParseJobSubmitResponse,
)


def test_parse_job_status_values_match_llamaparse_rest_statuses() -> None:
    assert {status.value for status in ParseJobStatus} == {
        "PENDING",
        "RUNNING",
        "COMPLETED",
        "FAILED",
        "CANCELLED",
    }


def test_parse_job_submit_response_accepts_raw_response() -> None:
    response = ParseJobSubmitResponse(
        job_id="job-123",
        status=ParseJobStatus.pending,
        raw_response={"id": "job-123", "status": "PENDING"},
    )

    assert response.job_id == "job-123"
    assert response.status == ParseJobStatus.pending
    assert response.raw_response == {"id": "job-123", "status": "PENDING"}


def test_parse_job_result_defaults_optional_artifacts() -> None:
    result = ParseJobResult(
        job_id="job-123",
        status=ParseJobStatus.completed,
    )

    assert result.markdown is None
    assert result.items == []
    assert result.metadata == {}
    assert result.job_metadata == {}
    assert result.raw_response == {}


def test_parse_job_polling_config_defaults() -> None:
    config = ParseJobPollingConfig()

    assert config.max_attempts == 60
    assert config.interval_seconds == 2.0


def test_parse_job_polling_config_rejects_invalid_values() -> None:
    with pytest.raises(ValidationError):
        ParseJobPollingConfig(max_attempts=0)

    with pytest.raises(ValidationError):
        ParseJobPollingConfig(interval_seconds=-1)