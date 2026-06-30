"""
Base Service Client with mock mode support and real HTTP client.

All external service clients inherit from this class.
Supports dual mode: mock responses for development/testing,
or real HTTP calls to the actual microservice.

HTTP client uses httpx with configurable timeouts, retry (tenacity),
and circuit breaker for resilience.
"""

import json
import logging
import time
from typing import Any, Dict, Optional, Type

import httpx
from pydantic import BaseModel, ValidationError
from circuitbreaker import CircuitBreaker, CircuitBreakerError
from tenacity import (
    retry,
    retry_if_exception,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.core.trace import build_correlation_headers

logger = logging.getLogger("services.base_client")


class ServiceClient:
    """Base class for microservice HTTP clients with mock mode support.

    In mock mode: returns predefined responses without network calls.
    In real mode: makes asynchronous HTTP requests via httpx with:
      - Configurable timeouts
      - Retry with exponential backoff (tenacity) on transient errors
      - Circuit breaker that opens after N failures
    """

    def __init__(
        self,
        service_name: str,
        service_url: Optional[str],
        mock_mode: bool = False,
        read_timeout: Optional[int] = None,
    ):
        self.service_name = service_name
        self.service_url = service_url.rstrip("/") if service_url else None
        self.mock_mode = mock_mode
        self._http_client: Optional[httpx.AsyncClient] = None
        self._circuit_breaker: Optional[CircuitBreaker] = None
        self._read_timeout = read_timeout

        if not mock_mode and self.service_url:
            # Initialize real HTTP client with timeouts from config
            http_cfg = settings.http_client
            rt = read_timeout if read_timeout is not None else http_cfg.READ_TIMEOUT
            timeout = httpx.Timeout(
                connect=http_cfg.CONNECT_TIMEOUT,
                read=rt,
                write=rt,
                pool=http_cfg.POOL_TIMEOUT,
            )
            limits = httpx.Limits(
                max_connections=http_cfg.POOL_CONNECTIONS,
                max_keepalive_connections=http_cfg.POOL_MAX_SIZE,
            )
            self._http_client = httpx.AsyncClient(
                base_url=self.service_url,
                timeout=timeout,
                limits=limits,
            )

            # Initialize circuit breaker from pipeline config
            pipeline_cfg = settings.pipeline
            self._circuit_breaker = CircuitBreaker(
                failure_threshold=pipeline_cfg.CIRCUIT_FAILURE_THRESHOLD,
                recovery_timeout=pipeline_cfg.CIRCUIT_RECOVERY_TIMEOUT,
                name=f"cb_{service_name}",
            )

            logger.info(
                "HTTP client initialized with retry + circuit breaker",
                extra={
                    "service": service_name,
                    "url": service_url,
                    "timeout": rt,
                    "max_retries": http_cfg.MAX_RETRIES,
                    "cb_threshold": pipeline_cfg.CIRCUIT_FAILURE_THRESHOLD,
                    "cb_timeout": pipeline_cfg.CIRCUIT_RECOVERY_TIMEOUT,
                },
            )

    async def call(
        self,
        method: str,
        endpoint: str,
        mock_response: Optional[Dict[str, Any]] = None,
        request_model: Optional[Type[BaseModel]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Make an API call (mock or real HTTP).

        In mock mode: delegates to ``_generate_mock``.
        In real mode: performs an actual HTTP request via httpx with
        retry (tenacity) and circuit breaker protection.

        Parameters
        ----------
        request_model : optional
            If provided, validates ``json`` kwargs through this Pydantic model
            before sending (catches type mismatches early in both mock and real mode).
        """
        # --- Validate json body through Pydantic if request_model provided ---
        if request_model is not None and "json" in kwargs:
            try:
                kwargs["json"] = request_model.model_validate(
                    kwargs["json"]
                ).model_dump(exclude_none=True)
            except ValidationError as exc:
                raise TypeError(
                    f"Request body for {method} {endpoint} failed "
                    f"Pydantic validation: {exc}"
                ) from exc

        # --- Guard: ensure json body is JSON-serializable ---
        if "json" in kwargs:
            try:
                json.dumps(kwargs["json"], ensure_ascii=False)
            except TypeError as exc:
                raise TypeError(
                    f"Request body for {method} {endpoint} contains "
                    f"non-serializable value: {exc}"
                ) from exc

        start_time = time.monotonic()

        if self.mock_mode:
            result = await self._generate_mock(
                method, endpoint, mock_response or {}, **kwargs
            )
            elapsed = time.monotonic() - start_time
            logger.debug(
                f"Mock call: {method} {endpoint} -> {elapsed:.3f}s",
                extra={
                    "service": self.service_name,
                    "method": method,
                    "endpoint": endpoint,
                    "mock": True,
                    "duration_ms": round(elapsed * 1000),
                },
            )
            return result

        # Real HTTP call with circuit breaker
        url = f"{self.service_url}{endpoint}" if self.service_url else endpoint
        try:
            if self._circuit_breaker:
                # Use circuit breaker
                response = await self._call_with_circuit_breaker(method, url, **kwargs)
            else:
                # No circuit breaker configured
                response = await self._retry_request(method, url, **kwargs)

            elapsed = time.monotonic() - start_time
            data: Dict[str, Any] = response.json()

            logger.info(
                f"HTTP {method} {endpoint} -> {response.status_code} ({elapsed:.3f}s)",
                extra={
                    "service": self.service_name,
                    "method": method,
                    "endpoint": endpoint,
                    "status": response.status_code,
                    "duration_ms": round(elapsed * 1000),
                },
            )
            return data

        except CircuitBreakerError:
            elapsed = time.monotonic() - start_time
            logger.error(
                f"Circuit breaker OPEN for {self.service_name}, "
                f"request blocked ({elapsed:.1f}s)",
                extra={
                    "service": self.service_name,
                    "method": method,
                    "endpoint": endpoint,
                    "duration_ms": round(elapsed * 1000),
                    "circuit_breaker": "open",
                },
            )
            # Graceful fallback: return mock_response instead of crashing
            fallback = mock_response if mock_response is not None else {}
            logger.info(
                f"Falling back to mock_response={fallback} for {method} {endpoint} "
                f"(circuit breaker open)",
                extra={
                    "service": self.service_name,
                    "method": method,
                    "endpoint": endpoint,
                },
            )
            return fallback

        except httpx.TimeoutException as exc:
            elapsed = time.monotonic() - start_time
            logger.error(
                f"HTTP timeout: {method} {endpoint} after {elapsed:.1f}s "
                f"(retries exhausted)",
                extra={
                    "service": self.service_name,
                    "method": method,
                    "endpoint": endpoint,
                    "duration_ms": round(elapsed * 1000),
                    "error": str(exc),
                },
            )
            raise

        except httpx.ConnectError as exc:
            elapsed = time.monotonic() - start_time
            logger.error(
                f"HTTP connection error after retries: {method} {endpoint} ({exc})",
                extra={
                    "service": self.service_name,
                    "method": method,
                    "endpoint": endpoint,
                    "duration_ms": round(elapsed * 1000),
                    "error": str(exc),
                },
            )
            # If a mock_response fallback was provided (or we can use {}),
            # return it instead of crashing. This supports graceful
            # degradation when a downstream service is unreachable.
            fallback = mock_response if mock_response is not None else {}
            logger.info(
                f"Falling back to mock_response={fallback} for {method} {endpoint}",
                extra={
                    "service": self.service_name,
                    "method": method,
                    "endpoint": endpoint,
                },
            )
            return fallback

        except httpx.HTTPStatusError as exc:
            elapsed = time.monotonic() - start_time
            logger.error(
                f"HTTP error: {method} {endpoint} -> {exc.response.status_code} "
                f"({elapsed:.3f}s, retries exhausted)",
                extra={
                    "service": self.service_name,
                    "method": method,
                    "endpoint": endpoint,
                    "status": exc.response.status_code,
                    "response_body": exc.response.text[:500],
                    "duration_ms": round(elapsed * 1000),
                },
            )
            raise

        except Exception as exc:
            elapsed = time.monotonic() - start_time
            logger.error(
                f"Unexpected error calling {method} {endpoint}: {exc}",
                extra={
                    "service": self.service_name,
                    "method": method,
                    "endpoint": endpoint,
                    "duration_ms": round(elapsed * 1000),
                    "error_type": type(exc).__name__,
                },
            )
            raise

    async def _call_with_circuit_breaker(
        self, method: str, url: str, **kwargs
    ) -> httpx.Response:
        """Execute request through circuit breaker.

        If circuit is OPEN, raises CircuitBreakerError immediately.
        If circuit is CLOSED/HALF-OPEN, attempts the request;
        on failure, the circuit breaker tracks the error.
        """
        cb = self._circuit_breaker
        assert cb is not None

        # CircuitBreaker.call_async executes the coroutine and tracks failures
        return await cb.call_async(self._retry_request, method, url, **kwargs)

    async def _retry_request(
        self, method: str, url: str, **kwargs
    ) -> httpx.Response:
        """Execute HTTP request with tenacity retry logic.

        Retries on TimeoutException and 5xx HTTP errors.
        Does NOT retry on ConnectError (connection refused/DNS failure)
        or 4xx client errors.
        """
        http_cfg = settings.http_client
        # Apply retry manually in the wrapper because tenacity's
        # async retry can interfere with the circuit breaker.
        return await self._request_with_retry(
            method, url, http_cfg.MAX_RETRIES, **kwargs
        )

    def _build_correlation_headers(self) -> dict:
        """Build correlation headers from current trace context (CM-5).

        Injects X-Trace-ID, X-Request-ID, X-User-ID, X-Draft-ID,
        X-Document-ID, X-Version-ID into every downstream request
        for end-to-end tracing across services.
        """
        return build_correlation_headers()

    async def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Execute the actual HTTP request (no retry — use _request_with_retry).

        Injects correlation headers from trace context for distributed tracing.
        Does NOT retry on any error — retry logic is in _request_with_retry.
        Must raise_for_status here so that tenacity can catch HTTPStatusError.
        """
        if self._http_client is None:
            raise RuntimeError(
                f"HTTP client not initialized for {self.service_name}. "
                f"Service URL may be missing."
            )
        # Inject correlation headers into every downstream call
        headers = kwargs.pop("headers", {})
        headers.update(self._build_correlation_headers())
        kwargs["headers"] = headers
        response = await self._http_client.request(method, url, **kwargs)
        # Raise on HTTP errors so tenacity can catch them for retry
        response.raise_for_status()
        return response

    async def _request_with_retry(
        self, method: str, url: str, max_retries: int, **kwargs
    ) -> httpx.Response:
        """Wrapper that dynamically sets tenacity stop condition."""
        # Dynamically apply retry by re-creating the decorator
        # with the configured max_retries count.
        retry_decorator = retry(
            stop=stop_after_attempt(max_retries + 1),  # +1 for initial attempt
            wait=wait_exponential(
                multiplier=settings.http_client.RETRY_BACKOFF_FACTOR,
                min=1,
                max=60,
            ),
            retry=(
                retry_if_exception_type(httpx.TimeoutException)
                | retry_if_exception(_is_retryable_http_error)
            ),
            reraise=True,
        )
        decorated = retry_decorator(self._request)
        return await decorated(method, url, **kwargs)

    async def close(self):
        """Close the underlying HTTP client."""
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None
            logger.debug(
                "HTTP client closed",
                extra={"service": self.service_name},
            )

    async def _generate_mock(
        self, method: str, endpoint: str, default_mock: Dict[str, Any], **kwargs
    ) -> Dict[str, Any]:
        """Override in subclasses to provide custom mock logic."""
        return default_mock


def _is_retryable_http_error(exc: BaseException) -> bool:
    """Check if an HTTP error is retryable.

    Retry on:
    - Server errors (5xx) — transient
    - TimeoutException — network may recover

    Do NOT retry on:
    - Client errors (4xx) — request is bad
    """
    if isinstance(exc, httpx.TimeoutException):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return 500 <= exc.response.status_code < 600
    return False
