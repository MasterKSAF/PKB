try:
    import pkg_resources
except ImportError as e:
    print("Import error:", e)
import os
import sys
import logging
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.propagators.b3 import B3MultiFormat
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from pythonjsonlogger import jsonlogger  # <-- ТРЕБОВАНИЕ: JSON-логирование в stdout

def setup_observability(service_name: str, otlp_endpoint: str = None):
    """
    Настройка OpenTelemetry для сервиса:
    - трейсы -> OTLP Span Exporter
    - метрики -> OTLP Metric Exporter
    - логи -> OTLP Log Exporter + JSON-формат в stdout
    """
    if otlp_endpoint is None:
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317")

    resource = Resource.create(attributes={SERVICE_NAME: service_name})

    # Tracing
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True))
    )
    trace.set_tracer_provider(tracer_provider)

    # Metrics
    metric_exporter = OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True)
    metric_reader = PeriodicExportingMetricReader(metric_exporter)
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    # Logs (OTLP)
    logger_provider = LoggerProvider(resource=resource)
    log_exporter = OTLPLogExporter(endpoint=otlp_endpoint, insecure=True)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))

    # OTLP Handler for standard logging
    otlp_handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)

    # Console handler с JSON-форматированием для stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    # JSON-форматтер (rename_fields для соответствия стандартам OTLP)
    json_formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        rename_fields={'levelname': 'severity', 'asctime': 'timestamp'},
        json_ensure_ascii=False
    )
    console_handler.setFormatter(json_formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    log_level = getattr(logging, os.getenv("LOG_LEVEL", "DEBUG").upper(), logging.DEBUG)
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()  # избегаем дублирования логов
    root_logger.addHandler(otlp_handler)
    root_logger.addHandler(console_handler)

    # Propagators for distributed tracing
    set_global_textmap(CompositePropagator([TraceContextTextMapPropagator(), B3MultiFormat()]))

    # HTTPX Instrumentation
    try:
        HTTPXClientInstrumentor().instrument(tracer_provider=tracer_provider)
    except Exception:
        pass  # Игнорируем ошибки инструментирования, если httpx не установлен

    return tracer_provider, meter_provider, root_logger

def instrument_fastapi(app, tracer_provider):
    """Инструментирует FastAPI приложение для сбора трейсов."""
    FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer_provider)
    return app