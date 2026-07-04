import json
from pathlib import Path

import httpx
import pytest

from convertor_validator_service_lama.clients.llama_parse_rest_client import (
    LlamaParseJobFailedError,
    LlamaParsePollingTimeoutError,
    LlamaParseRestClient,
)
from convertor_validator_service_lama.core.settings import Settings
from convertor_validator_service_lama.models.parse_job import (
    ParseJobPollingConfig,
    ParseJobStatus,
)


def _settings() -> Settings:
    return Settings(
        cloud_api_key="test-key",
        parse_base_url="https://llama.test",
    )


def test_upload_file_returns_file_id(tmp_path: Path) -> None:
    pdf_path = tmp_path / "document.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/v1/beta/files"
        assert request.headers["Authorization"] == "Bearer test-key"
        return httpx.Response(200, json={"id": "file-123"})

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = LlamaParseRestClient(settings=_settings(), http_client=http_client)

    assert client.upload_file(str(pdf_path)) == "file-123"


def test_start_parse_job_posts_file_id_and_returns_job_id() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/v2/parse"
        assert request.headers["Authorization"] == "Bearer test-key"
        assert request.headers["Content-Type"] == "application/json"

        payload = json.loads(request.content.decode("utf-8"))
        assert payload == {
            "file_id": "file-123",
            "tier": "agentic",
            "version": "latest",
        }

        return httpx.Response(
            200,
            json={
                "job": {
                    "id": "job-123",
                    "status": "PENDING",
                }
            },
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = LlamaParseRestClient(settings=_settings(), http_client=http_client)

    response = client.start_parse_job(file_id="file-123")

    assert response.job_id == "job-123"
    assert response.status == ParseJobStatus.pending
    assert response.raw_response == {
        "job": {
            "id": "job-123",
            "status": "PENDING",
        }
    }


def test_get_parse_job_returns_completed_result_with_artifacts() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v2/parse/job-123"
        assert request.url.params["expand"] == "markdown,items,metadata"
        assert request.headers["Authorization"] == "Bearer test-key"

        return httpx.Response(
            200,
            json={
                "job": {
                    "id": "job-123",
                    "status": "COMPLETED",
                },
                "markdown_full": "# Parsed document",
                "items": [{"type": "text", "value": "Parsed document"}],
                "metadata": {"page_count": 1},
                "job_metadata": {"source": "test"},
            },
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = LlamaParseRestClient(settings=_settings(), http_client=http_client)

    result = client.get_parse_job(
        job_id="job-123",
        expand=["markdown", "items", "metadata"],
    )

    assert result.job_id == "job-123"
    assert result.status == ParseJobStatus.completed
    assert result.markdown == "# Parsed document"
    assert result.items == [{"type": "text", "value": "Parsed document"}]
    assert result.metadata == {"page_count": 1}
    assert result.job_metadata == {"source": "test"}


def test_poll_parse_job_waits_until_completed() -> None:
    statuses = ["PENDING", "RUNNING", "COMPLETED"]
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        status = statuses.pop(0)
        return httpx.Response(
            200,
            json={
                "job": {
                    "id": "job-123",
                    "status": status,
                },
                "markdown_full": "# Done" if status == "COMPLETED" else None,
            },
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = LlamaParseRestClient(
        settings=_settings(),
        http_client=http_client,
        sleep_func=sleeps.append,
    )

    result = client.poll_parse_job(
        job_id="job-123",
        expand=["markdown"],
        config=ParseJobPollingConfig(max_attempts=3, interval_seconds=0.1),
    )

    assert result.status == ParseJobStatus.completed
    assert result.markdown == "# Done"
    assert sleeps == [0.1, 0.1]


def test_poll_parse_job_raises_on_failed_status() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "job": {
                    "id": "job-123",
                    "status": "FAILED",
                }
            },
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = LlamaParseRestClient(settings=_settings(), http_client=http_client)

    with pytest.raises(LlamaParseJobFailedError):
        client.poll_parse_job(
            job_id="job-123",
            config=ParseJobPollingConfig(max_attempts=1, interval_seconds=0.0),
        )


def test_poll_parse_job_raises_on_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "job": {
                    "id": "job-123",
                    "status": "RUNNING",
                }
            },
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = LlamaParseRestClient(
        settings=_settings(),
        http_client=http_client,
        sleep_func=lambda seconds: None,
    )

    with pytest.raises(LlamaParsePollingTimeoutError):
        client.poll_parse_job(
            job_id="job-123",
            config=ParseJobPollingConfig(max_attempts=2, interval_seconds=0.0),
        )