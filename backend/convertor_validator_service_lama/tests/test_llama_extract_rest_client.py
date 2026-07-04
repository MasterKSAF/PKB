import json

import httpx
import pytest

from convertor_validator_service_lama.clients.llama_extract_rest_client import (
    LlamaExtractJobFailedError,
    LlamaExtractPollingTimeoutError,
    LlamaExtractRestClient,
)
from convertor_validator_service_lama.core.settings import Settings
from convertor_validator_service_lama.models.extract_job import (
    ExtractJobPollingConfig,
    ExtractJobStatus,
    ExtractPassRequest,
)


def _settings() -> Settings:
    return Settings(
        cloud_api_key="test-key",
        extract_base_url="https://llama.test",
        extract_project_id="project-123",
    )


def test_start_extract_job_posts_parse_job_id_as_file_input() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/v2/extract"
        assert request.url.params["project_id"] == "project-123"
        assert request.headers["Authorization"] == "Bearer test-key"
        assert request.headers["Content-Type"] == "application/json"

        payload = json.loads(request.content.decode("utf-8"))
        assert payload == {
            "file_input": "parse-job-123",
            "configuration": {
                "tier": "agentic",
                "extraction_target": "per_doc",
                "data_schema": {"type": "object"},
                "system_prompt": "Extract sections.",
                "schema_name": "sections_schema",
            },
        }

        return httpx.Response(
            200,
            json={
                "job": {
                    "id": "extract-job-123",
                    "status": "PENDING",
                }
            },
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = LlamaExtractRestClient(settings=_settings(), http_client=http_client)

    response = client.start_extract_job(
        ExtractPassRequest(
            parse_job_id="parse-job-123",
            pass_name="sections",
            project_id="project-123",
            schema_name="sections_schema",
            extraction_schema={"type": "object"},
            instructions="Extract sections.",
        )
    )

    assert response.job_id == "extract-job-123"
    assert response.pass_name == "sections"
    assert response.status == ExtractJobStatus.pending


def test_get_extract_job_returns_completed_result() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v2/extract/extract-job-123"
        assert request.url.params["project_id"] == "project-123"
        assert request.headers["Authorization"] == "Bearer test-key"

        return httpx.Response(
            200,
            json={
                "job": {
                    "id": "extract-job-123",
                    "status": "COMPLETED",
                },
                "extract_result": {
                    "sections": [
                        {"title": "1. Scope", "page": 1},
                    ]
                },
            },
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = LlamaExtractRestClient(settings=_settings(), http_client=http_client)

    result = client.get_extract_job(
        job_id="extract-job-123",
        pass_name="sections",
        project_id="project-123",
        expand=["extract_result"],
    )

    assert result.job_id == "extract-job-123"
    assert result.pass_name == "sections"
    assert result.status == ExtractJobStatus.completed
    assert result.result == {
        "sections": [
            {"title": "1. Scope", "page": 1},
        ]
    }


def test_poll_extract_job_waits_until_completed() -> None:
    statuses = ["PENDING", "RUNNING", "COMPLETED"]
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        status = statuses.pop(0)
        return httpx.Response(
            200,
            json={
                "job": {
                    "id": "extract-job-123",
                    "status": status,
                },
                "extract_result": {"ok": True} if status == "COMPLETED" else {},
            },
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = LlamaExtractRestClient(
        settings=_settings(),
        http_client=http_client,
        sleep_func=sleeps.append,
    )

    result = client.poll_extract_job(
        job_id="extract-job-123",
        pass_name="sections",
        project_id="project-123",
        expand=["extract_result"],
        config=ExtractJobPollingConfig(max_attempts=3, interval_seconds=0.1),
    )

    assert result.status == ExtractJobStatus.completed
    assert result.result == {"ok": True}
    assert sleeps == [0.1, 0.1]


def test_poll_extract_job_raises_on_failed_status() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "job": {
                    "id": "extract-job-123",
                    "status": "FAILED",
                }
            },
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = LlamaExtractRestClient(settings=_settings(), http_client=http_client)

    with pytest.raises(LlamaExtractJobFailedError):
        client.poll_extract_job(
            job_id="extract-job-123",
            pass_name="sections",
            project_id="project-123",
            config=ExtractJobPollingConfig(max_attempts=1, interval_seconds=0.0),
        )


def test_poll_extract_job_raises_on_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "job": {
                    "id": "extract-job-123",
                    "status": "RUNNING",
                }
            },
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = LlamaExtractRestClient(
        settings=_settings(),
        http_client=http_client,
        sleep_func=lambda seconds: None,
    )

    with pytest.raises(LlamaExtractPollingTimeoutError):
        client.poll_extract_job(
            job_id="extract-job-123",
            pass_name="sections",
            project_id="project-123",
            config=ExtractJobPollingConfig(max_attempts=2, interval_seconds=0.0),
        )