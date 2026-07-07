from __future__ import annotations

from copy import deepcopy
from typing import Any


_MAX_LLAMA_EXTRACT_SCHEMA_DEPTH = 8

_UNSUPPORTED_KEYS: set[str] = {
    "$defs",
    "$schema",
    "$id",
    "additionalProperties",
    "patternProperties",
    "default",
    "examples",
    "format",
    "minLength",
    "maxLength",
    "minimum",
    "maximum",
    "exclusiveMinimum",
    "exclusiveMaximum",
    "minItems",
    "maxItems",
    "multipleOf",
}


def build_llama_extract_compatible_json_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Return a LlamaExtract-compatible subset of JSON Schema.

    Pydantic's full model_json_schema() output is useful for Python-side
    validation, but too rich for LlamaExtract schema validation. This adapter
    keeps the field names and broad semantic shapes, while removing unsupported
    constructs and limiting nesting depth. The strict Pydantic contract is still
    applied after extraction.
    """

    adapted = _adapt_node(deepcopy(schema), root=schema)

    if not isinstance(adapted, dict):
        adapted = {"type": "object", "properties": {}}

    adapted["type"] = "object"

    properties = adapted.get("properties")
    if not isinstance(properties, dict):
        adapted["properties"] = {}

    adapted = _limit_schema_depth(
        adapted,
        max_depth=_MAX_LLAMA_EXTRACT_SCHEMA_DEPTH,
    )

    if not isinstance(adapted, dict):
        return {"type": "object", "properties": {}}

    adapted["type"] = "object"

    properties = adapted.get("properties")
    if not isinstance(properties, dict):
        adapted["properties"] = {}

    return adapted


def _adapt_node(value: Any, *, root: dict[str, Any]) -> Any:
    if isinstance(value, list):
        return [
            adapted_item
            for item in value
            if (adapted_item := _adapt_node(item, root=root)) is not None
        ]

    if not isinstance(value, dict):
        return value

    if "$ref" in value:
        resolved = _resolve_ref(value.get("$ref"), root=root)
        adapted = _adapt_node(resolved, root=root)

        if isinstance(adapted, dict):
            for key in ("title", "description"):
                if key in value and key not in adapted:
                    adapted[key] = value[key]

        return adapted

    if "anyOf" in value:
        return _adapt_any_of(value, root=root)

    adapted: dict[str, Any] = {}

    for key, child in value.items():
        if key in _UNSUPPORTED_KEYS:
            continue

        if key == "const":
            _copy_const_as_description(adapted, child)
            continue

        if key == "type":
            adapted_type = _adapt_type(child)

            if adapted_type is None:
                continue

            adapted[key] = adapted_type
            continue

        if key == "properties":
            if not isinstance(child, dict):
                continue

            properties: dict[str, Any] = {}

            for property_name, property_schema in child.items():
                adapted_property = _adapt_node(property_schema, root=root)

                if isinstance(adapted_property, dict):
                    properties[property_name] = adapted_property

            adapted[key] = properties
            continue

        if key == "items":
            adapted_items = _adapt_node(child, root=root)

            if isinstance(adapted_items, dict):
                adapted[key] = adapted_items

            continue

        if key == "required":
            if isinstance(child, list):
                adapted[key] = [
                    item for item in child
                    if isinstance(item, str)
                ]

            continue

        adapted_child = _adapt_node(child, root=root)

        if adapted_child is not None:
            adapted[key] = adapted_child

    if "properties" in adapted and adapted.get("type") is None:
        adapted["type"] = "object"

    if adapted.get("type") == "array" and "items" not in adapted:
        adapted["items"] = {}

    if "required" in adapted and isinstance(adapted.get("properties"), dict):
        property_names = set(adapted["properties"])
        adapted["required"] = [
            item for item in adapted["required"]
            if item in property_names
        ]

        if not adapted["required"]:
            adapted.pop("required", None)

    return adapted


def _adapt_any_of(value: dict[str, Any], *, root: dict[str, Any]) -> dict[str, Any]:
    variants = value.get("anyOf")

    if not isinstance(variants, list):
        result = {
            key: _adapt_node(child, root=root)
            for key, child in value.items()
            if key != "anyOf" and key not in _UNSUPPORTED_KEYS
        }
        return _clean_none_values(result)

    nullable = _contains_null_variant(variants, root=root)
    selected = _first_non_null_variant(variants, root=root)

    if selected is None:
        result: dict[str, Any] = {"type": "string"}
    else:
        adapted_selected = _adapt_node(selected, root=root)
        result = adapted_selected if isinstance(adapted_selected, dict) else {"type": "string"}

    for key in ("title", "description"):
        if key in value and key not in result:
            result[key] = value[key]

    if nullable:
        _append_description(
            result,
            "Optional field. Use null or omit the field when the value is absent.",
        )

    return result


def _limit_schema_depth(
    value: Any,
    *,
    max_depth: int,
    depth: int = 0,
) -> Any:
    """Prune too-deep schema details while preserving broad field types."""

    if depth >= max_depth:
        return _summarize_deep_schema(value)

    if isinstance(value, list):
        return [
            _limit_schema_depth(item, max_depth=max_depth, depth=depth + 1)
            for item in value
        ]

    if not isinstance(value, dict):
        return value

    limited: dict[str, Any] = {}

    for key, child in value.items():
        limited[key] = _limit_schema_depth(
            child,
            max_depth=max_depth,
            depth=depth + 1,
        )

    if limited.get("type") == "array" and "items" not in limited:
        limited["items"] = {}

    if "required" in limited and isinstance(limited.get("properties"), dict):
        property_names = set(limited["properties"])
        limited["required"] = [
            item for item in limited["required"]
            if item in property_names
        ]

        if not limited["required"]:
            limited.pop("required", None)

    return limited


def _summarize_deep_schema(value: Any) -> Any:
    if isinstance(value, list):
        return []

    if not isinstance(value, dict):
        return value

    schema_type = _adapt_type(value.get("type"))

    if schema_type == "array":
        result: dict[str, Any] = {
            "type": "array",
            "items": {},
        }

        items = value.get("items")

        if isinstance(items, dict):
            item_type = _adapt_type(items.get("type"))

            if item_type in {"string", "integer", "number", "boolean"}:
                result["items"] = {"type": item_type}
            elif item_type == "object" or isinstance(items.get("properties"), dict):
                result["items"] = {
                    "type": "object",
                    "properties": {},
                }
            elif item_type == "array":
                result["items"] = {
                    "type": "array",
                    "items": {},
                }

        return result

    if schema_type == "object" or isinstance(value.get("properties"), dict):
        return {
            "type": "object",
            "properties": {},
        }

    if schema_type in {"string", "integer", "number", "boolean"}:
        result = {"type": schema_type}

        enum = value.get("enum")
        if schema_type == "string" and isinstance(enum, list):
            result["enum"] = [
                item for item in enum
                if isinstance(item, str)
            ]

            if not result["enum"]:
                result.pop("enum", None)

        return result

    enum = value.get("enum")
    if isinstance(enum, list):
        values = [
            item for item in enum
            if isinstance(item, str)
        ]

        result = {"type": "string"}

        if values:
            result["enum"] = values

        return result

    return {}

def _resolve_ref(ref: Any, *, root: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(ref, str):
        return {}

    prefix = "#/$defs/"

    if not ref.startswith(prefix):
        return {}

    name = ref[len(prefix):]
    defs = root.get("$defs")

    if not isinstance(defs, dict):
        return {}

    resolved = defs.get(name)

    return resolved if isinstance(resolved, dict) else {}


def _adapt_type(value: Any) -> str | None:
    if isinstance(value, str):
        return None if value == "null" else value

    if isinstance(value, list):
        for item in value:
            if isinstance(item, str) and item != "null":
                return item

    return None


def _contains_null_variant(variants: list[Any], *, root: dict[str, Any]) -> bool:
    for variant in variants:
        if isinstance(variant, dict) and variant.get("type") == "null":
            return True

        if isinstance(variant, dict) and "$ref" in variant:
            resolved = _resolve_ref(variant.get("$ref"), root=root)

            if resolved.get("type") == "null":
                return True

    return False


def _first_non_null_variant(
    variants: list[Any],
    *,
    root: dict[str, Any],
) -> dict[str, Any] | None:
    for variant in variants:
        if not isinstance(variant, dict):
            continue

        candidate = variant

        if "$ref" in candidate:
            candidate = _resolve_ref(candidate.get("$ref"), root=root)

        if candidate.get("type") == "null":
            continue

        return variant

    return None


def _copy_const_as_description(target: dict[str, Any], value: Any) -> None:
    if value is None:
        return

    _append_description(target, f"Expected constant value: {value!r}.")


def _append_description(target: dict[str, Any], text: str) -> None:
    current = target.get("description")

    if isinstance(current, str) and current.strip():
        if text not in current:
            target["description"] = current.rstrip() + " " + text

        return

    target["description"] = text


def _clean_none_values(value: dict[str, Any]) -> dict[str, Any]:
    return {
        key: child
        for key, child in value.items()
        if child is not None
    }
