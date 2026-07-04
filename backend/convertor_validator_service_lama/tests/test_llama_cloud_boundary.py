import pytest

from convertor_validator_service_lama.clients.llama_cloud_boundary import (
    LlamaCloudBoundary,
    MissingLlamaCloudApiKeyError,
)
from convertor_validator_service_lama.core.settings import Settings


def test_llama_cloud_boundary_requires_api_key() -> None:
    boundary = LlamaCloudBoundary(Settings(cloud_api_key=None))

    with pytest.raises(MissingLlamaCloudApiKeyError):
        boundary.build_auth_headers()


def test_llama_cloud_boundary_builds_auth_headers() -> None:
    boundary = LlamaCloudBoundary(Settings(cloud_api_key="test-key"))

    headers = boundary.build_auth_headers()

    assert headers == {
        "Authorization": "Bearer test-key",
        "Accept": "application/json",
    }


def test_llama_cloud_boundary_builds_request_preview_without_network_call() -> None:
    boundary = LlamaCloudBoundary(Settings(cloud_api_key="test-key"))

    preview = boundary.build_request_preview(
        method="POST",
        url="https://api.cloud.llamaindex.ai/api/parsing/upload",
        json_payload={"result_format": "markdown"},
    )

    assert preview.method == "POST"
    assert preview.url == "https://api.cloud.llamaindex.ai/api/parsing/upload"
    assert preview.has_authorization_header is True
    assert preview.json_payload == {"result_format": "markdown"}