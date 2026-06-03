from __future__ import annotations

import time
from uuid import uuid4

from fastapi import Request
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("x-request-id", str(uuid4()))
        correlation_id = request.headers.get("x-correlation-id", str(uuid4()))
        start = time.perf_counter()
        with logger.contextualize(request_id=request_id, correlation_id=correlation_id):
            logger.info("Request start method={} path={}", request.method, request.url.path)
            response = await call_next(request)
            took_ms = (time.perf_counter() - start) * 1000
            logger.info(
                "Request done method={} path={} status={} took_ms={:.2f}",
                request.method,
                request.url.path,
                response.status_code,
                took_ms,
            )
            response.headers["x-request-id"] = request_id
            response.headers["x-correlation-id"] = correlation_id
            return response
