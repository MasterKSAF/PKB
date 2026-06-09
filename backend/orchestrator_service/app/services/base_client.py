"""
Base Service Client with mock mode support.
"""

from typing import Any, Dict, Optional


class ServiceClient:
    """Base class for microservice HTTP clients with mock mode."""

    def __init__(
        self,
        service_name: str,
        service_url: str,
        mock_mode: bool = False,
    ):
        self.service_name = service_name
        self.service_url = service_url.rstrip("/") if service_url else None
        self.mock_mode = mock_mode

    async def call(
        self,
        method: str,
        endpoint: str,
        mock_response: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Make an HTTP call or return a mock response."""
        if self.mock_mode:
            return await self._generate_mock(method, endpoint, mock_response or {}, **kwargs)
        # In production: make real HTTP request
        return mock_response or {}

    async def close(self):
        """Close the underlying HTTP client (if any)."""
        pass

    async def _generate_mock(
        self, method: str, endpoint: str, default_mock: Dict[str, Any], **kwargs
    ) -> Dict[str, Any]:
        """Override in subclasses to provide custom mock logic."""
        return default_mock
