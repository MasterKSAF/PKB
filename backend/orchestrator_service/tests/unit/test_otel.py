"""
Unit tests for setup_otel graceful degradation (H2).

Verifies that setup_otel handles missing OTEL packages gracefully
— logs a warning, does not crash.
"""

import logging

import pytest
from fastapi import FastAPI


class TestSetupOtel:
    """setup_otel should degrade gracefully when OTEL packages are missing."""

    def test_graceful_degradation_logs_warning_not_crash(self, caplog):
        """setup_otel catches exceptions and logs a warning instead of crashing."""
        import app.core.otel as otel_module

        app = FastAPI()
        caplog.set_level(logging.WARNING)

        # Call the real setup_otel — if OTEL is not installed, it logs gracefully
        # This tests the actual graceful degradation behavior
        try:
            otel_module.setup_otel(app, service_name="test-service")
        except Exception as exc:
            pytest.fail(
                f"setup_otel should not raise, it should log a warning. Got: {exc}"
            )

        # If OTEL packages are not installed, we should see the warning
        if any("Failed to initialize OpenTelemetry" in msg for msg in caplog.messages):
            assert any("Tracing will be disabled" in msg for msg in caplog.messages)
        else:
            # OTEL packages were installed and setup succeeded
            pytest.skip("OTEL packages are installed, graceful degradation not triggered")
