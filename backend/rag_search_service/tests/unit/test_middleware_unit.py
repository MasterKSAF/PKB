"""Unit-тесты для middleware request logging."""

from __future__ import annotations

import logging

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.middleware import add_request_logging_middleware


def _create_app_with_middleware():
    """Создать FastAPI app с middleware и тестовыми эндпоинтами."""
    app = FastAPI()
    add_request_logging_middleware(app)

    @app.get("/test")
    async def test_endpoint():
        return {"ok": True}

    @app.get("/error")
    async def error_endpoint():
        raise ValueError("test error")

    return app


class TestRequestLoggingMiddleware:
    """Тесты middleware логирования HTTP-запросов."""

    def test_logs_request_method_and_path(self, caplog):
        """Middleware логирует method и path на входе."""
        app = _create_app_with_middleware()
        client = TestClient(app)

        with caplog.at_level(logging.INFO):
            client.get("/test")

        log_messages = [r.message for r in caplog.records]
        assert any("--> GET /test" in msg for msg in log_messages)

    def test_logs_response_status_and_elapsed(self, caplog):
        """Middleware логирует status code и время обработки на выходе."""
        app = _create_app_with_middleware()
        client = TestClient(app)

        with caplog.at_level(logging.INFO):
            client.get("/test")

        log_messages = [r.message for r in caplog.records]
        assert any("<-- GET /test | 200 |" in msg for msg in log_messages)

    def test_logs_exception_on_error(self, caplog):
        """Middleware логирует исключение при ошибке."""
        app = _create_app_with_middleware()
        client = TestClient(app)

        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError, match="test error"):
                client.get("/error", follow_redirects=False)

        log_messages = [r.message for r in caplog.records]
        assert any("ERROR" in msg for msg in log_messages)

    def test_logs_post_method(self, caplog):
        """Middleware корректно логирует POST-запросы."""
        app = FastAPI()
        add_request_logging_middleware(app)

        @app.post("/create")
        async def create_endpoint():
            return {"created": True}

        client = TestClient(app)

        with caplog.at_level(logging.INFO):
            client.post("/create")

        log_messages = [r.message for r in caplog.records]
        assert any("--> POST /create" in msg for msg in log_messages)

    def test_elapsed_time_is_positive(self, caplog):
        """Время обработки положительное."""
        app = _create_app_with_middleware()
        client = TestClient(app)

        with caplog.at_level(logging.INFO):
            client.get("/test")

        log_messages = [r.message for r in caplog.records]
        for msg in log_messages:
            if "<-- GET /test | 200 |" in msg:
                parts = msg.split("|")
                if len(parts) >= 3:
                    time_str = parts[2].strip().rstrip("s")
                    assert float(time_str) >= 0
                break
