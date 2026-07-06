from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from convertor_validator_service_lama.clients.llama_extract_rest_client import (
    LlamaExtractRestClient,
    MissingLlamaExtractProjectIdError,
)
from convertor_validator_service_lama.core.settings import Settings, get_settings
from convertor_validator_service_lama.models.contracts import LlamaExtractPassName
from convertor_validator_service_lama.models.extract_job import (
    ExtractJobPollingConfig,
    ExtractJobResult,
    ExtractJobSubmitResponse,
    ExtractPassRequest,
)
from convertor_validator_service_lama.services.document_structure_prompt_agent import (
    StructuredJsonPromptBackend,
    parse_json_object_response,
)


class LlamaExtractStructuredJsonBackendError(Exception):
    pass


class MissingLlamaExtractParseJobIdError(LlamaExtractStructuredJsonBackendError):
    pass


class LlamaExtractStructuredJsonResultError(LlamaExtractStructuredJsonBackendError):
    pass


class LlamaExtractClientLike(Protocol):
    def start_extract_job(self, request: ExtractPassRequest) -> ExtractJobSubmitResponse:
        ...

    def poll_extract_job(
        self,
        job_id: str,
        pass_name: str,
        project_id: str,
        expand: list[str] | None = None,
        config: ExtractJobPollingConfig | None = None,
    ) -> ExtractJobResult:
        ...

    def close(self) -> None:
        ...


@dataclass(frozen=True)
class LlamaExtractStructuredJsonPromptBackendConfig:
    parse_job_id: str | None = None
    parse_job_id_metadata_key: str = "job_id"
    pass_name: LlamaExtractPassName = "sections"
    schema_name: str = "document_structure_extraction_v1"
    expand: list[str] | None = None
    polling_config: ExtractJobPollingConfig | None = None
    include_metadata_in_instructions: bool = True


class LlamaExtractStructuredJsonPromptBackend(StructuredJsonPromptBackend):
    """StructuredJsonPromptBackend implementation backed by LlamaExtract.

    This adapter is intentionally narrow:
    - it uses the existing LlamaExtractRestClient contract;
    - it submits one extract job per structured prompt call;
    - it returns only the extract_result JSON object;
    - it does not know about document-structure workflow stages.
    """

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        client: LlamaExtractClientLike | None = None,
        config: LlamaExtractStructuredJsonPromptBackendConfig | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._client = client or LlamaExtractRestClient(self._settings)
        self._owns_client = client is None
        self._config = config or LlamaExtractStructuredJsonPromptBackendConfig()

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        json_schema: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        project_id = self._settings.extract_project_id
        if not project_id:
            raise MissingLlamaExtractProjectIdError(
                "LAMA_EXTRACT_PROJECT_ID is required for LlamaExtract network calls."
            )

        parse_job_id = self._resolve_parse_job_id(metadata or {})

        request = ExtractPassRequest(
            parse_job_id=parse_job_id,
            pass_name=self._config.pass_name,
            project_id=project_id,
            schema_name=self._config.schema_name,
            extraction_schema=json_schema,
            instructions=self._build_instructions(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                metadata=metadata or {},
            ),
        )

        submit_response = self._client.start_extract_job(request)
        result = self._client.poll_extract_job(
            job_id=submit_response.job_id,
            pass_name=self._config.pass_name,
            project_id=project_id,
            expand=self._config.expand or ["extract_result"],
            config=self._config.polling_config,
        )

        return self._extract_json_object(result)

    def _resolve_parse_job_id(self, metadata: dict[str, Any]) -> str:
        if self._config.parse_job_id:
            return self._config.parse_job_id

        value = metadata.get(self._config.parse_job_id_metadata_key)
        if isinstance(value, str) and value.strip():
            return value.strip()

        raise MissingLlamaExtractParseJobIdError(
            "parse_job_id is required either in backend config or in metadata."
        )

    def _build_instructions(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        metadata: dict[str, Any],
    ) -> str:
        parts = [
            system_prompt.strip(),
            "",
            "User prompt:",
            user_prompt.strip(),
        ]

        if self._config.include_metadata_in_instructions and metadata:
            parts.extend(
                [
                    "",
                    "Stage metadata:",
                    _format_metadata(metadata),
                ]
            )

        return "\n".join(parts).strip()

    def _extract_json_object(self, result: ExtractJobResult) -> dict[str, Any]:
        payload = result.result

        if not payload:
            raise LlamaExtractStructuredJsonResultError(
                "LlamaExtract extract_result is empty."
            )

        try:
            return parse_json_object_response(payload)
        except (TypeError, ValueError) as exc:
            raise LlamaExtractStructuredJsonResultError(
                "LlamaExtract extract_result must be a JSON object."
            ) from exc


def _format_metadata(metadata: dict[str, Any]) -> str:
    lines: list[str] = []

    for key in sorted(metadata):
        value = metadata[key]
        if isinstance(value, str | int | float | bool) or value is None:
            lines.append(f"{key}: {value}")

    return "\n".join(lines)
