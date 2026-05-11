"""
Base HTTP client for external services with dual mode support.
Supports both real API calls and mock/stub mode.
"""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import httpx

from app.core.config import ServiceConfig, settings


class ServiceClient(ABC):
    """Base client for external services with mock mode support."""

    def __init__(
        self,
        service_name: str,
        service_url: Optional[str] = None,
        mock_mode: bool = True,
    ):
        self.service_name = service_name
        self.service_url = service_url
        self.mock_mode = mock_mode
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                base_url=self.service_url or "",
                timeout=30.0,
                headers={"Content-Type": "application/json"},
            )
        return self._http_client

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Make HTTP request to real service."""
        client = await self._get_client()
        url = f"{self.service_url}{endpoint}"

        try:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise ServiceError(
                f"HTTP error from {self.service_name}: {e.response.status_code}",
                status_code=e.response.status_code,
                details=e.response.text,
            )
        except httpx.RequestError as e:
            raise ServiceError(
                f"Request error to {self.service_name}: {str(e)}",
                status_code=503,
                details=str(e),
            )

    async def call(
        self,
        method: str,
        endpoint: str,
        mock_response: Dict[str, Any],
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Make API call with automatic mock mode support.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            mock_response: Response to return in mock mode
            **kwargs: Additional arguments for HTTP request

        Returns:
            API response (real or mocked)
        """
        if self.mock_mode or not self.service_url:
            return await self._get_mock_response(
                method, endpoint, mock_response, **kwargs
            )

        return await self._make_request(method, endpoint, **kwargs)

    async def _get_mock_response(
        self,
        method: str,
        endpoint: str,
        default_mock: Dict[str, Any],
        **kwargs,
    ) -> Dict[str, Any]:
        """Generate mock response. Override in subclasses for custom mock logic."""
        mock_data = await self._generate_mock(method, endpoint, default_mock, **kwargs)
        return mock_data

    @abstractmethod
    async def _generate_mock(
        self,
        method: str,
        endpoint: str,
        default_mock: Dict[str, Any],
        **kwargs,
    ) -> Dict[str, Any]:
        """Generate mock response. Must be implemented by subclasses."""
        pass

    async def close(self):
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None


class ServiceError(Exception):
    """Service error exception."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[str] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": {
                "code": self._get_code_name(),
                "message": self.message,
                "details": {"service_error": self.details} if self.details else {},
            }
        }

    def _get_code_name(self) -> str:
        """Get error code name based on status code."""
        code_names = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            409: "CONFLICT",
            422: "VALIDATION_FAILED",
            500: "INTERNAL_ERROR",
            503: "SERVICE_UNAVAILABLE",
        }
        return code_names.get(self.status_code, "INTERNAL_ERROR")
