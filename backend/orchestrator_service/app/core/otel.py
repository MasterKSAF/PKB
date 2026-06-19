"""
OpenTelemetry initialization for Orchestrator Service.

Configures tracing with OTLP export to SigNoz.
FastAPI and httpx are auto-instrumented.
All imports are lazy so tests don't need OTEL packages installed.
"""

import logging

from fastapi import FastAPI

logger = logging.getLogger("orchestrator.otel")


def setup_otel(app: FastAPI, service_name: str = "orchestrator-service") -> None:
    """Initialize OpenTelemetry tracing with OTLP export.

    Lazy imports — if OTEL packages are not installed, logs a warning
    and continues without tracing (graceful degradation).
    """
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create(
            attributes={
                "service.name": service_name,
                "service.version": "1.0.0",
                "deployment.environment": "production",
            }
        )

        provider = TracerProvider(resource=resource)

        # OTLP exporter to SigNoz
        exporter = OTLPSpanExporter()
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)

        trace.set_tracer_provider(provider)

        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)

        # Instrument httpx client for downstream tracing
        HTTPXClientInstrumentor().instrument()

        logger.info(
            "OpenTelemetry initialized",
            extra={"service": service_name},
        )

    except Exception as exc:
        logger.warning(
            f"Failed to initialize OpenTelemetry: {exc}. "
            "Tracing will be disabled.",
        )
