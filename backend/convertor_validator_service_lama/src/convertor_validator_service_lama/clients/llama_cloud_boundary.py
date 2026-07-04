from dataclasses import dataclass
from typing import Any

from convertor_validator_service_lama.core.settings import Settings


class LlamaCloudBoundaryError(Exception):
    pass


class MissingLlamaCloudApiKeyError(LlamaCloudBoundaryError):
    pass


@dataclass(frozen=True)
class LlamaCloudRequestPreview:
    method: str
    url: str
    has_authorization_header: bool
    json_payload: dict[str, Any] | None = None


class LlamaCloudBoundary:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def build_auth_headers(self) -> dict[str, str]:
        if not self._settings.cloud_api_key:
            raise MissingLlamaCloudApiKeyError("LAMA_CLOUD_API_KEY is required for LlamaCloud network calls.")

        return {
            "Authorization": f"Bearer {self._settings.cloud_api_key}",
            "Accept": "application/json",
        }

    def build_request_preview(
        self,
        method: str,
        url: str,
        json_payload: dict[str, Any] | None = None,
    ) -> LlamaCloudRequestPreview:
        headers = self.build_auth_headers()

        return LlamaCloudRequestPreview(
            method=method,
            url=url,
            has_authorization_header="Authorization" in headers,
            json_payload=json_payload,
        )