import json

import httpx
import pytest

from convertor_validator_service_lama.clients.rag_builder_client import (
    RagBuilderRequestError,
    RagBuilderResponseError,
    RagBuilderRestClient,
)
from convertor_validator_service_lama.core.settings import Settings


def _settings() -> Settings:
    return Settings(
        rag_builder_base_url="http://rag-builder.test",
    )


def test_start_rag_build_posts_buildrequest_and_returns_accepted_response() -> None:
    buildrequest_payload = {
        "metadata": {
            "schema": "schema_registry_for_rag_v2",
            "document_id": 420000,
        },
        "document": {
            "id": 420000,
            "pkb_code": "-1",
            "doc_code": "GOST-TEST",
            "title": "Test document",
        },
        "sections": [],
        "terminology": [],
        "protected_spans": [],
        "options": {},
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/v1/rag/build"
        assert request.headers["Content-Type"] == "application/json"

        payload = json.loads(request.content.decode("utf-8"))
        assert payload == buildrequest_payload

        return httpx.Response(
            202,
            json={
                "status": "indexing",
                "document_id": 420000,
                "indexing_txn_id": "5c2d9d45-2e02-44ad-a2d7-806ba5158341",
                "task_id": 26,
            },
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = RagBuilderRestClient(settings=_settings(), http_client=http_client)

    response = client.start_rag_build(buildrequest_payload)

    assert response.status == "indexing"
    assert response.document_id == 420000
    assert response.indexing_txn_id == "5c2d9d45-2e02-44ad-a2d7-806ba5158341"
    assert response.task_id == 26


def test_start_rag_build_raises_request_error_for_structured_upstream_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            409,
            json={
                "detail": {
                    "code": "ALREADY_PROCESSING",
                    "message": "Document indexing is already in progress",
                    "details": {
                        "document_id": 420000,
                        "indexing_txn_id": "active-txn",
                        "status": "indexing",
                    },
                }
            },
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = RagBuilderRestClient(settings=_settings(), http_client=http_client)

    with pytest.raises(RagBuilderRequestError) as exc_info:
        client.start_rag_build({"metadata": {}, "document": {}, "sections": []})

    error = exc_info.value.error

    assert error.status_code == 409
    assert error.code == "ALREADY_PROCESSING"
    assert error.message == "Document indexing is already in progress"
    assert error.details == {
        "document_id": 420000,
        "indexing_txn_id": "active-txn",
        "status": "indexing",
    }


def test_start_rag_build_raises_request_error_for_string_upstream_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            404,
            json={
                "detail": "Indexing job not found",
            },
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = RagBuilderRestClient(settings=_settings(), http_client=http_client)

    with pytest.raises(RagBuilderRequestError) as exc_info:
        client.start_rag_build({"metadata": {}, "document": {}, "sections": []})

    error = exc_info.value.error

    assert error.status_code == 404
    assert error.code == "RAG_BUILDER_ERROR"
    assert error.message == "Indexing job not found"
    assert error.details == {}


def test_start_rag_build_rejects_unexpected_success_status() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "status": "indexing",
                "document_id": 420000,
                "indexing_txn_id": "txn",
            },
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = RagBuilderRestClient(settings=_settings(), http_client=http_client)

    with pytest.raises(RagBuilderResponseError) as exc_info:
        client.start_rag_build({"metadata": {}, "document": {}, "sections": []})

    assert "unexpected status code: 200" in str(exc_info.value)


def test_start_rag_build_rejects_malformed_accepted_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            202,
            json={
                "status": "indexing",
                "document_id": 420000,
            },
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = RagBuilderRestClient(settings=_settings(), http_client=http_client)

    with pytest.raises(RagBuilderResponseError) as exc_info:
        client.start_rag_build({"metadata": {}, "document": {}, "sections": []})

    assert "does not match contract" in str(exc_info.value)
