from __future__ import annotations

import json
from typing import Any

import pytest
from pydantic import ValidationError

from convertor_validator_service_lama.models.document_structure_extraction import (
    DocumentProfile,
    DocumentStructureExtraction,
    ItemClassificationExtraction,
    ItemRole,
    NumberingScopeExtraction,
    NumberingScopeType,
    ParseItemSpan,
    SectionExtraction,
    SectionKind,
)
from convertor_validator_service_lama.services.document_structure_prompt_agent import (
    DocumentStructurePromptAgent,
    DocumentStructurePromptAgentConfig,
    parse_json_object_response,
)


class FakeStructuredJsonPromptBackend:
    def __init__(self, outputs: list[dict[str, Any]]) -> None:
        self.outputs = outputs
        self.calls: list[dict[str, Any]] = []

    def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        json_schema: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "json_schema": json_schema,
                "metadata": metadata or {},
            }
        )

        if not self.outputs:
            raise AssertionError("Fake backend has no more outputs.")

        return self.outputs.pop(0)


def make_overview_output() -> dict[str, Any]:
    extraction = DocumentStructureExtraction(
        document_profile=DocumentProfile.SIMPLE_STANDARD,
        page_count=2,
        numbering_scopes=[
            NumberingScopeExtraction(
                namespace_id="main_document",
                title="Main document",
                scope_type=NumberingScopeType.MAIN_DOCUMENT,
                page_start=1,
                page_end=2,
                confidence=0.95,
                reason="Fake overview.",
            )
        ],
    )

    return extraction.model_dump(mode="json")


def make_scope_output() -> dict[str, Any]:
    extraction = DocumentStructureExtraction(
        document_profile=DocumentProfile.UNKNOWN,
        page_count=2,
        numbering_scopes=[
            NumberingScopeExtraction(
                namespace_id="main_document",
                title="Main document",
                scope_type=NumberingScopeType.MAIN_DOCUMENT,
                page_start=1,
                page_end=2,
                confidence=0.95,
                reason="Fake scope.",
            )
        ],
        item_classifications=[
            ItemClassificationExtraction(
                item_index=1,
                role=ItemRole.NORMATIVE_CLAUSE,
                namespace_id="main_document",
                clause="1.1",
                is_normative_clause=True,
                source_span=ParseItemSpan(page=1, item_index=1),
                confidence=0.9,
                reason="Fake classification.",
            )
        ],
        sections=[
            SectionExtraction(
                section_id="main_document/1/1",
                namespace_id="main_document",
                namespaced_path="main_document/1/1",
                clause="1.1",
                title="Clause 1.1",
                section_kind=SectionKind.NUMBERED_CLAUSE,
                content_item_indices=[1],
                source_spans=[
                    ParseItemSpan(page=1, item_index=1),
                ],
                confidence=0.9,
                reason="Fake section.",
            )
        ],
    )

    return extraction.model_dump(mode="json")


def test_prompt_agent_extracts_overview_with_backend_and_validates_output():
    backend = FakeStructuredJsonPromptBackend(outputs=[make_overview_output()])
    agent = DocumentStructurePromptAgent(
        backend=backend,
        config=DocumentStructurePromptAgentConfig(document_hint="???? test"),
    )

    result = agent.extract_overview(
        {
            "job_id": "job-1",
            "page_count": 2,
            "items_preview_count": 2,
            "page_overview": [{"page": 1}, {"page": 2}],
            "parse_items_preview": [
                {"item_index": 0, "type": "heading", "text": "???? TEST"},
                {"item_index": 1, "type": "text", "text": "1.1. Clause"},
            ],
            "markdown_excerpt": "# ???? TEST\n1.1. Clause",
            "goal": "Determine profile and numbering scopes.",
        }
    )

    assert result.document_profile == DocumentProfile.SIMPLE_STANDARD
    assert result.numbering_scopes[0].namespace_id == "main_document"

    call = backend.calls[0]
    assert "document structure extraction agent" in call["system_prompt"]
    assert "???? test" in call["user_prompt"]
    assert "stage_type=overview" in call["user_prompt"]
    assert "???? TEST" in call["user_prompt"]
    assert call["json_schema"]["title"] == "DocumentStructureExtraction"
    assert call["metadata"]["agent_stage_type"] == "overview"
    assert call["metadata"]["job_id"] == "job-1"


def test_prompt_agent_extracts_scope_with_stage_metadata():
    backend = FakeStructuredJsonPromptBackend(outputs=[make_scope_output()])
    agent = DocumentStructurePromptAgent(backend=backend)

    result = agent.extract_scope(
        {
            "job_id": "job-1",
            "stage_id": "scope_main_document_p1_2",
            "stage_type": "scope_extraction",
            "namespace_id": "main_document",
            "scope_title": "Main document",
            "scope_type": "MAIN_DOCUMENT",
            "page_start": 1,
            "page_end": 2,
            "window_index": 1,
            "windows_count": 1,
            "page_count": 2,
            "items_count": 3,
            "items_preview_count": 3,
            "parse_items_preview": [
                {"item_index": 1, "type": "text", "text": "1.1. Clause"},
            ],
            "markdown_excerpt": "1.1. Clause",
            "goal": "Extract sections for this scope.",
        }
    )

    assert result.sections[0].namespaced_path == "main_document/1/1"

    call = backend.calls[0]
    assert "stage_type=scope" in call["user_prompt"]
    assert "stage_id=scope_main_document_p1_2" in call["user_prompt"]
    assert "namespace_id=main_document" in call["user_prompt"]
    assert call["metadata"]["agent_stage_type"] == "scope"
    assert call["metadata"]["stage_id"] == "scope_main_document_p1_2"
    assert call["metadata"]["namespace_id"] == "main_document"
    assert call["metadata"]["window_index"] == 1


def test_prompt_agent_rejects_invalid_backend_output():
    backend = FakeStructuredJsonPromptBackend(
        outputs=[
            {
                "schema_version": "document_structure_extraction_v1",
                "document_profile": "SIMPLE_STANDARD",
                "page_count": 1,
                "numbering_scopes": [],
            }
        ]
    )
    agent = DocumentStructurePromptAgent(backend=backend)

    with pytest.raises(ValidationError):
        agent.extract_overview(
            {
                "page_count": 1,
                "parse_items_preview": [],
                "markdown_excerpt": "",
            }
        )


def test_parse_json_object_response_accepts_dict_string_and_bytes():
    data = make_overview_output()

    assert parse_json_object_response(data) == data
    assert parse_json_object_response(json.dumps(data)) == data
    assert parse_json_object_response(json.dumps(data).encode("utf-8")) == data


def test_parse_json_object_response_rejects_non_object_json():
    with pytest.raises(ValueError, match="JSON object"):
        parse_json_object_response("[1, 2, 3]")


def test_parse_json_object_response_rejects_unsupported_type():
    with pytest.raises(TypeError, match="unsupported JSON response type"):
        parse_json_object_response(123)  # type: ignore[arg-type]
