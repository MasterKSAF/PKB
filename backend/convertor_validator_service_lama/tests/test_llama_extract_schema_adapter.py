from __future__ import annotations

from typing import Any

from convertor_validator_service_lama.prompts.document_structure_extraction import (
    document_structure_extraction_json_schema,
)
from convertor_validator_service_lama.services.llama_extract_schema_adapter import (
    build_llama_extract_compatible_json_schema,
)


_FORBIDDEN_KEYS = {
    "$defs",
    "$ref",
    "anyOf",
    "oneOf",
    "allOf",
    "default",
    "additionalProperties",
    "patternProperties",
    "minLength",
    "maxLength",
    "minimum",
    "maximum",
    "minItems",
    "maxItems",
    "format",
}


def test_llama_extract_schema_adapter_simplifies_document_structure_schema() -> None:
    schema = document_structure_extraction_json_schema()

    compatible = build_llama_extract_compatible_json_schema(schema)

    assert compatible["type"] == "object"
    assert isinstance(compatible["properties"], dict)
    assert "numbering_scopes" in compatible["properties"]
    assert "sections" in compatible["properties"]

    forbidden_hits: list[str] = []
    null_type_hits: list[str] = []
    max_depth = _walk_schema(
        compatible,
        forbidden_hits=forbidden_hits,
        null_type_hits=null_type_hits,
    )

    assert forbidden_hits == []
    assert null_type_hits == []
    assert max_depth <= 10

    source_span = (
        compatible["properties"]["item_classifications"]
        ["items"]["properties"]["source_span"]
    )
    source_span_properties = source_span["properties"]

    assert source_span_properties["page"]["type"] == "integer"
    assert source_span_properties["item_index"]["type"] == "integer"
    assert source_span_properties["bbox"]["type"] == "array"
    assert source_span_properties["bbox"]["items"]["type"] == "number"
    assert source_span_properties["normalized_bbox"]["type"] == "array"
    assert source_span_properties["normalized_bbox"]["items"]["type"] == "number"
    assert source_span_properties["text_preview"]["type"] == "string"


def test_llama_extract_schema_adapter_replaces_nullable_any_of_with_optional_description() -> None:
    schema = {
        "type": "object",
        "properties": {
            "clause": {
                "anyOf": [
                    {
                        "type": "string",
                        "minLength": 1,
                    },
                    {
                        "type": "null",
                    },
                ],
                "default": None,
            }
        },
    }

    compatible = build_llama_extract_compatible_json_schema(schema)

    clause = compatible["properties"]["clause"]

    assert clause["type"] == "string"
    assert "anyOf" not in clause
    assert "default" not in clause
    assert "minLength" not in clause
    assert "Optional field" in clause["description"]


def test_llama_extract_schema_adapter_resolves_local_refs() -> None:
    schema = {
        "$defs": {
            "Span": {
                "type": "object",
                "properties": {
                    "page": {"type": "integer"},
                },
                "additionalProperties": False,
            }
        },
        "type": "object",
        "properties": {
            "span": {
                "$ref": "#/$defs/Span",
            }
        },
    }

    compatible = build_llama_extract_compatible_json_schema(schema)

    span = compatible["properties"]["span"]

    assert span == {
        "type": "object",
        "properties": {
            "page": {"type": "integer"},
        },
    }


def _walk_schema(
    value: Any,
    *,
    forbidden_hits: list[str],
    null_type_hits: list[str],
    path: str = "(root)",
    depth: int = 0,
) -> int:
    max_depth = depth

    if isinstance(value, dict):
        for key, child in value.items():
            if key in _FORBIDDEN_KEYS:
                forbidden_hits.append(f"{path}.{key}")

            if key == "type" and child == "null":
                null_type_hits.append(f"{path}.type")

            child_depth = _walk_schema(
                child,
                forbidden_hits=forbidden_hits,
                null_type_hits=null_type_hits,
                path=f"{path}.{key}",
                depth=depth + 1,
            )
            max_depth = max(max_depth, child_depth)

    elif isinstance(value, list):
        for index, item in enumerate(value):
            child_depth = _walk_schema(
                item,
                forbidden_hits=forbidden_hits,
                null_type_hits=null_type_hits,
                path=f"{path}[{index}]",
                depth=depth + 1,
            )
            max_depth = max(max_depth, child_depth)

    return max_depth
