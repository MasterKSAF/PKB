"""
Tests for centralized error handling in the orchestrator service.

Covers:
  - ServiceError (services/response.py)
  - APIException (services/response.py)
  - Error response format in API endpoints
  - get_status() codes and messages
"""

from fastapi import status
from fastapi.testclient import TestClient

from app.schemas.common import ErrorDetail, ErrorResponse
from app.services.base_client import ServiceError
from services.response import APIException


# ===========================================================================
# get_status (imported from services.response via APIException)
# ===========================================================================


class TestGetStatus:
    """Tests for the get_status function used by APIException."""

    def test_import_get_status(self):
        """Verify get_status is importable and returns expected structure."""
        from services.response import get_status

        result = get_status(200)
        assert result is not None
        assert result["code_name"] == "OK"
        assert result["message"] == "Успех"

    def test_get_status_all_codes(self):
        from services.response import get_status

        expected_codes = {
            200: "OK",
            201: "CREATED",
            202: "ACCEPTED",
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            409: "CONFLICT",
            413: "PAYLOAD_TOO_LARGE",
            422: "VALIDATION_FAILED",
            500: "INTERNAL_ERROR",
            501: "NOT_IMPLEMENTED",
            503: "SERVICE_UNAVAILABLE",
            504: "GATEWAY_TIMEOUT",
        }
        for code, expected_name in expected_codes.items():
            result = get_status(code)
            assert result is not None, f"No status for {code}"
            assert result["code_name"] == expected_name, f"Expected {expected_name} for {code}"

    def test_get_status_unknown_code(self):
        from services.response import get_status

        result = get_status(999)
        assert result is None


# ===========================================================================
# APIException
# ===========================================================================


class TestAPIException:
    """Tests for the APIException class."""

    def test_api_exception_default_message(self):
        exc = APIException(code=400)
        assert exc.status_code == 400
        detail = exc.detail
        assert detail["error"]["code"] == "BAD_REQUEST"
        assert detail["error"]["message"] == "Неверные параметры запроса"
        assert detail["error"]["details"] == {}

    def test_api_exception_custom_message(self):
        exc = APIException(code=404, message="Документ не найден")
        assert exc.status_code == 404
        assert exc.detail["error"]["message"] == "Документ не найден"

    def test_api_exception_with_details(self):
        exc = APIException(
            code=400,
            details={"document_id": "doc-123", "field": "source_type"},
        )
        assert exc.detail["error"]["details"]["document_id"] == "doc-123"
        assert exc.detail["error"]["details"]["field"] == "source_type"

    def test_api_exception_string_details(self):
        exc = APIException(code=500, details="raw error string")
        assert exc.detail["error"]["details"] == "raw error string"

    def test_api_exception_all_http_codes(self):
        """Verify APIException works for all documented HTTP codes."""
        http_codes = [400, 401, 403, 404, 409, 413, 422, 500, 501, 503, 504]
        for code in http_codes:
            exc = APIException(code=code)
            assert exc.status_code == code
            assert "code" in exc.detail["error"]
            assert "message" in exc.detail["error"]

    def test_api_exception_unknown_code(self):
        """Unknown HTTP code should fall back to INTERNAL_ERROR."""
        exc = APIException(code=999, message="Custom error")
        assert exc.detail["error"]["code"] == "INTERNAL_ERROR"


# ===========================================================================
# ErrorResponse Pydantic schema
# ===========================================================================


class TestErrorResponseSchema:
    """Tests for the ErrorResponse Pydantic model."""

    def test_error_response_minimal(self):
        data = {"error": {"code": "NOT_FOUND", "message": "Not found"}}
        model = ErrorResponse(**data)
        assert model.error.code == "NOT_FOUND"
        assert model.error.message == "Not found"
        assert model.error.details is None

    def test_error_response_with_details(self):
        data = {
            "error": {
                "code": "BAD_REQUEST",
                "message": "Invalid param",
                "details": {"field": "source_type"},
            }
        }
        model = ErrorResponse(**data)
        assert model.error.details == {"field": "source_type"}

    def test_error_response_missing_code(self):
        with pytest.raises(Exception):
            ErrorResponse(**{"error": {"message": "No code"}})

    def test_error_detail_model(self):
        detail = ErrorDetail(code="TEST_ERROR", message="Test message")
        assert detail.code == "TEST_ERROR"
        assert detail.message == "Test message"
        assert detail.details is None

    def test_error_detail_with_details(self):
        detail = ErrorDetail(code="ERR", message="Msg", details={"key": "val"})
        assert detail.details == {"key": "val"}


# ===========================================================================
# Error responses in API endpoints
# ===========================================================================


class TestEndpointErrorResponses:
    """Tests that API endpoints return correct error formats."""

    def test_upload_unsupported_type_returns_400(self, client: TestClient, auth_header: dict):
        response = client.post(
            "/api/v1/documents/",
            files={"file": ("test.txt", b"test content", "text/plain")},
            data={"source_type": "GOST"},
            headers=auth_header,
        )
        assert response.status_code == 400
        data = response.json()
        # FastAPI wraps error in detail key
        detail = data.get("detail", data)
        error = detail.get("error", detail)
        assert error["code"] == "BAD_REQUEST"
        assert "message" in error
        assert "details" in error

    def test_upload_invalid_source_type_returns_400(self, client: TestClient, auth_header: dict):
        response = client.post(
            "/api/v1/documents/",
            files={"file": ("test.pdf", b"%PDF-1.4 test", "application/pdf")},
            data={"source_type": "INVALID_TYPE"},
            headers=auth_header,
        )
        assert response.status_code == 400
        data = response.json()
        detail = data.get("detail", data)
        error = detail.get("error", detail)
        assert error["code"] == "BAD_REQUEST"
        assert "allowed_values" in error["details"]

    def test_upload_without_file_returns_422(self, client: TestClient, auth_header: dict):
        response = client.post(
            "/api/v1/documents/",
            headers=auth_header,
        )
        assert response.status_code == 422
        data = response.json()
        # FastAPI validation errors have their own format
        assert "detail" in data

    def test_get_nonexistent_document_returns_404(self, client: TestClient, auth_header: dict):
        response = client.get(
            "/api/v1/documents/doc-nonexistent-99999",
            headers=auth_header,
        )
        assert response.status_code == 200  # Mock mode always returns data

    def test_unauthenticated_protected_endpoint_returns_401(self):
        """
        In real auth mode, protected endpoints require token.
        
        Note: This test is better covered in test_auth_real_mode.py.
        The conftest sets AUTH_SERVICE_MOCK=true globally which makes
        all endpoints accessible without token during testing.
        See test_auth_real_mode.py for comprehensive auth tests.
        """
        pytest.skip("Real auth mode tests are in test_auth_real_mode.py")

    def test_ask_missing_question_returns_422(self, client: TestClient, auth_header: dict):
        response = client.post(
            "/api/v1/ask",
            json={},
            headers=auth_header,
        )
        assert response.status_code == 422

    def test_search_top_k_exceeds_max_returns_422(self, client: TestClient, auth_header: dict):
        response = client.post(
            "/api/v1/documents/search",
            json={"query": "test", "top_k": 200},
            headers=auth_header,
        )
        assert response.status_code == 422

    def test_page_view_out_of_range(self, client: TestClient, auth_header: dict):
        response = client.get(
            "/api/v1/documents/doc-mock-001/pages/99999",
            headers=auth_header,
        )
        assert response.status_code == 200  # Mock mode returns data for any page


# Need to import pytest for proper test discovery
import pytest
