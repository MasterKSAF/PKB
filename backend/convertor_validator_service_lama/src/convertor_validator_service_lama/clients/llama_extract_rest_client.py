from collections.abc import Callable, Sequence
from time import sleep
from typing import Any

import httpx

from convertor_validator_service_lama.clients.llama_cloud_boundary import LlamaCloudBoundary
from convertor_validator_service_lama.core.settings import Settings
from convertor_validator_service_lama.models.extract_job import (
    ExtractJobPollingConfig,
    ExtractJobResult,
    ExtractJobStatus,
    ExtractJobSubmitResponse,
    ExtractPassRequest,
)


class LlamaExtractRestClientError(Exception):
    pass


class MissingLlamaExtractProjectIdError(LlamaExtractRestClientError):
    pass


class LlamaExtractResponseError(LlamaExtractRestClientError):
    pass


class LlamaExtractJobFailedError(LlamaExtractRestClientError):
    pass


class LlamaExtractPollingTimeoutError(LlamaExtractRestClientError):
    pass


class LlamaExtractRestClient:
    def __init__(
        self,
        settings: Settings,
        http_client: httpx.Client | None = None,
        sleep_func: Callable[[float], None] = sleep,
    ) -> None:
        self._settings = settings
        self._boundary = LlamaCloudBoundary(settings)
        self._http_client = http_client or httpx.Client(timeout=30.0)
        self._owns_http_client = http_client is None
        self._sleep = sleep_func

    def close(self) -> None:
        if self._owns_http_client:
            self._http_client.close()

    def start_extract_job(self, request: ExtractPassRequest) -> ExtractJobSubmitResponse:
        payload = self._build_extract_payload(request)

        response = self._http_client.post(
            self._url("/api/v2/extract"),
            headers=self._json_headers(),
            params={"project_id": request.project_id},
            json=payload,
        )

        raw_response = self._read_json_response(response)
        job = self._extract_job(raw_response)
        job_id = self._extract_job_id(job, raw_response)
        status = self._extract_status(job, raw_response, required=False)

        return ExtractJobSubmitResponse(
            job_id=job_id,
            pass_name=request.pass_name,
            status=status,
            raw_response=raw_response,
        )

    def get_extract_job(
        self,
        job_id: str,
        pass_name: str,
        project_id: str,
        expand: Sequence[str] | None = None,
    ) -> ExtractJobResult:
        params: dict[str, str | list[str]] = {"project_id": project_id}
        if expand:
            params["expand"] = list(expand)

        response = self._http_client.get(
            self._url(f"/api/v2/extract/{job_id}"),
            headers=self._boundary.build_auth_headers(),
            params=params,
        )

        raw_response = self._read_json_response(response)
        job = self._extract_job(raw_response)
        parsed_job_id = self._extract_job_id(job, raw_response)
        status = self._extract_status(job, raw_response, required=True)

        return ExtractJobResult(
            job_id=parsed_job_id,
            pass_name=pass_name,
            status=status,
            result=self._as_dict(raw_response.get("extract_result")),
            raw_response=raw_response,
        )

    def poll_extract_job(
        self,
        job_id: str,
        pass_name: str,
        project_id: str,
        expand: Sequence[str] | None = None,
        config: ExtractJobPollingConfig | None = None,
    ) -> ExtractJobResult:
        polling_config = config or ExtractJobPollingConfig()

        for attempt in range(polling_config.max_attempts):
            result = self.get_extract_job(
                job_id=job_id,
                pass_name=pass_name,
                project_id=project_id,
                expand=expand,
            )

            if result.status == ExtractJobStatus.completed:
                return result

            if result.status in {ExtractJobStatus.failed, ExtractJobStatus.cancelled}:
                raise LlamaExtractJobFailedError(
                    f"LlamaExtract job {job_id} ended with status {result.status.value}."
                )

            if attempt < polling_config.max_attempts - 1:
                self._sleep(polling_config.interval_seconds)

        raise LlamaExtractPollingTimeoutError(
            f"LlamaExtract job {job_id} did not complete after {polling_config.max_attempts} attempts."
        )

    def _build_extract_payload(self, request: ExtractPassRequest) -> dict[str, Any]:
        configuration: dict[str, Any] = {
            "tier": "agentic",
            "extraction_target": "per_doc",
            "data_schema": request.extraction_schema,
        }

        if request.instructions:
            configuration["system_prompt"] = request.instructions

        if request.schema_name:
            configuration["schema_name"] = request.schema_name

        return {
            "file_input": request.parse_job_id,
            "configuration": configuration,
        }

    def _url(self, path: str) -> str:
        return f"{self._settings.extract_base_url.rstrip('/')}{path}"

    def _json_headers(self) -> dict[str, str]:
        headers = self._boundary.build_auth_headers()
        headers["Content-Type"] = "application/json"
        return headers

    def _read_json_response(self, response: httpx.Response) -> dict[str, Any]:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise LlamaExtractResponseError(str(exc)) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise LlamaExtractResponseError("LlamaExtract response is not valid JSON.") from exc

        if not isinstance(data, dict):
            raise LlamaExtractResponseError("LlamaExtract response JSON must be an object.")

        return data

    def _extract_job(self, raw_response: dict[str, Any]) -> dict[str, Any]:
        job = raw_response.get("job")
        if isinstance(job, dict):
            return job
        return raw_response

    def _extract_job_id(self, job: dict[str, Any], raw_response: dict[str, Any]) -> str:
        job_id = job.get("id") or raw_response.get("job_id") or raw_response.get("id")
        if not job_id:
            raise LlamaExtractResponseError("LlamaExtract response does not contain job id.")
        return str(job_id)

    def _extract_status(
        self,
        job: dict[str, Any],
        raw_response: dict[str, Any],
        required: bool,
    ) -> ExtractJobStatus | None:
        raw_status = job.get("status") or raw_response.get("status")
        if raw_status is None:
            if required:
                raise LlamaExtractResponseError("LlamaExtract response does not contain job status.")
            return None

        try:
            return ExtractJobStatus(str(raw_status))
        except ValueError as exc:
            raise LlamaExtractResponseError(f"Unknown LlamaExtract job status: {raw_status}") from exc

    def _as_dict(self, value: Any) -> dict[str, Any]:
        return value if isinstance(value, dict) else {}