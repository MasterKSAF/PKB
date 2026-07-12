from __future__ import annotations

from typing import Any

import httpx
from pydantic import ValidationError

from convertor_validator_service_lama.core.settings import Settings
from convertor_validator_service_lama.models.contracts import (
    RagBuilderBuildAcceptedResponse,
    RagBuilderClientError as RagBuilderClientErrorModel,
)
from convertor_validator_service_lama.services.rag_builder_client_contracts import (
    build_rag_builder_client_error,
)


class RagBuilderRestClientError(Exception):
    pass


class RagBuilderResponseError(RagBuilderRestClientError):
    pass


class RagBuilderRequestError(RagBuilderRestClientError):
    def __init__(self, error: RagBuilderClientErrorModel) -> None:
        self.error = error
        super().__init__(f"{error.status_code} {error.code}: {error.message}")


class RagBuilderRestClient:
    def __init__(
        self,
        settings: Settings,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._settings = settings
        self._http_client = http_client or httpx.Client(timeout=30.0)
        self._owns_http_client = http_client is None

    def close(self) -> None:
        if self._owns_http_client:
            self._http_client.close()

    def start_rag_build(
        self,
        buildrequest_payload: dict[str, Any],
    ) -> RagBuilderBuildAcceptedResponse:
        response = self._http_client.post(
            self._url("/api/v1/rag/build"),
            headers={"Content-Type": "application/json"},
            json=buildrequest_payload,
        )

        raw_response = self._read_json_response(response)

        try:
            return RagBuilderBuildAcceptedResponse.model_validate(raw_response)
        except ValidationError as exc:
            raise RagBuilderResponseError(
                "RAG Builder accepted response does not match contract."
            ) from exc

    def _url(self, path: str) -> str:
        return f"{self._settings.rag_builder_base_url.rstrip('/')}{path}"

    def _read_json_response(self, response: httpx.Response) -> dict[str, Any]:
        if response.status_code >= 400:
            raise RagBuilderRequestError(
                build_rag_builder_client_error(
                    status_code=response.status_code,
                    detail=self._extract_error_detail(response),
                )
            )

        if response.status_code != 202:
            raise RagBuilderResponseError(
                f"RAG Builder returned unexpected status code: {response.status_code}."
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise RagBuilderResponseError(
                "RAG Builder response is not valid JSON."
            ) from exc

        if not isinstance(data, dict):
            raise RagBuilderResponseError(
                "RAG Builder response JSON must be an object."
            )

        return data

    def _extract_error_detail(self, response: httpx.Response) -> Any:
        try:
            data = response.json()
        except ValueError:
            return response.text

        if isinstance(data, dict) and "detail" in data:
            return data["detail"]

        return data
