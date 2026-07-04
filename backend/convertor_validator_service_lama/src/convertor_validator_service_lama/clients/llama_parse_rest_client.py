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

        return ParseJobResult(
            job_id=parsed_job_id,
            status=status,
            markdown=self._extract_markdown(raw_response),
            items=self._extract_items(raw_response),
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

    def _extract_markdown(self, raw_response: dict[str, Any]) -> str | None:
        markdown_full = raw_response.get("markdown_full")
        if isinstance(markdown_full, str):
            return markdown_full

        markdown = raw_response.get("markdown")
        if isinstance(markdown, str):
            return markdown

        page_markdown = self._extract_page_markdown(markdown)
        if page_markdown:
            return page_markdown

        return None

    def _extract_page_markdown(self, markdown: Any) -> str | None:
        if not isinstance(markdown, dict):
            return None

        pages = markdown.get("pages")
        if not isinstance(pages, list):
            return None

        chunks: list[str] = []
        for page in pages:
            if not isinstance(page, dict):
                continue

            page_md = page.get("md") or page.get("markdown")
            if isinstance(page_md, str) and page_md.strip():
                chunks.append(page_md.strip())

        if not chunks:
            return None

        return "\n\n---\n\n".join(chunks)

    def _extract_items(self, raw_response: dict[str, Any]) -> list[dict[str, Any]]:
        raw_items = raw_response.get("items")

        if isinstance(raw_items, list):
            return [item for item in raw_items if isinstance(item, dict)]

        if isinstance(raw_items, dict):
            pages = raw_items.get("pages")
            if isinstance(pages, list):
                return self._extract_items_from_pages(pages)

        return []

    def _extract_items_from_pages(self, pages: list[Any]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []

        for page in pages:
            if not isinstance(page, dict):
                continue

            page_number = page.get("page_number")
            page_width = page.get("page_width")
            page_height = page.get("page_height")
            page_items = page.get("items")

            if not isinstance(page_items, list):
                continue

            for item in page_items:
                if not isinstance(item, dict):
                    continue

                enriched_item = dict(item)
                if page_number is not None and "page_number" not in enriched_item:
                    enriched_item["page_number"] = page_number
                if page_width is not None and "page_width" not in enriched_item:
                    enriched_item["page_width"] = page_width
                if page_height is not None and "page_height" not in enriched_item:
                    enriched_item["page_height"] = page_height

                items.append(enriched_item)

        return items

    def _as_dict(self, value: Any) -> dict[str, Any]:
        return value if isinstance(value, dict) else {}