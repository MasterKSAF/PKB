import pytest
from fastapi.testclient import TestClient

from convertor_validator_service_lama.api import app as app_module
from convertor_validator_service_lama.clients.llama_cloud_boundary import (
    MissingLlamaCloudApiKeyError,
)
from convertor_validator_service_lama.clients.llama_extract_rest_client import (
    LlamaExtractJobFailedError,
    LlamaExtractPollingTimeoutError,
    LlamaExtractResponseError,
    MissingLlamaExtractProjectIdError,
)
from convertor_validator_service_lama.models.extract_job import (
    ExtractJobPollingConfig,
    ExtractJobResult,
    ExtractJobStatus,
)


def test_extract_pass_endpoint_runs_service_orchestration(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run_extract_pass_with_polling(
        parse_job_id: str,
        pass_name: str,
        extraction_schema: dict[str, object],
        instructions: str | None,
        schema_name: str | None,
        expand: list[str],
        polling_config: ExtractJobPollingConfig,
    ) -> ExtractJobResult:
        captured["parse_job_id"] = parse_job_id
        captured["pass_name"] = pass_name
        captured["extraction_schema"] = extraction_schema
        captured["instructions"] = instructions
        captured["schema_name"] = schema_name
        captured["expand"] = expand
        captured["polling_config"] = polling_config

        return ExtractJobResult(
            job_id="extract-job-123",
            pass_name="sections",
            status=ExtractJobStatus.completed,
            result={"sections": [{"title": "1. Scope"}]},
            raw_response={"job": {"id": "extract-job-123", "status": "COMPLETED"}},
        )

    monkeypatch.setattr(
        app_module,
        "run_extract_pass_with_polling",
        fake_run_extract_pass_with_polling,
    )

    client = TestClient(app_module.app)

    response = client.post(
        "/extract-pass",
        json={
            "parse_job_id": "parse-job-123",
            "pass_name": "sections",
            "extraction_schema": {"type": "object"},
            "instructions": "Extract sections.",
            "schema_name": "sections_schema",
            "expand": ["extract_result"],
            "max_attempts": 3,
            "interval_seconds": 0.0,
        },
    )

    assert response.status_code == 200
    assert response.json()["job_id"] == "extract-job-123"
    assert response.json()["pass_name"] == "sections"
    assert response.json()["status"] == "COMPLETED"
    assert response.json()["result"] == {"sections": [{"title": "1. Scope"}]}

    assert captured["parse_job_id"] == "parse-job-123"
    assert captured["pass_name"] == "sections"
    assert captured["extraction_schema"] == {"type": "object"}
    assert captured["instructions"] == "Extract sections."
    assert captured["schema_name"] == "sections_schema"
    assert captured["expand"] == ["extract_result"]
    assert captured["polling_config"] == ExtractJobPollingConfig(
        max_attempts=3,
        interval_seconds=0.0,
    )


@pytest.mark.parametrize(
    ("exception", "expected_status_code"),
    [
        (MissingLlamaCloudApiKeyError("missing api key"), 400),
        (MissingLlamaExtractProjectIdError("missing extract project id"), 400),
        (LlamaExtractPollingTimeoutError("polling timeout"), 504),
        (LlamaExtractJobFailedError("job failed"), 502),
        (LlamaExtractResponseError("bad upstream response"), 502),
    ],
)
def test_extract_pass_endpoint_maps_service_errors_to_http_errors(
    monkeypatch,
    exception: Exception,
    expected_status_code: int,
) -> None:
    def fake_run_extract_pass_with_polling(
        parse_job_id: str,
        pass_name: str,
        extraction_schema: dict[str, object],
        instructions: str | None,
        schema_name: str | None,
        expand: list[str],
        polling_config: ExtractJobPollingConfig,
    ) -> ExtractJobResult:
        raise exception

    monkeypatch.setattr(
        app_module,
        "run_extract_pass_with_polling",
        fake_run_extract_pass_with_polling,
    )

    client = TestClient(app_module.app)

    response = client.post(
        "/extract-pass",
        json={
            "parse_job_id": "parse-job-123",
            "pass_name": "sections",
            "extraction_schema": {"type": "object"},
            "expand": ["extract_result"],
            "max_attempts": 1,
            "interval_seconds": 0.0,
        },
    )

    assert response.status_code == expected_status_code
    assert response.json()["detail"]