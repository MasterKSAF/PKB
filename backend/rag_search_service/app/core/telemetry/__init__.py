"""OpenTelemetry telemetry setup для RAG Search Service."""

from __future__ import annotations


def setup_observability(service_name, otlp_endpoint=None):
    """Lazy import to avoid ImportError when OTEL packages are not installed."""
    from app.core.telemetry.telemetry import setup_observability as _setup
    return _setup(service_name, otlp_endpoint)


def instrument_fastapi(app, tracer_provider=None):
    """Lazy import to avoid ImportError when OTEL packages are not installed."""
    from app.core.telemetry.telemetry import instrument_fastapi as _instrument
    return _instrument(app, tracer_provider)
