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


def test_extract_passes_endpoint_runs_all_planned_passes(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run_all_extract_passes_with_polling(
        parse_job_id: str,
        extraction_schemas: dict[str, dict[str, object]],
        instructions_by_pass: dict[str, str],
        schema_names_by_pass: dict[str, str],
        expand: list[str],
        polling_config: ExtractJobPollingConfig,
    ) -> dict[str, ExtractJobResult]:
        captured["parse_job_id"] = parse_job_id
        captured["extraction_schemas"] = extraction_schemas
        captured["instructions_by_pass"] = instructions_by_pass
        captured["schema_names_by_pass"] = schema_names_by_pass
        captured["expand"] = expand
        captured["polling_config"] = polling_config

        return {
            "sections": ExtractJobResult(
                job_id="extract-job-sections",
                pass_name="sections",
                status=ExtractJobStatus.completed,
                result={"sections": [{"title": "1. Scope"}]},
                raw_response={"job": {"id": "extract-job-sections", "status": "COMPLETED"}},
            ),
            "tables": ExtractJobResult(
                job_id="extract-job-tables",
                pass_name="tables",
                status=ExtractJobStatus.completed,
                result={"tables": []},
                raw_response={"job": {"id": "extract-job-tables", "status": "COMPLETED"}},
            ),
        }

    monkeypatch.setattr(
        app_module,
        "run_all_extract_passes_with_polling",
        fake_run_all_extract_passes_with_polling,
    )

    client = TestClient(app_module.app)

    response = client.post(
        "/extract-passes",
        json={
            "parse_job_id": "parse-job-123",
            "extraction_schemas": {
                "sections": {"type": "object"},
            },
            "instructions_by_pass": {
                "sections": "Extract sections.",
            },
            "schema_names_by_pass": {
                "sections": "sections_schema",
            },
            "expand": ["extract_result"],
            "max_attempts": 3,
            "interval_seconds": 0.0,
        },
    )

    assert response.status_code == 200
    assert response.json()["sections"]["job_id"] == "extract-job-sections"
    assert response.json()["sections"]["status"] == "COMPLETED"
    assert response.json()["sections"]["result"] == {"sections": [{"title": "1. Scope"}]}
    assert response.json()["tables"]["job_id"] == "extract-job-tables"

    assert captured["parse_job_id"] == "parse-job-123"
    assert captured["extraction_schemas"] == {"sections": {"type": "object"}}
    assert captured["instructions_by_pass"] == {"sections": "Extract sections."}
    assert captured["schema_names_by_pass"] == {"sections": "sections_schema"}
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
def test_extract_passes_endpoint_maps_service_errors_to_http_errors(
    monkeypatch,
    exception: Exception,
    expected_status_code: int,
) -> None:
    def fake_run_all_extract_passes_with_polling(
        parse_job_id: str,
        extraction_schemas: dict[str, dict[str, object]],
        instructions_by_pass: dict[str, str],
        schema_names_by_pass: dict[str, str],
        expand: list[str],
        polling_config: ExtractJobPollingConfig,
    ) -> dict[str, ExtractJobResult]:
        raise exception

    monkeypatch.setattr(
        app_module,
        "run_all_extract_passes_with_polling",
        fake_run_all_extract_passes_with_polling,
    )

    client = TestClient(app_module.app)

    response = client.post(
        "/extract-passes",
        json={
            "parse_job_id": "parse-job-123",
            "extraction_schemas": {
                "sections": {"type": "object"},
            },
            "instructions_by_pass": {
                "sections": "Extract sections.",
            },
            "schema_names_by_pass": {
                "sections": "sections_schema",
            },
            "expand": ["extract_result"],
            "max_attempts": 1,
            "interval_seconds": 0.0,
        },
    )

    assert response.status_code == expected_status_code
    assert response.json()["detail"]