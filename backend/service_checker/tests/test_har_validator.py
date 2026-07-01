"""
Tests for core/har_validator.py — HAR vs OpenAPI validation.
"""

from __future__ import annotations

import json
import pytest
from pathlib import Path
from typing import Any, Dict

from service_checker.core.har_validator import (
    HarValidator,
    HarValidationReport,
    HarValidationResult,
    HarValidationError,
    format_har_report,
    _parse_har_entry,
)
from service_checker.core.openapi_loader import OpenApiEndpoint


# ── Helpers ──────────────────────────────────────────────────────────

def _make_endpoint(
    method: str = "GET",
    path: str = "/health",
    parameters: list | None = None,
    request_body: dict | None = None,
    responses: dict | None = None,
) -> OpenApiEndpoint:
    """Создать OpenApiEndpoint с заданными параметрами."""
    ep = OpenApiEndpoint(method=method, path=path)
    if parameters:
        ep.parameters = parameters
    if request_body:
        ep.request_body = request_body
    if responses:
        ep.responses = responses
    # Вычисляем flat_fields из responses
    if ep.responses:
        from service_checker.core.openapi_loader import OpenApiLoader
        stub = OpenApiLoader("http://stub")
        for sc, schema in ep.responses.items():
            ep.flat_fields = stub._flatten_schema(schema)
            break
    return ep


class TestParseHarEntry:
    """Тесты парсинга HAR entry."""

    def test_parse_get_request(self):
        """GET запрос без тела."""
        raw = {
            "request": {
                "method": "GET",
                "url": "http://localhost:18080/health",
                "headers": [],
            },
            "response": {
                "status": 200,
                "content": {
                    "mimeType": "application/json",
                    "text": '{"status": "ok"}',
                },
            },
        }
        entry = _parse_har_entry(raw)
        assert entry is not None
        assert entry["method"] == "GET"
        assert entry["path"] == "/health"
        assert entry["response_status"] == 200
        assert entry["response_body"] == {"status": "ok"}

    def test_parse_post_request(self):
        """POST запрос с JSON телом."""
        raw = {
            "request": {
                "method": "POST",
                "url": "http://localhost:18084/api/v1/registry/classifiers",
                "headers": [{"name": "Content-Type", "value": "application/json"}],
                "postData": {
                    "mimeType": "application/json",
                    "text": '{"name": "test", "description": "test"}',
                },
            },
            "response": {
                "status": 200,
                "content": {
                    "mimeType": "application/json",
                    "text": '{"id": 1, "name": "test"}',
                },
            },
        }
        entry = _parse_har_entry(raw)
        assert entry is not None
        assert entry["request_body"] == {"name": "test", "description": "test"}
        assert entry["response_body"] == {"id": 1, "name": "test"}

    def test_parse_with_query_string(self):
        """GET запрос с query параметрами."""
        raw = {
            "request": {
                "method": "GET",
                "url": "http://localhost:18082/api/v1/auth/users?skip=0&limit=10",
                "headers": [],
            },
            "response": {
                "status": 200,
                "content": {"mimeType": "application/json", "text": '[]'},
            },
        }
        entry = _parse_har_entry(raw)
        assert entry is not None
        assert entry["query_string"] == "skip=0&limit=10"

    def test_parse_non_json_response(self):
        """Ответ не в JSON формате."""
        raw = {
            "request": {
                "method": "GET",
                "url": "http://localhost:18080/health",
            },
            "response": {
                "status": 200,
                "content": {
                    "mimeType": "text/plain",
                    "text": "OK",
                },
            },
        }
        entry = _parse_har_entry(raw)
        assert entry is not None
        assert entry["response_body"] == "OK"

    def test_parse_malformed_entry(self):
        """Плохо сформированная запись — должен вернуть None."""
        raw = {"not": "a proper entry"}
        entry = _parse_har_entry(raw)
        assert entry is None


class TestHarValidatorLoadOpenApi:
    """Тесты загрузки OpenAPI схемы."""

    @pytest.mark.asyncio
    async def test_validate_without_loading(self):
        """Валидация без загрузки OpenAPI должна вернуть ошибку."""
        validator = HarValidator("http://test:18080")
        report = validator.validate_har("nonexistent.har")
        assert "не загружена" in " ".join(report.errors).lower()


class TestHarValidatorValidation:
    """Тесты валидации записей против OpenAPI схемы."""

    def _make_validator(self) -> HarValidator:
        """Создать валидатор с предзаполненной OpenAPI схемой."""
        validator = HarValidator("http://test:18080")
        validator._loaded = True
        validator._loader = _make_stub_loader()
        return validator

    def test_valid_get_request(self):
        """GET запрос, который полностью соответствует OpenAPI."""
        validator = self._make_validator()
        report = validator.validate_entries([
            {
                "method": "GET",
                "path": "/health",
                "response_status": 200,
                "response_body": {"status": "ok"},
            }
        ])
        assert report.passed == 1
        assert report.failed == 0

    def test_valid_post_request(self):
        """POST запрос, соответствующий OpenAPI."""
        validator = self._make_validator()
        report = validator.validate_entries([
            {
                "method": "POST",
                "path": "/api/v1/registry/classifiers",
                "request_body": {"name": "test", "description": "desc"},
                "response_status": 200,
                "response_body": {"id": 1, "name": "test", "description": "desc"},
            }
        ])
        assert report.passed == 1, f"Expected passed=1, got {report}"
        assert report.failed == 0

    def test_status_code_not_in_openapi(self):
        """Status code, отсутствующий в OpenAPI."""
        validator = self._make_validator()
        report = validator.validate_entries([
            {
                "method": "GET",
                "path": "/health",
                "response_status": 418,  # I'm a teapot — не описано
                "response_body": {},
            }
        ])
        assert report.failed == 1
        assert any(e.category == "status_code" for e in report.results[0].errors)

    def test_missing_endpoint(self):
        """Endpoint, отсутствующий в OpenAPI."""
        validator = self._make_validator()
        report = validator.validate_entries([
            {
                "method": "PATCH",
                "path": "/nonexistent",
                "response_status": 200,
            }
        ])
        assert report.skipped == 1
        assert report.results[0].skipped
        assert any(e.category == "missing_endpoint" for e in report.results[0].errors)

    def test_extra_query_param(self):
        """Query параметр, отсутствующий в OpenAPI."""
        validator = self._make_validator()
        report = validator.validate_entries([
            {
                "method": "GET",
                "path": "/api/v1/auth/users",
                "query_string": "skip=0&limit=10&unknown=true",
                "response_status": 200,
                "response_body": {"users": [], "total": 0},
            }
        ])
        assert report.failed == 1
        assert any(e.category == "query_param" for e in report.results[0].errors)

    def test_path_parameter_matching(self):
        """Path с параметром {id} должен совпадать."""
        validator = self._make_validator()
        report = validator.validate_entries([
            {
                "method": "GET",
                "path": "/api/v1/registry/classifiers/42",
                "response_status": 200,
                "response_body": {"id": 42, "name": "test"},
            }
        ])
        assert report.passed == 1, f"Expected passed=1, got {report}"
        # Проверяем, что matched_endpoint содержит шаблон с параметром
        assert report.results[0].matched_endpoint is not None
        assert "{classifier_id}" in report.results[0].matched_endpoint

    def test_unknown_path_returns_skipped(self):
        """Неизвестный path должен вернуть skipped."""
        validator = self._make_validator()
        report = validator.validate_entries([
            {
                "method": "GET",
                "path": "/some/completely/unknown/path",
                "response_status": 200,
            }
        ])
        assert report.skipped == 1

    def test_404_status_ok_in_openapi(self):
        """Status 404, который описан в OpenAPI (например, DELETE несуществующего)."""
        validator = self._make_validator()
        report = validator.validate_entries([
            {
                "method": "DELETE",
                "path": "/api/v1/registry/classifiers/999",
                "response_status": 404,
                "response_body": {"detail": "Not found"},
            }
        ])
        assert report.passed == 1, f"Expected passed=1, got failed={report.failed}: {report}"

    def test_multiple_entries_mixed_results(self):
        """Смешанные результаты: один passed, один failed."""
        validator = self._make_validator()
        report = validator.validate_entries([
            {
                "method": "GET",
                "path": "/health",
                "response_status": 200,
                "response_body": {"status": "ok"},
            },
            {
                "method": "GET",
                "path": "/health",
                "response_status": 503,  # не описано
                "response_body": {},
            },
        ])
        assert report.passed == 1
        assert report.failed == 1
        assert report.total_entries == 2


class TestHarValidatorLoadHar:
    """Тесты загрузки HAR из файла."""

    def test_load_sample_har(self):
        """Загрузка sample_har.json должна распарсить все entry."""
        fixture_path = Path(__file__).resolve().parent / "fixtures" / "sample_har.json"
        assert fixture_path.exists(), f"Fixture not found: {fixture_path}"

        har_data = HarValidator._load_har(str(fixture_path))
        entries = HarValidator._extract_entries(har_data)
        assert len(entries) == 5, f"Expected 5 entries, got {len(entries)}"

    def test_validate_sample_har(self):
        """Валидация sample_har против заглушки."""
        validator = HarValidator("http://test:18080")
        validator._loaded = True
        validator._loader = _make_stub_loader()

        fixture_path = Path(__file__).resolve().parent / "fixtures" / "sample_har.json"
        report = validator.validate_har(str(fixture_path))

        assert report.total_entries == 5
        # health, POST classifiers, GET classifiers/1, DELETE classifiers/999, GET users
        assert report.passed >= 3  # минимум 3 должны пройти
        assert report.failed == 0, f"Expected 0 failed, got {report.failed}: " \
            f"{[r.errors for r in report.results if not r.passed]}"


class TestFormatHarReport:
    """Тесты форматирования отчёта."""

    def test_format_report(self):
        """Форматирование не должно падать."""
        report = HarValidationReport(
            file_path="test.har",
            total_entries=5,
            passed=3,
            failed=1,
            skipped=1,
            results=[
                HarValidationResult(
                    path="/health", method="GET", status_code=200,
                    matched_endpoint="GET /health", passed=True,
                ),
                HarValidationResult(
                    path="/error", method="GET", status_code=500,
                    matched_endpoint="GET /error", passed=False,
                    errors=[HarValidationError(
                        path="/error", method="GET", status_code=500,
                        category="status_code",
                        message="Status code 500 не описан в OpenAPI",
                    )],
                ),
            ],
        )
        text = format_har_report(report)
        assert "HAR Validation" in text
        assert "/error" in text
        assert "Status code 500" in text


# ── Stub OpenAPI Loader ──────────────────────────────────────────────

def _make_stub_loader():
    """Создать OpenApiLoader с предзаполненными эндпоинтами для тестов."""
    from service_checker.core.openapi_loader import OpenApiLoader
    loader = OpenApiLoader("http://test:18080")

    # GET /health
    loader.endpoints["/health"] = {
        "GET": _make_endpoint(
            method="GET", path="/health",
            responses={
                "200": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                    },
                    "required": ["status"],
                }
            },
        )
    }

    # POST /api/v1/registry/classifiers
    loader.endpoints["/api/v1/registry/classifiers"] = {
        "POST": _make_endpoint(
            method="POST", path="/api/v1/registry/classifiers",
            request_body={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["name"],
            },
            responses={
                "200": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                    },
                    "required": ["id", "name"],
                },
            },
        )
    }

    # /api/v1/registry/classifiers/{classifier_id} — GET + DELETE
    loader.endpoints["/api/v1/registry/classifiers/{classifier_id}"] = {
        "GET": _make_endpoint(
            method="GET", path="/api/v1/registry/classifiers/{classifier_id}",
            responses={
                "200": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                    },
                    "required": ["id", "name"],
                },
            },
        ),
        "DELETE": _make_endpoint(
            method="DELETE", path="/api/v1/registry/classifiers/{classifier_id}",
            responses={
                "200": {"type": "object", "properties": {}},
                "404": {
                    "type": "object",
                    "properties": {
                        "detail": {"type": "string"},
                    },
                },
            },
        ),
    }

    # GET /api/v1/auth/users (с query params)
    loader.endpoints["/api/v1/auth/users"] = {
        "GET": _make_endpoint(
            method="GET", path="/api/v1/auth/users",
            parameters=[
                {"name": "skip", "in": "query", "schema": {"type": "integer"}},
                {"name": "limit", "in": "query", "schema": {"type": "integer"}},
            ],
            responses={
                "200": {
                    "type": "object",
                    "properties": {
                        "users": {"type": "array", "items": {"type": "object"}},
                        "total": {"type": "integer"},
                    },
                    "required": ["users", "total"],
                },
            },
        )
    }

    return loader
