"""
Tests for core/openapi_loader.py and core/schema_comparator.py.
"""

from __future__ import annotations

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any, Dict

from service_checker.core.openapi_loader import OpenApiLoader, OpenApiEndpoint
from service_checker.core.schema_comparator import (
    SchemaComparator,
    ServiceDiff,
    EndpointDiff,
    FieldDiff,
    format_diff,
    summarize_diff,
)
from service_checker.core.md_parser import MdEndpoint, MdBody, MdField


# ── OpenApiLoader tests ──────────────────────────────────────────

class TestOpenApiLoaderResolveRefs:
    """Тесты разрешения $ref."""

    @pytest.mark.asyncio
    async def test_resolve_local_ref(self):
        """$ref на local components/schemas должен разрешаться."""
        spec = {
            "openapi": "3.0.3",
            "components": {
                "schemas": {
                    "Error": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "integer"},
                            "message": {"type": "string"},
                        },
                    }
                }
            },
            "paths": {
                "/test": {
                    "get": {
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/Error"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
        }

        loader = OpenApiLoader("http://test:8080")
        loader.spec = spec
        loader._resolve_refs()

        # Проверяем, что $ref разрешён
        path_item = loader.spec["paths"]["/test"]["get"]
        resp_schema = path_item["responses"]["200"]["content"]["application/json"]["schema"]
        assert resp_schema["type"] == "object"
        assert "code" in resp_schema["properties"]
        assert resp_schema["properties"]["code"]["type"] == "integer"

    @pytest.mark.asyncio
    async def test_resolve_nested_ref(self):
        """Вложенный $ref должен разрешаться."""
        spec = {
            "openapi": "3.0.3",
            "components": {
                "schemas": {
                    "DataItem": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                        },
                    },
                    "Response": {
                        "type": "object",
                        "properties": {
                            "data": {"$ref": "#/components/schemas/DataItem"},
                        },
                    },
                }
            },
            "paths": {
                "/item": {
                    "get": {
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/Response"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
        }

        loader = OpenApiLoader("http://test:8080")
        loader.spec = spec
        loader._resolve_refs()

        schema = loader.spec["paths"]["/item"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
        assert schema["type"] == "object"
        assert schema["properties"]["data"]["type"] == "object"
        assert schema["properties"]["data"]["properties"]["id"]["type"] == "integer"

    @staticmethod
    def _make_mock_response(status_code: int, json_data: Dict):
        mock = MagicMock()
        mock.status_code = status_code
        mock.json.return_value = json_data
        return mock


class TestOpenApiLoaderFlatten:
    """Тесты flatten_schema."""

    def test_flatten_simple(self):
        schema = {
            "type": "object",
            "required": ["status", "service"],
            "properties": {
                "status": {"type": "string"},
                "service": {"type": "string"},
                "version": {"type": "string"},
            }
        }
        loader = OpenApiLoader("http://test:8080")
        flat = loader._flatten_schema(schema)
        assert flat["status"]["type"] == "string"
        assert flat["status"]["required"] is True
        assert flat["service"]["required"] is True
        assert flat["version"]["required"] is False  # не в required

    def test_flatten_nested(self):
        schema = {
            "type": "object",
            "required": ["data"],
            "properties": {
                "data": {
                    "type": "object",
                    "required": ["id", "title"],
                    "properties": {
                        "id": {"type": "integer"},
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                    },
                },
                "meta": {
                    "type": "object",
                    "properties": {
                        "total": {"type": "integer"},
                    },
                },
            },
        }
        loader = OpenApiLoader("http://test:8080")
        flat = loader._flatten_schema(schema)
        assert flat["data"]["type"] == "object"
        assert flat["data"]["required"] is True
        assert flat["data.id"]["type"] == "integer"
        assert flat["data.id"]["required"] is True
        assert flat["data.description"]["required"] is False
        assert flat["meta.total"]["type"] == "integer"


class TestOpenApiLoaderMatchEndpoint:
    """Тесты match_endpoint."""

    def _make_loader_with_endpoints(self):
        loader = OpenApiLoader("http://test:8080")
        loader.endpoints = {
            "/api/v1/items/{item_id}": {
                "GET": OpenApiEndpoint(method="GET", path="/api/v1/items/{item_id}"),
            },
            "/api/v1/items": {
                "GET": OpenApiEndpoint(method="GET", path="/api/v1/items"),
            },
        }
        return loader

    def test_exact_match(self):
        loader = self._make_loader_with_endpoints()
        ep = loader.match_endpoint("/api/v1/items", "GET")
        assert ep is not None
        assert ep.path == "/api/v1/items"

    def test_path_param_match(self):
        loader = self._make_loader_with_endpoints()
        ep = loader.match_endpoint("/api/v1/items/42", "GET")
        assert ep is not None
        assert ep.path == "/api/v1/items/{item_id}"

    def test_no_match(self):
        loader = self._make_loader_with_endpoints()
        ep = loader.match_endpoint("/api/v1/other", "GET")
        assert ep is None


# ── SchemaComparator tests ──────────────────────────────────────

class TestSchemaComparator:
    """Тесты сравнения схем."""

    def test_identical_schemas(self):
        """Две одинаковые схемы — без расхождений."""
        md_eps = [
            MdEndpoint(
                method="GET",
                path="/api/v1/health",
                group="health",
                title="Health check",
                responses={
                    "200": MdBody(
                        status_code="200",
                        json_example={
                            "type": "object",
                            "required": ["status"],
                            "properties": {
                                "status": {"type": "string"},
                                "version": {"type": "string"},
                            },
                        },
                    ),
                },
            ),
        ]

        oapi_eps = {
            "/api/v1/health": {
                "GET": OpenApiEndpoint(
                    method="GET",
                    path="/api/v1/health",
                    responses={
                        "200": {
                            "type": "object",
                            "required": ["status"],
                            "properties": {
                                "status": {"type": "string"},
                                "version": {"type": "string"},
                            },
                        },
                    },
                ),
            },
        }

        diff = SchemaComparator.compare_endpoints(md_eps, oapi_eps)

        assert len(diff.endpoints) == 1
        ed = diff.endpoints[0]
        assert len(ed.missing_in_md) == 0
        assert len(ed.missing_in_oapi) == 0
        assert len(ed.type_mismatches) == 0

    def test_missing_fields(self):
        """Поля, отсутствующие в одной из схем."""
        md_eps = [
            MdEndpoint(
                method="GET",
                path="/api/v1/item",
                group="items",
                title="Get item",
                responses={
                    "200": MdBody(
                        status_code="200",
                        json_example={
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer"},
                                "name": {"type": "string"},
                            },
                        },
                    ),
                },
            ),
        ]

        oapi_eps = {
            "/api/v1/item": {
                "GET": OpenApiEndpoint(
                    method="GET",
                    path="/api/v1/item",
                    responses={
                        "200": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer"},
                                "name": {"type": "string"},
                                "extra_field": {"type": "string"},
                            },
                        },
                    },
                ),
            },
        }

        diff = SchemaComparator.compare_endpoints(md_eps, oapi_eps)
        assert len(diff.endpoints) == 1
        ed = diff.endpoints[0]
        # extra_field есть в OpenAPI, нет в md
        assert "extra_field" in ed.missing_in_md

    def test_type_mismatch(self):
        """Несовпадение типов."""
        md_eps = [
            MdEndpoint(
                method="GET",
                path="/api/v1/item",
                group="items",
                title="Get item",
                responses={
                    "200": MdBody(
                        status_code="200",
                        json_example={
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "count": {"type": "integer"},
                            },
                        },
                    ),
                },
            ),
        ]

        oapi_eps = {
            "/api/v1/item": {
                "GET": OpenApiEndpoint(
                    method="GET",
                    path="/api/v1/item",
                    responses={
                        "200": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer"},
                                "count": {"type": "string"},
                            },
                        },
                    },
                ),
            },
        }

        diff = SchemaComparator.compare_endpoints(md_eps, oapi_eps)
        assert len(diff.endpoints) == 1
        ed = diff.endpoints[0]

        # id: string ↔ integer — совместимы (автоконверсия)
        # count: integer ↔ string — совместимы
        # Так что type_mismatches должно быть 0 (string ↔ integer допустимо)
        assert len(ed.type_mismatches) == 0

    def test_incompatible_type(self):
        """Несовместимые типы (object vs string)."""
        md_eps = [
            MdEndpoint(
                method="GET",
                path="/api/v1/item",
                group="items",
                title="Get item",
                responses={
                    "200": MdBody(
                        status_code="200",
                        json_example={
                            "type": "object",
                            "properties": {
                                "data": {"type": "object"},
                            },
                        },
                    ),
                },
            ),
        ]

        oapi_eps = {
            "/api/v1/item": {
                "GET": OpenApiEndpoint(
                    method="GET",
                    path="/api/v1/item",
                    responses={
                        "200": {
                            "type": "object",
                            "properties": {
                                "data": {"type": "string"},
                            },
                        },
                    },
                ),
            },
        }

        diff = SchemaComparator.compare_endpoints(md_eps, oapi_eps)
        assert len(diff.endpoints) == 1
        ed = diff.endpoints[0]
        assert len(ed.type_mismatches) >= 1
        assert ed.type_mismatches[0].field == "data"

    def test_md_only_endpoints(self):
        """Эндпоинты, описанные в md, но отсутствующие в OpenAPI."""
        md_eps = [
            MdEndpoint(method="GET", path="/api/v1/health", group="health", title="Health"),
            MdEndpoint(method="POST", path="/api/v1/extra", group="extra", title="Extra"),
        ]

        oapi_eps = {
            "/api/v1/health": {
                "GET": OpenApiEndpoint(method="GET", path="/api/v1/health"),
            },
        }

        diff = SchemaComparator.compare_endpoints(md_eps, oapi_eps)
        assert "POST /api/v1/extra" in diff.md_only_endpoints

    def test_oapi_only_endpoints(self):
        """Эндпоинты, присутствующие в OpenAPI, но не описанные в md."""
        md_eps = [
            MdEndpoint(method="GET", path="/api/v1/health", group="health", title="Health"),
        ]

        oapi_eps = {
            "/api/v1/health": {
                "GET": OpenApiEndpoint(method="GET", path="/api/v1/health"),
            },
            "/api/v1/secret": {
                "GET": OpenApiEndpoint(method="GET", path="/api/v1/secret"),
            },
        }

        diff = SchemaComparator.compare_endpoints(md_eps, oapi_eps)
        assert "GET /api/v1/secret" in diff.oapi_only_endpoints

    def test_query_param_diff(self):
        """Различия в query-параметрах."""
        md_eps = [
            MdEndpoint(
                method="GET",
                path="/api/v1/search",
                group="search",
                title="Search",
                query_params=[
                    MdField(name="q", type_raw="string", required=True),
                    MdField(name="page", type_raw="int", required=False),
                ],
            ),
        ]

        oapi_eps = {
            "/api/v1/search": {
                "GET": OpenApiEndpoint(
                    method="GET",
                    path="/api/v1/search",
                    parameters=[
                        {"name": "q", "in": "query", "schema": {"type": "string"}},
                        {"name": "limit", "in": "query", "schema": {"type": "integer"}},
                    ],
                ),
            },
        }

        diff = SchemaComparator.compare_endpoints(md_eps, oapi_eps)
        assert len(diff.endpoints) == 1
        ed = diff.endpoints[0]
        # page — в md, нет в OpenAPI
        assert "page" in ed.extra_query_params
        # limit — в OpenAPI, нет в md
        assert "limit" in ed.missing_query_params


class TestSummarizeDiff:
    def test_empty(self):
        diff = ServiceDiff(service_key="test")
        summary = summarize_diff(diff)
        assert summary["endpoints_total"] == 0
        assert summary["endpoints_with_issues"] == 0

    def test_with_issues(self):
        diff = ServiceDiff(
            service_key="test",
            endpoints=[
                EndpointDiff(
                    path="/api/v1/test",
                    method="GET",
                    missing_in_md=["field1", "field2"],
                    type_mismatches=[
                        FieldDiff(field="f1", md_type="string", oapi_type="integer"),
                    ],
                ),
                EndpointDiff(
                    path="/api/v1/test2",
                    method="POST",
                    missing_in_oapi=["field3"],
                ),
            ],
        )
        summary = summarize_diff(diff)
        assert summary["endpoints_total"] == 2
        assert summary["endpoints_with_issues"] == 2
        assert summary["type_mismatches"] == 1
        assert summary["missing_in_md"] == 2
        assert summary["missing_in_oapi"] == 1


class TestFormatDiff:
    def test_format_output(self):
        diff = ServiceDiff(
            service_key="test",
            endpoints=[
                EndpointDiff(
                    path="/api/v1/test",
                    method="GET",
                    md_title="Test endpoint",
                    missing_in_md=["field_x"],
                ),
            ],
        )
        output = format_diff(diff)
        assert "GET /api/v1/test" in output
        assert "field_x" in output
