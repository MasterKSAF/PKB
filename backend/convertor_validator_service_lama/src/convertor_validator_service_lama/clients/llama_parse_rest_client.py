from collections.abc import Callable, Sequence
from pathlib import Path
from time import sleep
from typing import Any

import httpx

from convertor_validator_service_lama.clients.llama_cloud_boundary import LlamaCloudBoundary
from convertor_validator_service_lama.core.settings import Settings
from convertor_validator_service_lama.models.parse_job import (
    ParseJobPollingConfig,
    ParseJobResult,
    ParseJobStatus,
    ParseJobSubmitResponse,
)


class LlamaParseRestClientError(Exception):
    pass


class LlamaParseResponseError(LlamaParseRestClientError):
    pass


class LlamaParseJobFailedError(LlamaParseRestClientError):
    pass


class LlamaParsePollingTimeoutError(LlamaParseRestClientError):
    pass


class LlamaParseRestClient:
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

    def upload_file(self, source_pdf_path: str) -> str:
        path = Path(source_pdf_path)
        if not path.is_file():
            raise FileNotFoundError(source_pdf_path)

        with path.open("rb") as file_obj:
            response = self._http_client.post(
                self._url("/api/v1/beta/files"),
                headers=self._boundary.build_auth_headers(),
                data={"purpose": "parse"},
                files={"file": (path.name, file_obj, "application/pdf")},
            )

        raw_response = self._read_json_response(response)
        file_id = raw_response.get("id")
        if not file_id:
            raise LlamaParseResponseError("LlamaParse upload response does not contain file id.")

        return str(file_id)

    def start_parse_job(
        self,
        file_id: str,
        tier: str = "agentic",
        version: str = "latest",
        options: dict[str, Any] | None = None,
    ) -> ParseJobSubmitResponse:
        payload: dict[str, Any] = {
            "file_id": file_id,
            "tier": tier,
            "version": version,
        }
        if options:
            payload.update(options)

        response = self._http_client.post(
            self._url("/api/v2/parse"),
            headers=self._json_headers(),
            json=payload,
        )

        raw_response = self._read_json_response(response)
        job = self._extract_job(raw_response)
        job_id = self._extract_job_id(job, raw_response)
        status = self._extract_status(job, raw_response, required=False)

        return ParseJobSubmitResponse(
            job_id=job_id,
            status=status,
            raw_response=raw_response,
        )

    def get_parse_job(
        self,
        job_id: str,
        expand: Sequence[str] | None = None,
    ) -> ParseJobResult:
        params = {"expand": ",".join(expand)} if expand else None

        response = self._http_client.get(
            self._url(f"/api/v2/parse/{job_id}"),
            headers=self._boundary.build_auth_headers(),
            params=params,
        )

        raw_response = self._read_json_response(response)
        job = self._extract_job(raw_response)
        parsed_job_id = self._extract_job_id(job, raw_response)
        status = self._extract_status(job, raw_response, required=True)

        markdown = raw_response.get("markdown_full")
        if markdown is None and isinstance(raw_response.get("markdown"), str):
            markdown = raw_response["markdown"]

        return ParseJobResult(
            job_id=parsed_job_id,
            status=status,
            markdown=markdown,
            items=self._as_list_of_dicts(raw_response.get("items")),
            metadata=self._as_dict(raw_response.get("metadata")),
            job_metadata=self._as_dict(raw_response.get("job_metadata")),
            raw_response=raw_response,
        )

    def poll_parse_job(
        self,
        job_id: str,
        expand: Sequence[str] | None = None,
        config: ParseJobPollingConfig | None = None,
    ) -> ParseJobResult:
        polling_config = config or ParseJobPollingConfig()

        for attempt in range(polling_config.max_attempts):
            result = self.get_parse_job(job_id=job_id, expand=expand)

            if result.status == ParseJobStatus.completed:
                return result

            if result.status in {ParseJobStatus.failed, ParseJobStatus.cancelled}:
                raise LlamaParseJobFailedError(f"LlamaParse job {job_id} ended with status {result.status.value}.")

            if attempt < polling_config.max_attempts - 1:
                self._sleep(polling_config.interval_seconds)

        raise LlamaParsePollingTimeoutError(
            f"LlamaParse job {job_id} did not complete after {polling_config.max_attempts} attempts."
        )

    def _url(self, path: str) -> str:
        return f"{self._settings.parse_base_url.rstrip('/')}{path}"

    def _json_headers(self) -> dict[str, str]:
        headers = self._boundary.build_auth_headers()
        headers["Content-Type"] = "application/json"
        return headers

    def _read_json_response(self, response: httpx.Response) -> dict[str, Any]:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise LlamaParseResponseError(str(exc)) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise LlamaParseResponseError("LlamaParse response is not valid JSON.") from exc

        if not isinstance(data, dict):
            raise LlamaParseResponseError("LlamaParse response JSON must be an object.")

        return data

    def _extract_job(self, raw_response: dict[str, Any]) -> dict[str, Any]:
        job = raw_response.get("job")
        if isinstance(job, dict):
            return job
        return raw_response

    def _extract_job_id(self, job: dict[str, Any], raw_response: dict[str, Any]) -> str:
        job_id = job.get("id") or raw_response.get("job_id") or raw_response.get("id")
        if not job_id:
            raise LlamaParseResponseError("LlamaParse response does not contain job id.")
        return str(job_id)

    def _extract_status(
        self,
        job: dict[str, Any],
        raw_response: dict[str, Any],
        required: bool,
    ) -> ParseJobStatus | None:
        raw_status = job.get("status") or raw_response.get("status")
        if raw_status is None:
            if required:
                raise LlamaParseResponseError("LlamaParse response does not contain job status.")
            return None

        try:
            return ParseJobStatus(str(raw_status))
        except ValueError as exc:
            raise LlamaParseResponseError(f"Unknown LlamaParse job status: {raw_status}") from exc

    def _as_dict(self, value: Any) -> dict[str, Any]:
        return value if isinstance(value, dict) else {}

    def _as_list_of_dicts(self, value: Any) -> list[dict[str, Any]]:
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, dict)]