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
            },
        }

        assert "schema_name" not in payload
        assert "schema_name" not in payload["configuration"]

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

from convertor_validator_service_lama.clients.llama_extract_rest_client import LlamaExtractResponseError, LlamaExtractRestClient

from typing import Any

import httpx
import pytest

from convertor_validator_service_lama.clients.llama_extract_rest_client import (
    LlamaExtractResponseError,
    LlamaExtractRestClient,
)
from convertor_validator_service_lama.core.settings import Settings
from convertor_validator_service_lama.models.extract_job import ExtractPassRequest


class FakeHttpClient:
    def __init__(self, *, post_response: httpx.Response) -> None:
        self.post_response = post_response
        self.post_calls: list[dict[str, Any]] = []
        self.closed = False

    def post(
        self,
        url: str,
        *,
        headers: dict[str, str],
        params: dict[str, Any],
        json: dict[str, Any],
    ) -> httpx.Response:
        self.post_calls.append(
            {
                "url": url,
                "headers": headers,
                "params": params,
                "json": json,
            }
        )
        return self.post_response

    def close(self) -> None:
        self.closed = True


def make_settings() -> Settings:
    return Settings(
        cloud_api_key="test-key",
        extract_base_url="https://llama.test",
        extract_project_id="project-123",
    )


def test_start_extract_job_builds_llama_extract_v2_payload_without_schema_name() -> None:
    http_client = FakeHttpClient(
        post_response=httpx.Response(
            200,
            json={
                "id": "ext-job-123",
                "status": "PENDING",
            },
            request=httpx.Request("POST", "https://llama.test/api/v2/extract"),
        )
    )
    client = LlamaExtractRestClient(
        settings=make_settings(),
        http_client=http_client,
    )

    result = client.start_extract_job(
        ExtractPassRequest(
            parse_job_id="pjb-parse-job-123",
            pass_name="sections",
            project_id="project-123",
            schema_name="document_structure_extraction_v1",
            extraction_schema={
                "type": "object",
                "properties": {
                    "answer": {"type": "string"},
                },
            },
            instructions="Extract document structure.",
        )
    )

    assert result.job_id == "ext-job-123"
    assert result.status == "PENDING"

    call = http_client.post_calls[0]

    assert call["url"] == "https://llama.test/api/v2/extract"
    assert call["params"] == {"project_id": "project-123"}

    payload = call["json"]

    assert payload == {
        "file_input": "pjb-parse-job-123",
        "configuration": {
            "tier": "agentic",
            "extraction_target": "per_doc",
            "data_schema": {
                "type": "object",
                "properties": {
                    "answer": {"type": "string"},
                },
            },
            "system_prompt": "Extract document structure.",
        },
    }

    assert "schema_name" not in payload
    assert "schema_name" not in payload["configuration"]


def test_start_extract_job_error_includes_upstream_response_body() -> None:
    http_client = FakeHttpClient(
        post_response=httpx.Response(
            400,
            text='{"detail":"extra field schema_name is not permitted"}',
            request=httpx.Request("POST", "https://llama.test/api/v2/extract"),
        )
    )
    client = LlamaExtractRestClient(
        settings=make_settings(),
        http_client=http_client,
    )

    with pytest.raises(LlamaExtractResponseError) as exc_info:
        client.start_extract_job(
            ExtractPassRequest(
                parse_job_id="pjb-parse-job-123",
                pass_name="sections",
                project_id="project-123",
                schema_name="document_structure_extraction_v1",
                extraction_schema={"type": "object"},
                instructions="Extract document structure.",
            )
        )

    message = str(exc_info.value)

    assert "400 Bad Request" in message
    assert "response_body=" in message
    assert "schema_name" in message

def test_get_extract_job_omits_invalid_extract_result_expand() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v2/extract/extract-job-123"
        assert request.url.params["project_id"] == "project-123"
        assert "expand" not in request.url.params

        return httpx.Response(
            200,
            json={
                "id": "extract-job-123",
                "status": "COMPLETED",
                "extract_result": {
                    "ok": True,
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

    assert result.result == {"ok": True}


def test_get_extract_job_keeps_valid_v2_expand_values() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v2/extract/extract-job-123"
        assert request.url.params["project_id"] == "project-123"
        assert request.url.params["expand"] == "configuration"

        return httpx.Response(
            200,
            json={
                "id": "extract-job-123",
                "status": "COMPLETED",
                "extract_result": {
                    "ok": True,
                },
            },
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = LlamaExtractRestClient(settings=_settings(), http_client=http_client)

    result = client.get_extract_job(
        job_id="extract-job-123",
        pass_name="sections",
        project_id="project-123",
        expand=["extract_result", "configuration"],
    )

    assert result.result == {"ok": True}
