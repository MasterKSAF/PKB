"""
PKB Neuroassistant — Schema Comparator.

Сравнивает две схемы (из md-документации и из OpenAPI сервиса) и выявляет расхождения:
- Поля, отсутствующие в одной из схем
- Несовпадение типов
- Несовпадение обязательности (required)
- Лишние поля
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from service_checker.core.md_parser import MdEndpoint, MdBody, MdField
from service_checker.core.openapi_loader import OpenApiEndpoint


@dataclass
class FieldDiff:
    """Различие по одному полю."""
    field: str                           # "data.id"
    md_type: Optional[str] = None        # Из md
    oapi_type: Optional[str] = None      # Из OpenAPI
    md_required: Optional[bool] = None   # Обязательность в md
    oapi_required: Optional[bool] = None  # Обязательность в OpenAPI
    md_description: str = ""
    oapi_description: str = ""


@dataclass
class EndpointDiff:
    """Расхождения по одному эндпоинту."""
    path: str
    method: str
    md_title: str = ""
    oapi_summary: str = ""
    # Типы различий
    missing_in_md: List[str] = field(default_factory=list)    # есть в OpenAPI, нет в md
    missing_in_oapi: List[str] = field(default_factory=list)  # есть в md, нет в OpenAPI
    type_mismatches: List[FieldDiff] = field(default_factory=list)
    required_mismatches: List[FieldDiff] = field(default_factory=list)
    # Query param differences
    missing_query_params: List[str] = field(default_factory=list)
    extra_query_params: List[str] = field(default_factory=list)


@dataclass
class ServiceDiff:
    """Сводные расхождения по сервису."""
    service_key: str
    service_name: str = ""
    port: int = 0
    endpoints: List[EndpointDiff] = field(default_factory=list)
    # Только в md (нет в OpenAPI)
    md_only_endpoints: List[str] = field(default_factory=list)
    # Только в OpenAPI (нет в md)
    oapi_only_endpoints: List[str] = field(default_factory=list)


class SchemaComparator:
    """Сравнение MdEndpoint с OpenApiEndpoint."""

    @staticmethod
    def compare_endpoints(
        md_eps: List[MdEndpoint],
        oapi_eps: Dict[str, Dict[str, OpenApiEndpoint]],
    ) -> ServiceDiff:
        """Сравнить все эндпоинты сервиса.

        Args:
            md_eps: Эндпоинты из md-документации
            oapi_eps: Эндпоинты из OpenAPI, grouped by path -> method -> endpoint

        Returns:
            ServiceDiff с расхождениями
        """
        # Строим индекс md эндпоинтов: (path, method) -> MdEndpoint
        md_index: Dict[Tuple[str, str], MdEndpoint] = {}
        for ep in md_eps:
            md_index[(ep.path, ep.method)] = ep

        # Строим индекс oapi эндпоинтов
        oapi_index: Dict[Tuple[str, str], OpenApiEndpoint] = {}
        for path, methods in oapi_eps.items():
            for method, ep in methods.items():
                oapi_index[(path, method)] = ep

        md_keys = set(md_index.keys())
        oapi_keys = set(oapi_index.keys())

        common_keys = md_keys & oapi_keys
        md_only = md_keys - oapi_keys
        oapi_only = oapi_keys - md_keys

        diffs: List[EndpointDiff] = []

        for path, method in sorted(common_keys):
            md_ep = md_index[(path, method)]
            oapi_ep = oapi_index[(path, method)]
            diff = SchemaComparator._compare_single(md_ep, oapi_ep)
            diffs.append(diff)

        # Эндпоинты только в md или только в openapi
        md_only_str = sorted(f"{m} {p}" for p, m in md_only)
        oapi_only_str = sorted(f"{m} {p}" for p, m in oapi_only)

        # Определяем service info
        service_key = ""
        service_name = ""
        port = 0
        if md_eps:
            from service_checker.core.md_parser import MdService
            service_name = md_eps[0].group
        if oapi_eps:
            pass  # берём из первого

        return ServiceDiff(
            service_key=service_key,
            endpoints=diffs,
            md_only_endpoints=md_only_str,
            oapi_only_endpoints=oapi_only_str,
        )

    @staticmethod
    def _compare_single(md_ep: MdEndpoint, oapi_ep: OpenApiEndpoint) -> EndpointDiff:
        """Сравнить один эндпоинт."""
        diff = EndpointDiff(
            path=md_ep.path,
            method=md_ep.method,
            md_title=md_ep.title,
            oapi_summary=oapi_ep.summary,
        )

        # Сравниваем query-параметры
        md_qp = {(p.name, p.type_raw) for p in md_ep.query_params}
        oapi_qp = {
            (p.get("name", ""), p.get("schema", {}).get("type", "string"))
            for p in oapi_ep.parameters
        }
        md_qp_names = {p.name for p in md_ep.query_params}
        oapi_qp_names = {p.get("name") for p in oapi_ep.parameters}

        extra_qp = md_qp_names - oapi_qp_names
        missing_qp = oapi_qp_names - md_qp_names
        if extra_qp:
            diff.extra_query_params = sorted(extra_qp)
        if missing_qp:
            diff.missing_query_params = sorted(missing_qp)

        # Сравниваем поля ответа (по плоской карте)
        # Берём первый response (200) для сравнения
        md_response = None
        for sc in ("200", "201", "default"):
            if sc in md_ep.responses:
                md_response = md_ep.responses[sc]
                break

        oapi_response = None
        for sc in ("200", "201", "default"):
            if sc in oapi_ep.responses:
                oapi_response = oapi_ep.responses[sc]
                break

        if md_response and oapi_response:
            # Из md строим плоскую карту
            md_fields = {}
            if md_response.json_example and isinstance(md_response.json_example, dict):
                # Если json_example — JSON Schema (после merge)
                md_fields = SchemaComparator._flatten_md_schema(md_response.json_example)
            elif md_response.fields:
                md_fields = SchemaComparator._flatten_md_fields(md_response.fields)

            # Если flat_fields не заданы (тесты), вычисляем из responses
            oapi_fields = oapi_ep.flat_fields
            if not oapi_fields and oapi_ep.responses:
                # Берём первый response
                from service_checker.core.openapi_loader import OpenApiLoader
                loader_stub = OpenApiLoader("http://stub")
                for sc in ("200", "201", "default"):
                    if sc in oapi_ep.responses:
                        oapi_fields = loader_stub._flatten_schema(oapi_ep.responses[sc])
                        break

            # Сравниваем
            all_fields = set(list(md_fields.keys()) + list(oapi_fields.keys()))
            for field in sorted(all_fields):
                md_info = md_fields.get(field, {})
                oapi_info = oapi_fields.get(field, {})

                md_type = md_info.get("type")
                oapi_type = oapi_info.get("type")

                if not md_info and oapi_info:
                    diff.missing_in_md.append(field)
                elif md_info and not oapi_info:
                    diff.missing_in_oapi.append(field)
                elif md_info and oapi_info:
                    # Сравниваем типы
                    if md_type and oapi_type and md_type != oapi_type:
                        # Допускаем string ↔ integer (автоконверсия)
                        if not SchemaComparator._is_type_compatible(md_type, oapi_type):
                            fd = FieldDiff(
                                field=field,
                                md_type=md_type,
                                oapi_type=oapi_type,
                                md_required=md_info.get("required"),
                                oapi_required=oapi_info.get("required"),
                            )
                            diff.type_mismatches.append(fd)

                    # Сравниваем required
                    md_req = md_info.get("required", True)
                    oapi_req = oapi_info.get("required", True)
                    if md_req != oapi_req:
                        fd = FieldDiff(
                            field=field,
                            md_type=md_type,
                            oapi_type=oapi_type,
                            md_required=md_req,
                            oapi_required=oapi_req,
                        )
                        # Не добавляем в required_mismatches если одно из них False
                        # (OpenAPI может не указывать required для опциональных)
                        if md_req and not oapi_req:
                            diff.required_mismatches.append(fd)

        elif md_response and not oapi_response:
            # Поля из md отсутствуют в OpenAPI (весь ответ)
            pass
        elif oapi_response and not md_response:
            # Поля из OpenAPI отсутствуют в md
            pass

        return diff

    @staticmethod
    def _is_type_compatible(t1: str, t2: str) -> bool:
        """Проверить совместимость типов."""
        # string ↔ integer — допустимо (автоконверсия)
        if {t1, t2} <= {"string", "integer"}:
            return True
        # string ↔ number
        if {t1, t2} <= {"string", "number"}:
            return True
        # object ↔ any
        if t1 == "object" and t2 == "any":
            return True
        if t2 == "object" and t1 == "any":
            return True
        return t1 == t2

    @staticmethod
    def _flatten_md_schema(
        schema: Dict[str, Any], prefix: str = ""
    ) -> Dict[str, Dict[str, Any]]:
        """Преобразовать md JSON Schema в плоскую карту."""
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
                    if prop_type == "object":
                        result.update(
                            SchemaComparator._flatten_md_schema(prop, full_path)
                        )
                    elif prop_type == "array":
                        items = prop.get("items", {})
                        if isinstance(items, dict):
                            result.update(
                                SchemaComparator._flatten_md_schema(items, f"{full_path}[]")
                            )

        elif schema_type == "array":
            items = schema.get("items", {})
            if isinstance(items, dict):
                result.update(
                    SchemaComparator._flatten_md_schema(items, f"{prefix}[]")
                )

        return result

    @staticmethod
    def _flatten_md_fields(
        fields: List[MdField],
    ) -> Dict[str, Dict[str, Any]]:
        """Преобразовать список MdField в плоскую карту."""
        from service_checker.core.md_parser import _map_type
        result: Dict[str, Dict[str, Any]] = {}
        for f in fields:
            result[f.name] = {
                "type": _map_type(f.type_raw),
                "required": f.required,
                "description": f.description,
            }
        return result


def format_diff(diff: ServiceDiff) -> str:
    """Форматировать расхождения в читаемый текст."""
    lines: List[str] = []
    w = lines.append

    if diff.endpoints:
        w(f"\n📊 Сравнение эндпоинтов:")
        for ed in diff.endpoints:
            has_issues = (
                ed.missing_in_md or ed.missing_in_oapi or
                ed.type_mismatches or ed.required_mismatches
            )
            status = "⚠️" if has_issues else "✅"
            w(f"\n  {status} {ed.method} {ed.path}")
            if ed.md_title:
                w(f"     MD: {ed.md_title}")
            if ed.oapi_summary:
                w(f"     OpenAPI: {ed.oapi_summary}")
            if ed.missing_in_md:
                w(f"     ❌ В OpenAPI есть, в md нет:")
                for f in ed.missing_in_md[:10]:
                    w(f"       - {f}")
                if len(ed.missing_in_md) > 10:
                    w(f"       ... и ещё {len(ed.missing_in_md) - 10}")
            if ed.missing_in_oapi:
                w(f"     ⚠️ В md есть, в OpenAPI нет:")
                for f in ed.missing_in_oapi[:10]:
                    w(f"       - {f}")
                if len(ed.missing_in_oapi) > 10:
                    w(f"       ... и ещё {len(ed.missing_in_oapi) - 10}")
            if ed.type_mismatches:
                w(f"     🔴 Несовпадение типов:")
                for fd in ed.type_mismatches[:5]:
                    w(f"       {fd.field}: md={fd.md_type}, oapi={fd.oapi_type}")
            if ed.required_mismatches:
                w(f"     🟡 Обязательность:")
                for fd in ed.required_mismatches[:5]:
                    w(f"       {fd.field}: md_req={fd.md_required}, oapi_req={fd.oapi_required}")

    if diff.md_only_endpoints:
        w(f"\n  📝 Только в md (нет в OpenAPI):")
        for ep in diff.md_only_endpoints[:10]:
            w(f"    - {ep}")
        if len(diff.md_only_endpoints) > 10:
            w(f"    ... и ещё {len(diff.md_only_endpoints) - 10}")

    if diff.oapi_only_endpoints:
        w(f"\n  🔧 Только в OpenAPI (нет в md):")
        for ep in diff.oapi_only_endpoints[:10]:
            w(f"    - {ep}")
        if len(diff.oapi_only_endpoints) > 10:
            w(f"    ... и ещё {len(diff.oapi_only_endpoints) - 10}")

    return "\n".join(lines)


def summarize_diff(diff: ServiceDiff) -> Dict[str, Any]:
    """Сводная статистика расхождений."""
    total_endpoints = len(diff.endpoints)
    endpoints_with_issues = sum(
        1 for ed in diff.endpoints
        if ed.missing_in_md or ed.missing_in_oapi or ed.type_mismatches
    )
    total_type_mismatches = sum(len(ed.type_mismatches) for ed in diff.endpoints)
    total_missing_in_md = sum(len(ed.missing_in_md) for ed in diff.endpoints)
    total_missing_in_oapi = sum(len(ed.missing_in_oapi) for ed in diff.endpoints)

    return {
        "endpoints_total": total_endpoints,
        "endpoints_with_issues": endpoints_with_issues,
        "type_mismatches": total_type_mismatches,
        "missing_in_md": total_missing_in_md,
        "missing_in_oapi": total_missing_in_oapi,
        "md_only_endpoints": len(diff.md_only_endpoints),
        "oapi_only_endpoints": len(diff.oapi_only_endpoints),
    }
