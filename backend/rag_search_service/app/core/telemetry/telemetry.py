"""OpenTelemetry: трейсы, метрики, логи → SigNoz через OTLP."""

from __future__ import annotations

import logging
import os
import sys


def setup_observability(
    service_name: str,
    otlp_endpoint: str | None = None,
) -> tuple:
    """
    Настройка OpenTelemetry для сервиса:
    - трейсы → OTLP Span Exporter
    - метрики → OTLP Metric Exporter
    - логи → OTLP Log Exporter + JSON-формат в stdout
    """
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
    from pythonjsonlogger import jsonlogger

    if otlp_endpoint is None:
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317")

    resource = Resource.create(attributes={SERVICE_NAME: service_name})

    # --- Tracing ---
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True))
    )
    trace.set_tracer_provider(tracer_provider)

    # --- Metrics ---
    metric_exporter = OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True)
    metric_reader = PeriodicExportingMetricReader(metric_exporter)
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    # --- Logs (OTLP) ---
    logger_provider = LoggerProvider(resource=resource)
    log_exporter = OTLPLogExporter(endpoint=otlp_endpoint, insecure=True)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))

    otlp_handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)

    # --- Console handler: JSON в stdout ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    json_formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        rename_fields={"levelname": "severity", "asctime": "timestamp"},
        json_ensure_ascii=False,
    )
    console_handler.setFormatter(json_formatter)

    # --- Root logger ---
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.handlers.clear()
    root_logger.addHandler(otlp_handler)
    root_logger.addHandler(console_handler)

    # --- Propagators for distributed tracing ---
    set_global_textmap(
        CompositePropagator([TraceContextTextMapPropagator(), B3MultiFormat()])
    )

    # --- HTTPX Instrumentation ---
    try:
        HTTPXClientInstrumentor().instrument(tracer_provider=tracer_provider)
    except Exception:
        pass

    return tracer_provider, meter_provider, root_logger


def instrument_fastapi(app, tracer_provider=None):
    """Инструментирует FastAPI приложение для сбора трейсов."""
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry import trace

    if tracer_provider is None:
        tracer_provider = trace.get_tracer_provider()

    FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer_provider)
    return app
