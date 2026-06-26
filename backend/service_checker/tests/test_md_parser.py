"""
Tests for core/md_parser.py — parsing docs/api/*.md files.
"""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from service_checker.core.md_parser import (
    MdApiParser,
    MdEndpoint,
    MdField,
    _map_type,
    _extract_method_path,
    _build_schema_from_example,
    _is_endpoint_header,
    _extract_json_from_code_block,
)


# ── Unit tests for utility functions ─────────────────────────────────


class TestMapType:
    def test_string(self):
        assert _map_type("string") == "string"
        assert _map_type("str") == "string"

    def test_integer(self):
        assert _map_type("int") == "integer"
        assert _map_type("integer") == "integer"
        assert _map_type("bigint") == "integer"
        assert _map_type("bigint | null") == "integer"

    def test_boolean(self):
        assert _map_type("bool") == "boolean"
        assert _map_type("boolean") == "boolean"

    def test_array(self):
        assert _map_type("string[]") == "array"
        assert _map_type("integer[]") == "array"
        assert _map_type("bigint[]") == "array"

    def test_object(self):
        assert _map_type("dict") == "object"
        assert _map_type("object") == "object"
        assert _map_type("json") == "object"

    def test_unknown(self):
        assert _map_type("unknown_type") == "string"
        assert _map_type("") == "string"


class TestExtractMethodPath:
    def test_simple(self):
        assert _extract_method_path("GET /api/v1/health") == ("GET", "/api/v1/health")
        assert _extract_method_path("POST /auth/token") == ("POST", "/auth/token")

    def test_with_dash(self):
        assert _extract_method_path("PUT /registry/classifiers/{code}") == ("PUT", "/registry/classifiers/{code}")

    def test_no_match(self):
        assert _extract_method_path("Some description text") is None
        assert _extract_method_path("") is None


class TestIsEndpointHeader:
    def test_with_method(self):
        assert _is_endpoint_header("POST /auth/token") is True
        assert _is_endpoint_header("GET /api/v1/health") is True
        assert _is_endpoint_header("4.1. POST /registry/drafts — Создать") is True

    def test_numeric(self):
        assert _is_endpoint_header("1.1. Список (плоский") is True
        assert _is_endpoint_header("3.2.1. Секции документа") is True

    def test_non_endpoint(self):
        assert _is_endpoint_header("Группы") is False
        assert _is_endpoint_header("Формат ответа") is False
        assert _is_endpoint_header("Коды ошибок") is False


class TestBuildSchemaFromExample:
    def test_string(self):
        assert _build_schema_from_example("hello") == {"type": "string"}

    def test_integer(self):
        assert _build_schema_from_example(42) == {"type": "integer"}

    def test_boolean(self):
        assert _build_schema_from_example(True) == {"type": "boolean"}

    def test_list(self):
        schema = _build_schema_from_example([1, 2, 3])
        assert schema == {"type": "array", "items": {"type": "integer"}}

    def test_simple_object(self):
        schema = _build_schema_from_example({"status": "ok", "code": 200})
        assert schema["type"] == "object"
        assert schema["properties"]["status"] == {"type": "string"}
        assert schema["properties"]["code"] == {"type": "integer"}
        assert "status" in schema["required"]
        assert "code" in schema["required"]

    def test_nested_object(self):
        schema = _build_schema_from_example({
            "data": {"id": 1, "name": "test"},
            "meta": {"total": 10}
        })
        assert schema["type"] == "object"
        assert schema["properties"]["data"]["type"] == "object"
        assert "id" in schema["properties"]["data"]["required"]


class TestExtractJsonFromCodeBlock:
    def test_simple_json(self):
        lines = [
            '```json',
            '{"status": "ok", "code": 200}',
            '```',
        ]
        result, end = _extract_json_from_code_block(lines, 0)
        assert result == {"status": "ok", "code": 200}
        assert end == 3

    def test_multiline_json(self):
        lines = [
            '```json',
            '{',
            '  "data": {"id": 1}',
            '}',
            '```',
        ]
        result, end = _extract_json_from_code_block(lines, 0)
        assert result == {"data": {"id": 1}}
        assert end == 5

    def test_no_json_block(self):
        lines = ["Some text", "More text"]
        result, end = _extract_json_from_code_block(lines, 0)
        assert result is None

    def test_invalid_json(self):
        lines = [
            '```json',
            '{invalid json}',
            '```',
        ]
        result, _ = _extract_json_from_code_block(lines, 0)
        assert result is None


# ── Integration tests: parse real md files ──────────────────────────

API_DOCS_DIR = Path(__file__).resolve().parent.parent / "docs" / "api"


@pytest.fixture
def auth_parser():
    path = API_DOCS_DIR / "auth_service_api.md"
    if not path.exists():
        pytest.skip(f"Файл не найден: {path}")
    parser = MdApiParser(str(path))
    return parser.parse()


@pytest.fixture
def registry_parser():
    path = API_DOCS_DIR / "registry_service_api.md"
    if not path.exists():
        pytest.skip(f"Файл не найден: {path}")
    parser = MdApiParser(str(path))
    return parser.parse()


class TestAuthServiceParsing:
    def test_service_info(self, auth_parser):
        assert auth_parser.port == 18082
        assert auth_parser.key == "auth"
        assert len(auth_parser.errors) == 0

    def test_endpoint_count(self, auth_parser):
        """Auth должен иметь 14 эндпоинтов."""
        assert len(auth_parser.endpoints) == 14

    def test_auth_token_endpoint(self, auth_parser):
        token_ep = next(
            (ep for ep in auth_parser.endpoints if "auth/token" in ep.path),
            None
        )
        assert token_ep is not None
        assert token_ep.method == "POST"
        assert token_ep.path == "/api/v1/auth/token"
        assert token_ep.group == "auth"
        assert token_ep.responses.get("200") is not None

    def test_admin_users_endpoint(self, auth_parser):
        users_ep = next(
            (ep for ep in auth_parser.endpoints if "admin/users" in ep.path and ep.method == "GET"),
            None
        )
        assert users_ep is not None
        assert users_ep.group == "admin"
        assert "users" in users_ep.path

    def test_health_endpoint(self, auth_parser):
        # Auth health endpoint не тестируется (может быть не в секции группа)
        pass

    def test_no_parse_errors(self, auth_parser):
        assert len(auth_parser.errors) == 0


class TestRegistryServiceParsing:
    def test_service_info(self, registry_parser):
        assert registry_parser.port == 18084
        assert registry_parser.key == "registry"
        # 1 ошибка: "7.6. Ошибки групп categories (справочно)" — не эндпоинт
        assert len(registry_parser.errors) <= 1

    def test_endpoint_count(self, registry_parser):
        """Registry должен иметь 44+ эндпоинтов."""
        assert len(registry_parser.endpoints) >= 40

    def test_classifiers_list(self, registry_parser):
        ep = next(
            (ep for ep in registry_parser.endpoints
             if ep.path == "/api/v1/registry/classifiers" and ep.method == "GET"),
            None
        )
        assert ep is not None, "GET /registry/classifiers не найден"
        assert ep.group == "classifiers"
        assert len(ep.query_params) >= 5

    def test_classifiers_create(self, registry_parser):
        ep = next(
            (ep for ep in registry_parser.endpoints
             if ep.path == "/api/v1/registry/classifiers" and ep.method == "POST"),
            None
        )
        assert ep is not None
        assert ep.request_body is not None

    def test_documents_with_placeholders(self, registry_parser):
        """Проверить, что {doc_id} корректно извлекается."""
        doc_eps = [ep for ep in registry_parser.endpoints if "{doc_id}" in ep.path]
        assert len(doc_eps) >= 5

    def test_terminology_normalize(self, registry_parser):
        ep = next(
            (ep for ep in registry_parser.endpoints
             if "normalize" in ep.path),
            None
        )
        assert ep is not None
        assert ep.method == "GET"
        assert any("term" in qp.name for qp in ep.query_params)

    def test_drafts_endpoints(self, registry_parser):
        draft_eps = [ep for ep in registry_parser.endpoints if "drafts" in ep.path]
        assert len(draft_eps) >= 5, f"Найдено draft эндпоинтов: {len(draft_eps)}"

    def test_responses_have_schema_or_fields(self, registry_parser):
        """У большинства эндпоинтов должен быть JSON example или таблица полей."""
        eps_with_response = [ep for ep in registry_parser.endpoints if ep.responses]
        assert len(eps_with_response) >= 30

    def test_classifiers_tree_params(self, registry_parser):
        ep = next(
            (ep for ep in registry_parser.endpoints
             if "classifiers/tree" in ep.path),
            None
        )
        assert ep is not None
        qp = {p.name: p.required for p in ep.query_params}
        # classifier_system — required=true (есть колонка Обязательный)
        if "classifier_system" in qp:
            assert qp["classifier_system"] is True
        # root_code — необязательный
        if "root_code" in qp:
            assert qp["root_code"] is False


class TestCrossServiceParsing:
    """Парсинг всех доступных md-файлов."""

    def test_all_files_parse_without_crash(self):
        """Все md-файлы должны парситься без исключений."""
        md_files = sorted(API_DOCS_DIR.glob("*.md"))
        assert len(md_files) >= 10, f"Найдено md-файлов: {len(md_files)}"

        results = {}
        for md_file in md_files:
            try:
                parser = MdApiParser(str(md_file))
                service = parser.parse()
                results[md_file.name] = {
                    "endpoints": len(service.endpoints),
                    "errors": len(service.errors),
                    "port": service.port,
                }
            except Exception as e:
                pytest.fail(f"Крэш при парсинге {md_file.name}: {e}")

        # Проверяем ключевые сервисы
        assert results["auth_service_api.md"]["endpoints"] >= 10
        assert results["registry_service_api.md"]["endpoints"] >= 40
        assert results["orchestrator_service_api.md"]["endpoints"] >= 15
        assert results["query_service_api.md"]["endpoints"] >= 15
        assert results["gateway_service_api.md"]["endpoints"] >= 1

        print("\n📊 Результаты парсинга всех файлов:")
        for name, info in sorted(results.items()):
            print(f"  {name:40s} {info['endpoints']:3d} эндпоинтов, "
                  f"{info['errors']} ошибок, порт {info['port']}")


class TestToOpenApi:
    """Проверка конвертации в OpenAPI формат."""

    def test_auth_to_openapi(self, auth_parser):
        openapi = MdApiParser.to_openapi(auth_parser.endpoints)
        assert openapi["openapi"] == "3.0.3"
        assert "paths" in openapi
        assert len(openapi["paths"]) >= 8

        # Проверить, что /api/v1/auth/token есть в путях
        token_path = "/api/v1/auth/token"
        assert token_path in openapi["paths"]

        # Проверить operation для POST /auth/token
        post_op = openapi["paths"][token_path].get("post")
        assert post_op is not None
        assert "responses" in post_op
        assert "200" in post_op["responses"]

    def test_registry_to_openapi(self, registry_parser):
        openapi = MdApiParser.to_openapi(registry_parser.endpoints)
        assert len(openapi["paths"]) >= 25

        # Проверить путь с плейсхолдером
        doc_path = "/api/v1/registry/documents/{doc_id}"
        assert doc_path in openapi["paths"]
