"""Optional Prometheus metrics endpoint."""

from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST
from prometheus_client import Counter
from prometheus_client import generate_latest
from starlette.responses import Response


INGESTIONS_TOTAL = Counter(
    "ingestions_total",
    "Total number of ingestion runs created",
    ["status"],
)


def metrics_response() -> Response:
    payload = generate_latest()
    return Response(payload, media_type=CONTENT_TYPE_LATEST)

