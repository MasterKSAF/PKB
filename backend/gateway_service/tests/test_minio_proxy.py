"""
Tests for the MinIO proxy module.

  - Unit tests for _s3_presigned_get_url (AWS SigV4 presigned URL).
  - Integration tests for GET /api/v1/files/{file_key:path} via TestClient.

All external calls are mocked — no Docker/network required.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import httpx
import pytest

_GATEWAY_DIR = os.path.join(os.path.dirname(__file__), "..")
if _GATEWAY_DIR not in sys.path:
    sys.path.insert(0, _GATEWAY_DIR)

from gateway.minio_proxy import _s3_presigned_get_url


# ======================================================================
#  Unit: _s3_presigned_get_url
# ======================================================================


class TestS3PresignedGetUrl:
    """Unit tests for _s3_presigned_get_url — AWS SigV4 query-string signing."""

    # Shared default arguments for every call.
    _URL_KWARGS = dict(
        endpoint="http://minio:9000",
        bucket="documents",
        object_key="test.pdf",
        access_key="minioadmin",
        secret_key="minioadmin",
    )

    @patch("gateway.minio_proxy.datetime")
    @patch("gateway.minio_proxy.config")
    def test_presigned_url_starts_with_http(
        self, mock_config, mock_datetime
    ):
        """URL scheme — http://, because config.minio_secure is False."""
        mock_config.minio_secure = False
        fixed_dt = datetime(2026, 7, 1, 10, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = fixed_dt

        url = _s3_presigned_get_url(**self._URL_KWARGS)

        assert url.startswith("http://")

    @patch("gateway.minio_proxy.datetime")
    @patch("gateway.minio_proxy.config")
    def test_presigned_url_contains_bucket_and_key(
        self, mock_config, mock_datetime
    ):
        """The bucket name and object key appear in the canonical URI part."""
        mock_config.minio_secure = False
        fixed_dt = datetime(2026, 7, 1, 10, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = fixed_dt

        url = _s3_presigned_get_url(**self._URL_KWARGS)

        assert "documents" in url
        assert "test.pdf" in url

    @patch("gateway.minio_proxy.datetime")
    @patch("gateway.minio_proxy.config")
    def test_presigned_url_contains_signature(
        self, mock_config, mock_datetime
    ):
        """The X-Amz-Signature query parameter is present."""
        mock_config.minio_secure = False
        fixed_dt = datetime(2026, 7, 1, 10, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = fixed_dt

        url = _s3_presigned_get_url(**self._URL_KWARGS)

        assert "X-Amz-Signature=" in url


# ======================================================================
#  Integration: GET /api/v1/files/{file_key:path}
# ======================================================================


class TestGatewayFileProxy:
    """Integration tests for the MinIO file-proxy endpoint via TestClient.

    These tests patch both:
      - ``gateway.routers.fetch_from_minio`` — so the handler receives a fake
        httpx.Response instead of reaching MinIO.
      - ``gateway.main.is_deprecated_integration_route`` — so the RBAC
        middleware does **not** return 410 (the old Integration Service
        deprecation check); the new MinIO proxy replaces that service.

    *Note*: The ``:path`` converter in ``{file_key:path}`` captures slashes,
    so path-like keys such as ``previews/1/p1.png`` are tested separately.
    """

    @patch("gateway.main.is_deprecated_integration_route")
    @patch("gateway.routers.fetch_from_minio")
    def test_simple_key_returns_200(
        self, mock_fetch, mock_deprecated, client
    ):
        """GET /api/v1/files/test.pdf — returns 200."""
        mock_deprecated.return_value = False
        mock_fetch.return_value = _fake_response(
            status_code=200,
            content=b"%PDF-1.4 fake content",
            content_type="application/pdf",
        )

        resp = client.get("/api/v1/files/test.pdf")

        assert resp.status_code == 200

    @patch("gateway.main.is_deprecated_integration_route")
    @patch("gateway.routers.fetch_from_minio")
    def test_path_like_key_returns_200(
        self, mock_fetch, mock_deprecated, client
    ):
        """GET /api/v1/files/previews/1/p1.png — :path converter handles
        slashes correctly, returns 200."""
        mock_deprecated.return_value = False
        mock_fetch.return_value = _fake_response(
            status_code=200,
            content=b"PNG content",
            content_type="image/png",
        )

        resp = client.get("/api/v1/files/previews/1/p1.png")

        assert resp.status_code == 200

    @patch("gateway.main.is_deprecated_integration_route")
    @patch("gateway.routers.fetch_from_minio")
    def test_content_type_from_minio_is_preserved(
        self, mock_fetch, mock_deprecated, client
    ):
        """The response carries the content-type returned by MinIO."""
        mock_deprecated.return_value = False
        mock_fetch.return_value = _fake_response(
            status_code=200,
            content=b"%PDF-1.4 fake content",
            content_type="application/pdf",
        )

        resp = client.get("/api/v1/files/test.pdf")

        assert resp.headers.get("content-type") == "application/pdf"

    @patch("gateway.main.is_deprecated_integration_route")
    @patch("gateway.routers.fetch_from_minio")
    def test_preview_key_uses_image_bucket(
        self, mock_fetch, mock_deprecated, client
    ):
        """file_key starting with previews/ → bucket=images (image bucket).

        The handler maps ``previews/*`` to ``config.minio_image_bucket``
        (default: ``images``).
        """
        mock_deprecated.return_value = False
        mock_fetch.return_value = _fake_response(
            status_code=200,
            content=b"preview data",
            content_type="image/png",
        )

        resp = client.get("/api/v1/files/previews/1/p1.png")
        assert resp.status_code == 200

        mock_fetch.assert_called_once_with(
            "previews/1/p1.png",
            bucket="images",
        )

    @patch("gateway.main.is_deprecated_integration_route")
    @patch("gateway.routers.fetch_from_minio")
    def test_regular_key_uses_documents_bucket(
        self, mock_fetch, mock_deprecated, client
    ):
        """file_key NOT starting with previews/ → bucket=documents.

        The handler uses ``config.minio_bucket`` for all ordinary keys
        (default: ``documents``).
        """
        mock_deprecated.return_value = False
        mock_fetch.return_value = _fake_response(
            status_code=200,
            content=b"pdf content",
            content_type="application/pdf",
        )

        resp = client.get("/api/v1/files/some/deep/path/doc.pdf")
        assert resp.status_code == 200

        mock_fetch.assert_called_once_with(
            "some/deep/path/doc.pdf",
            bucket="documents",
        )

    @patch("gateway.main.is_deprecated_integration_route")
    @patch("gateway.routers.fetch_from_minio")
    def test_404_when_minio_raises(
        self, mock_fetch, mock_deprecated, client
    ):
        """fetch_from_minio raises an exception → 404 with FILE_NOT_FOUND."""
        mock_deprecated.return_value = False
        mock_fetch.side_effect = Exception("Object not found in MinIO")

        resp = client.get("/api/v1/files/missing.pdf")

        assert resp.status_code == 404
        data = resp.json()
        assert data["error"]["code"] == "FILE_NOT_FOUND"
        assert "missing.pdf" in data["error"]["message"]


# -----------------------------------------------------------------------
#  Helper
# -----------------------------------------------------------------------


def _fake_response(
    status_code: int = 200,
    content: bytes = b"",
    content_type: str = "application/octet-stream",
) -> MagicMock:
    """Build a mocked ``httpx.Response`` suitable for ``fetch_from_minio``.

    The returned ``MagicMock`` supports both synchronous attribute access
    (``.status_code``, ``.headers``) and ``iter_bytes()``, which
    ``StreamingResponse`` will consume.
    """
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.headers = {
        "content-type": content_type,
        "content-disposition": "inline",
        "content-length": str(len(content)),
    }
    resp.iter_bytes.return_value = iter([content])
    return resp
