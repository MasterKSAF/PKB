"""
PKB Neuroassistant — OpenAPI Schema Loader.

Загружает /openapi.json с сервиса, разрешает $ref,
извлекает схемы для каждого эндпоинта по method + path.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import httpx


@dataclass
class OpenApiEndpoint:
    """Схема одного эндпоинта из OpenAPI."""
    method: str
    path: str
    summary: str = ""
    description: str = ""
    parameters: List[Dict[str, Any]] = field(default_factory=list)  # query params
    request_body: Optional[Dict[str, Any]] = None  # JSON Schema
    responses: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # code -> JSON Schema
    # Плоская карта всех полей: "data.id" -> {"type": "integer", "required": True}
    flat_fields: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class OpenApiLoader:
    """Загрузчик и кэшировщик OpenAPI-схем."""

    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.spec: Optional[Dict[str, Any]] = None
        self.endpoints: Dict[str, Dict[str, OpenApiEndpoint]] = {}  # path -> {method -> endpoint}
        self.errors: List[str] = []
        self.timeout = timeout

    async def load(self) -> bool:
        """Загрузить /openapi.json. Вернуть True при успехе."""
        url = f"{self.base_url}/openapi.json"
        try:
            async with httpx.AsyncClient(
                    timeout=self.timeout,
                    trust_env=False,
            ) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    self.errors.append(f"HTTP {resp.status_code} при загрузке {url}")
                    return False
                self.spec = resp.json()
        except httpx.ConnectError:
            self.errors.append(f"Сервис не отвечает: {self.base_url}")
            return False
        except httpx.TimeoutException:
            self.errors.append(f"Таймаут при загрузке {url}")
            return False
        except json.JSONDecodeError as e:
            self.errors.append(f"Невалидный JSON: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Ошибка загрузки: {e}")
            return False

        self._resolve_refs()
        self._extract_endpoints()
        return True

    def _resolve_refs(self, obj: Any = None, root: Optional[Dict] = None) -> Any:
        """Рекурсивно разрешить все $ref в spec."""
        if root is None:
            root = self.spec
            obj = self.spec
            result = self._resolve_refs_internal(obj, root)
            self.spec = result
            return result
        return self._resolve_refs_internal(obj, root)

    def _resolve_refs_internal(self, obj: Any, root: Dict) -> Any:
        """Внутренняя рекурсия разрешения $ref."""
        if obj is None:
            return None
        if isinstance(obj, dict):
            if "$ref" in obj:
                ref_path = obj["$ref"]
                # Поддерживаем только локальные ref: #/components/schemas/Name
                if ref_path.startswith("#/"):
                    parts = ref_path[2:].split("/")
                    resolved = root
                    for part in parts:
                        if isinstance(resolved, dict) and part in resolved:
                            resolved = resolved[part]
                        else:
                            return obj  # fallback
                    # Рекурсивно разрешаем внутри resolved
                    return self._resolve_refs_internal(resolved, root)
                return obj
            return {k: self._resolve_refs_internal(v, root) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._resolve_refs_internal(item, root) for item in obj]
        return obj

    def _extract_endpoints(self) -> None:
        """Извлечь все эндпоинты из OpenAPI spec."""
        if not self.spec or "paths" not in self.spec:
            self.errors.append("Нет paths в OpenAPI spec")
            return

        paths = self.spec["paths"]
        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
            for method in ("get", "post", "put", "patch", "delete"):
                operation = path_item.get(method)
                if not operation:
                    continue

                ep = OpenApiEndpoint(method=method.upper(), path=path)

                # Summary / description
                ep.summary = operation.get("summary", "")
                ep.description = operation.get("description", "")

                # Parameters (query params)
                ep.parameters = [
                    p for p in operation.get("parameters", [])
                    if isinstance(p, dict) and p.get("in") == "query"
                ]

                # Request body
                req_body = operation.get("requestBody")
                if req_body:
                    content = req_body.get("content", {})
                    json_content = content.get("application/json", {})
                    ep.request_body = json_content.get("schema")

                # Responses
                for status_code, response in operation.get("responses", {}).items():
                    if not isinstance(response, dict):
                        continue
                    content = response.get("content", {})
                    json_content = content.get("application/json", {})
                    schema = json_content.get("schema")
                    if schema:
                        # Нормализуем: если schema - список, берём первый
                        ep.responses[status_code] = schema

                # Плоская карта полей из response schema
                for sc, schema in ep.responses.items():
                    ep.flat_fields = self._flatten_schema(schema)

                self.endpoints.setdefault(path, {})[method.upper()] = ep

    def _flatten_schema(
        self, schema: Dict[str, Any], prefix: str = ""
    ) -> Dict[str, Dict[str, Any]]:
        """Преобразовать JSON Schema в плоскую карту {путь: {type, required}}."""
        result: Dict[str, Dict[str, Any]] = {}
        if not isinstance(schema, dict):
            return result

        schema_type = schema.get("type", "object")
        required_fields = set(schema.get("required", []))

        if schema_type == "object":
            properties = schema.get("properties", {})
            for key, prop in properties.items():
                full_path = f"{prefix}.{key}" if prefix else key
                if isinstance(prop, dict):
                    prop_type = prop.get("type", "object")
                    result[full_path] = {
                        "type": prop_type,
                        "required": key in required_fields,
                        "description": prop.get("description", ""),
                    }
                    # Рекурсивно для вложенных объектов
                    if prop_type == "object":
                        result.update(self._flatten_schema(prop, full_path))
                    elif prop_type == "array":
                        items = prop.get("items", {})
                        if isinstance(items, dict) and items.get("type") == "object":
                            result.update(self._flatten_schema(items, f"{full_path}[]"))

        elif schema_type == "array":
            items = schema.get("items", {})
            if isinstance(items, dict) and items.get("type") == "object":
                result.update(self._flatten_schema(items, f"{prefix}[]"))

        return result

    def get_endpoint(self, path: str, method: str) -> Optional[OpenApiEndpoint]:
        """Получить схему эндпоинта по пути и методу."""
        path_item = self.endpoints.get(path)
        if not path_item:
            return None
        return path_item.get(method.upper())

    def match_endpoint(self, path: str, method: str) -> Optional[OpenApiEndpoint]:
        """Найти эндпоинт по пути с учётом path parameters.

        Пытается найти точное совпадение, затем заменяет {param} на match-any.
        """
        # Сначала точное совпадение
        ep = self.get_endpoint(path, method)
        if ep:
            return ep

        # Ищем по шаблону: /api/v1/registry/documents/42 → /api/v1/registry/documents/{doc_id}
        path_parts = path.strip("/").split("/")
        for oa_path in self.endpoints:
            oa_parts = oa_path.strip("/").split("/")
            if len(path_parts) != len(oa_parts):
                continue
            match = True
            for pp, op in zip(path_parts, oa_parts):
                if op.startswith("{") and op.endswith("}"):
                    continue  # path param — любой
                if pp != op:
                    match = False
                    break
            if match:
                return self.get_endpoint(oa_path, method)

        return None


# ── CLI отладки ──────────────────────────────────────────────────

async def main():
    """Загрузить openapi.json с указанного сервиса."""
    import sys
    if len(sys.argv) < 2:
        print("Использование: python -m service_checker.core.openapi_loader <base_url>")
        print("Пример: python -m service_checker.core.openapi_loader http://127.0.0.1:18082")
        sys.exit(1)

    base_url = sys.argv[1]
    loader = OpenApiLoader(base_url)
    success = await loader.load()

    if not success:
        print(f"❌ Ошибка загрузки:")
        for err in loader.errors:
            print(f"  - {err}")
        sys.exit(1)

    print(f"✅ Загружена OpenAPI схема с {base_url}")
    print(f"   Эндпоинтов: {sum(len(methods) for methods in loader.endpoints.values())}")
    print(f"   Путей: {len(loader.endpoints)}")

    for path, methods in sorted(loader.endpoints.items()):
        for method, ep in sorted(methods.items()):
            print(f"  {method:6s} {path}")
            if ep.parameters:
                print(f"         Query: {len(ep.parameters)}")
            if ep.responses:
                codes = ", ".join(ep.responses.keys())
                print(f"         Responses: {codes}")
            if ep.flat_fields:
                print(f"         Fields: {len(ep.flat_fields)}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
