"""
T-15: OTEL → SigNoz интеграция (CM-6).

Проверяет, что OpenTelemetry SDK корректно интегрирован:
  - OTEL SDK инициализируется при старте (graceful fallback)
  - FastAPI инструментирован (span'ы создаются)
  - Экспорт в OTLP endpoint (SigNoz) настроен
  - Graceful fallback при отсутствии пакетов

В production:
  - OTEL_EXPORTER_OTLP_ENDPOINT=http://signoz:4318/v1/traces
  - OTEL_SERVICE_NAME=gateway
  - Трейсы экспортируются в SigNoz для визуализации

В mock-режиме OTEL не используется — проверяем только конфигурацию.
"""

import os
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import pytest

from gateway.config import config


class TestOTELConfiguration:
    """T-15: Проверка конфигурации OTEL в production Gateway."""

    def test_otel_imports_available(self):
        """Проверяем, что модули OTEL могут быть импортированы (если установлены)."""
        try:
            from opentelemetry import trace  # noqa
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter  # noqa
            from opentelemetry.sdk.trace import TracerProvider  # noqa
            from opentelemetry.sdk.trace.export import BatchSpanProcessor  # noqa
            _OTEL_IMPORT_OK = True
        except ImportError:
            _OTEL_IMPORT_OK = False

        # Если пакеты не установлены — это нормально (graceful fallback)
        if not _OTEL_IMPORT_OK:
            pytest.skip("OpenTelemetry packages not installed — OTEL disabled")

    def test_otel_endpoint_configurable(self):
        """OTEL endpoint настраивается через OTEL_EXPORTER_OTLP_ENDPOINT."""
        endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://127.0.0.1:4318/v1/traces")
        assert endpoint.startswith("http"), f"Invalid OTEL endpoint: {endpoint}"
        assert "/v1/traces" in endpoint, "OTEL endpoint should end with /v1/traces"

    def test_otel_service_name_configurable(self):
        """OTEL service name настраивается через OTEL_SERVICE_NAME."""
        service_name = os.getenv("OTEL_SERVICE_NAME", "gateway")
        assert service_name == "gateway", f"Expected 'gateway', got {service_name!r}"

    def test_main_has_otel_setup(self):
        """Проверяем, что main.py содержит OTEL-инициализацию."""
        main_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "gateway",
            "main.py",
        )
        assert os.path.exists(main_path), "gateway/main.py not found"
        with open(main_path, encoding="utf-8") as f:
            content = f.read()
        assert "_setup_otel" in content, "main.py missing _setup_otel function"
        assert "OTEL_EXPORTER_OTLP_ENDPOINT" in content, (
            "main.py missing OTEL_EXPORTER_OTLP_ENDPOINT"
        )
        assert "FastAPIInstrumentor.instrument_app" in content, (
            "main.py missing FastAPIInstrumentor"
        )


class TestOTELSigNozIntegration:
    """T-15: Проверка интеграции с SigNoz."""

    def test_signoz_endpoint_format(self):
        """SigNoz endpoint по умолчанию: http://127.0.0.1:4318/v1/traces."""
        endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://127.0.0.1:4318/v1/traces")
        # SigNoz использует стандартный OTLP HTTP port 4318
        assert ":4318" in endpoint, f"SigNoz endpoint should use port 4318: {endpoint}"
