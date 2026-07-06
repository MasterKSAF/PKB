from __future__ import annotations

from typing import Any

import pytest

from convertor_validator_service_lama.core.settings import Settings
from convertor_validator_service_lama.models.extract_job import (
    ExtractJobPollingConfig,
    ExtractJobResult,
    ExtractJobStatus,
    ExtractJobSubmitResponse,
    ExtractPassRequest,
)
from convertor_validator_service_lama.services.llama_extract_structured_json_backend import (
    LlamaExtractStructuredJsonPromptBackend,
    LlamaExtractStructuredJsonPromptBackendConfig,
    LlamaExtractStructuredJsonResultError,
    MissingLlamaExtractParseJobIdError,
)
from convertor_validator_service_lama.clients.llama_extract_rest_client import (
    MissingLlamaExtractProjectIdError,
)


class FakeLlamaExtractClient:
    def __init__(self, result_payload: dict[str, Any] | None = None) -> None:
        self.result_payload = {"ok": True} if result_payload is None else result_payload
        self.start_requests: list[ExtractPassRequest] = []
        self.poll_calls: list[dict[str, Any]] = []
        self.closed = False

    def start_extract_job(self, request: ExtractPassRequest) -> ExtractJobSubmitResponse:
        self.start_requests.append(request)
        return ExtractJobSubmitResponse(
            job_id="extract-job-123",
            pass_name=request.pass_name,
            status=ExtractJobStatus.pending,
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
            result=self.result_payload,
        )

    def close(self) -> None:
        self.closed = True


def make_settings(project_id: str | None = "project-123") -> Settings:
    return Settings(
        cloud_api_key="test-key",
        extract_base_url="https://llama.test",
        extract_project_id=project_id,
    )


def test_llama_extract_backend_submits_structured_prompt_and_returns_result():
    client = FakeLlamaExtractClient(
        result_payload={
            "schema_version": "document_structure_extraction_v1",
            "document_profile": "UNKNOWN",
            "numbering_scopes": [
                {
                    "namespace_id": "main_document",
                    "title": "Main document",
                    "scope_type": "MAIN_DOCUMENT",
                    "confidence": 0.9,
                    "reason": "Fake.",
                }
            ],
        }
    )
    backend = LlamaExtractStructuredJsonPromptBackend(
        settings=make_settings(),
        client=client,
        config=LlamaExtractStructuredJsonPromptBackendConfig(
            parse_job_id="parse-job-123",
            pass_name="sections",
            schema_name="document_structure_extraction_v1",
        ),
    )

    result = backend.generate_json(
        system_prompt="System prompt.",
        user_prompt="User prompt.",
        json_schema={"type": "object", "title": "DocumentStructureExtraction"},
        metadata={
            "agent_stage_type": "overview",
            "stage_id": "overview",
            "job_id": "ignored-because-config-wins",
        },
    )

    assert result["schema_version"] == "document_structure_extraction_v1"

    request = client.start_requests[0]
    assert request.parse_job_id == "parse-job-123"
    assert request.pass_name == "sections"
    assert request.project_id == "project-123"
    assert request.schema_name == "document_structure_extraction_v1"
    assert request.extraction_schema == {
        "type": "object",
        "title": "DocumentStructureExtraction",
    }
    assert "System prompt." in (request.instructions or "")
    assert "User prompt." in (request.instructions or "")
    assert "agent_stage_type: overview" in (request.instructions or "")
    assert "stage_id: overview" in (request.instructions or "")

    assert client.poll_calls == [
        {
            "job_id": "extract-job-123",
            "pass_name": "sections",
            "project_id": "project-123",
            "expand": ["extract_result"],
            "config": None,
        }
    ]


def test_llama_extract_backend_can_resolve_parse_job_id_from_metadata():
    client = FakeLlamaExtractClient()
    backend = LlamaExtractStructuredJsonPromptBackend(
        settings=make_settings(),
        client=client,
        config=LlamaExtractStructuredJsonPromptBackendConfig(
            parse_job_id=None,
            parse_job_id_metadata_key="job_id",
        ),
    )

    backend.generate_json(
        system_prompt="System",
        user_prompt="User",
        json_schema={"type": "object"},
        metadata={"job_id": "parse-job-from-metadata"},
    )

    assert client.start_requests[0].parse_job_id == "parse-job-from-metadata"


def test_llama_extract_backend_raises_without_parse_job_id():
    backend = LlamaExtractStructuredJsonPromptBackend(
        settings=make_settings(),
        client=FakeLlamaExtractClient(),
        config=LlamaExtractStructuredJsonPromptBackendConfig(parse_job_id=None),
    )

    with pytest.raises(MissingLlamaExtractParseJobIdError):
        backend.generate_json(
            system_prompt="System",
            user_prompt="User",
            json_schema={"type": "object"},
            metadata={},
        )


def test_llama_extract_backend_raises_without_project_id():
    backend = LlamaExtractStructuredJsonPromptBackend(
        settings=make_settings(project_id=None),
        client=FakeLlamaExtractClient(),
        config=LlamaExtractStructuredJsonPromptBackendConfig(
            parse_job_id="parse-job-123",
        ),
    )

    with pytest.raises(MissingLlamaExtractProjectIdError):
        backend.generate_json(
            system_prompt="System",
            user_prompt="User",
            json_schema={"type": "object"},
        )


def test_llama_extract_backend_passes_polling_config_and_expand():
    polling_config = ExtractJobPollingConfig(max_attempts=2, interval_seconds=0.0)
    client = FakeLlamaExtractClient()
    backend = LlamaExtractStructuredJsonPromptBackend(
        settings=make_settings(),
        client=client,
        config=LlamaExtractStructuredJsonPromptBackendConfig(
            parse_job_id="parse-job-123",
            expand=["extract_result", "raw"],
            polling_config=polling_config,
        ),
    )

    backend.generate_json(
        system_prompt="System",
        user_prompt="User",
        json_schema={"type": "object"},
    )

    assert client.poll_calls[0]["expand"] == ["extract_result", "raw"]
    assert client.poll_calls[0]["config"] == polling_config


def test_llama_extract_backend_can_omit_metadata_from_instructions():
    client = FakeLlamaExtractClient()
    backend = LlamaExtractStructuredJsonPromptBackend(
        settings=make_settings(),
        client=client,
        config=LlamaExtractStructuredJsonPromptBackendConfig(
            parse_job_id="parse-job-123",
            include_metadata_in_instructions=False,
        ),
    )

    backend.generate_json(
        system_prompt="System",
        user_prompt="User",
        json_schema={"type": "object"},
        metadata={"stage_id": "overview"},
    )

    assert "stage_id: overview" not in (client.start_requests[0].instructions or "")


def test_llama_extract_backend_rejects_empty_result():
    backend = LlamaExtractStructuredJsonPromptBackend(
        settings=make_settings(),
        client=FakeLlamaExtractClient(result_payload={}),
        config=LlamaExtractStructuredJsonPromptBackendConfig(
            parse_job_id="parse-job-123",
        ),
    )

    with pytest.raises(LlamaExtractStructuredJsonResultError, match="empty"):
        backend.generate_json(
            system_prompt="System",
            user_prompt="User",
            json_schema={"type": "object"},
        )


def test_llama_extract_backend_does_not_close_injected_client():
    client = FakeLlamaExtractClient()
    backend = LlamaExtractStructuredJsonPromptBackend(
        settings=make_settings(),
        client=client,
        config=LlamaExtractStructuredJsonPromptBackendConfig(
            parse_job_id="parse-job-123",
        ),
    )

    backend.close()

    assert client.closed is False
