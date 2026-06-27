"""Optional OpenTelemetry observability for RAG services."""

from __future__ import annotations

import logging
import os
import sys
from typing import Any

_MASKED_FIELDS = frozenset(
    {
        "password",
        "access_token",
        "refresh_token",
        "secret",
        "token",
        "api_key",
        "authorization",
        "password_hash",
    }
)


class _TraceAndMaskingFilter(logging.Filter):
    """Adds trace/span ids and masks sensitive log fields."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = "no-trace"
        record.span_id = "no-span"

        try:
            from opentelemetry import trace

            span = trace.get_current_span()
            ctx = span.get_span_context()
            if ctx.is_valid:
                record.trace_id = format(ctx.trace_id, "032x")
                record.span_id = format(ctx.span_id, "016x")
        except Exception:
            pass

        for field in _MASKED_FIELDS:
            if hasattr(record, field):
                setattr(record, field, "***")

        if isinstance(record.msg, str):
            lowered = record.msg.lower()
            if any(field in lowered for field in _MASKED_FIELDS):
                record.msg = "[MASKED LOG: contains sensitive field]"
                record.args = ()

        return True


def _resolve_log_level(value: str | None) -> int:
    name = (value or "INFO").upper()
    return getattr(logging, name, logging.INFO)


def _configure_json_logging(log_level: str | None) -> logging.Logger:
    from pythonjsonlogger import jsonlogger

    trace_filter = _TraceAndMaskingFilter()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.addFilter(trace_filter)

    json_formatter = jsonlogger.JsonFormatter(
        fmt=(
            "%(asctime)s %(levelname)s %(name)s %(message)s "
            "%(pathname)s %(lineno)d %(trace_id)s %(span_id)s"
        ),
        rename_fields={
            "asctime": "timestamp",
            "levelname": "severity",
        },
        json_ensure_ascii=False,
    )
    console_handler.setFormatter(json_formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(_resolve_log_level(log_level))
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)

    return root_logger


def setup_observability(
    service_name: str,
    otlp_endpoint: str | None = None,
    enabled: bool = False,
    log_level: str | None = None,
) -> tuple[Any | None, Any | None, logging.Logger]:
    """Configure JSON logs and, when enabled, OTLP traces/logs/metrics."""

    if not enabled:
        return None, None, logging.getLogger()

    from opentelemetry import metrics, trace
    from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.propagate import set_global_textmap
    from opentelemetry.propagators.b3 import B3MultiFormat
    from opentelemetry.propagators.composite import CompositePropagator
    from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

    endpoint = otlp_endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317")

    resource = Resource.create(attributes={SERVICE_NAME: service_name})

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(endpoint=endpoint, insecure=True, timeout=5)
        )
    )
    trace.set_tracer_provider(tracer_provider)

    metric_exporter = OTLPMetricExporter(endpoint=endpoint, insecure=True, timeout=5)
    metric_reader = PeriodicExportingMetricReader(metric_exporter)
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    logger_provider = LoggerProvider(resource=resource)
    log_exporter = OTLPLogExporter(endpoint=endpoint, insecure=True, timeout=5)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))

    root_logger = _configure_json_logging(log_level)

    trace_filter = _TraceAndMaskingFilter()
    otlp_handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
    otlp_handler.addFilter(trace_filter)
    root_logger.addHandler(otlp_handler)

    set_global_textmap(
        CompositePropagator([TraceContextTextMapPropagator(), B3MultiFormat()])
    )

    try:
        HTTPXClientInstrumentor().instrument(tracer_provider=tracer_provider)
    except Exception:
        pass

    return tracer_provider, meter_provider, root_logger


def instrument_fastapi(app: Any, tracer_provider: Any | None = None) -> Any:
    """Instrument FastAPI app when observability is enabled."""

    if tracer_provider is None:
        return app

    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=tracer_provider,
        excluded_urls="health,ready",
    )
    return app
