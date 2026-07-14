from __future__ import annotations

from typing import Any

import pytest

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
from convertor_validator_service_lama.services.document_structure_extraction_workflow import (
    run_document_structure_extraction_workflow,
)


class FakeDocumentStructureExtractionAgent:
    def __init__(
        self,
        *,
        overview_extraction: DocumentStructureExtraction | dict[str, Any],
        scope_extractions_by_namespace: dict[str, DocumentStructureExtraction | dict[str, Any]],
    ) -> None:
        self.overview_extraction = overview_extraction
        self.scope_extractions_by_namespace = scope_extractions_by_namespace
        self.overview_calls: list[dict[str, Any]] = []
        self.scope_calls: list[dict[str, Any]] = []

    def extract_overview(
        self,
        overview_input: dict[str, Any],
    ) -> DocumentStructureExtraction | dict[str, Any]:
        self.overview_calls.append(overview_input)
        return self.overview_extraction

    def extract_scope(
        self,
        scope_input: dict[str, Any],
    ) -> DocumentStructureExtraction | dict[str, Any]:
        self.scope_calls.append(scope_input)
        namespace_id = scope_input["namespace_id"]
        return self.scope_extractions_by_namespace[namespace_id]


def make_scope(
    namespace_id: str,
    *,
    page_start: int,
    page_end: int,
    scope_type: NumberingScopeType = NumberingScopeType.MAIN_DOCUMENT,
) -> NumberingScopeExtraction:
    return NumberingScopeExtraction(
        namespace_id=namespace_id,
        title=namespace_id.replace("_", " ").title(),
        scope_type=scope_type,
        page_start=page_start,
        page_end=page_end,
        confidence=0.95,
        reason="Fake overview scope.",
    )


def make_overview_extraction(
    *,
    page_count: int,
    scopes: list[NumberingScopeExtraction],
    profile: DocumentProfile = DocumentProfile.SIMPLE_STANDARD,
) -> DocumentStructureExtraction:
    return DocumentStructureExtraction(
        document_profile=profile,
        page_count=page_count,
        numbering_scopes=scopes,
    )


def make_scope_extraction(
    *,
    namespace_id: str,
    page_count: int,
    page_start: int,
    page_end: int,
    section_path: str,
    item_index: int,
) -> DocumentStructureExtraction:
    return DocumentStructureExtraction(
        document_profile=DocumentProfile.UNKNOWN,
        page_count=page_count,
        numbering_scopes=[
            make_scope(
                namespace_id,
                page_start=page_start,
                page_end=page_end,
            )
        ],
        item_classifications=[
            ItemClassificationExtraction(
                item_index=item_index,
                role=ItemRole.NORMATIVE_CLAUSE,
                namespace_id=namespace_id,
                clause="1.1",
                is_normative_clause=True,
                source_span=ParseItemSpan(
                    page=page_start,
                    item_index=item_index,
                ),
                confidence=0.91,
                reason="Fake scope classification.",
            )
        ],
        sections=[
            SectionExtraction(
                section_id=section_path,
                namespace_id=namespace_id,
                namespaced_path=section_path,
                clause="1.1",
                title="Fake section",
                section_kind=SectionKind.NUMBERED_CLAUSE,
                content_item_indices=[item_index],
                source_spans=[
                    ParseItemSpan(
                        page=page_start,
                        item_index=item_index,
                    )
                ],
                confidence=0.9,
                reason="Fake scope section.",
            )
        ],
    )


def test_workflow_runs_overview_scope_and_merge_for_simple_document():
    payload = {
        "job_id": "job-simple",
        "status": "COMPLETED",
        "job_metadata": {"pdf-pages": 2},
        "items": [
            {"type": "heading", "page_number": 1, "md": "# ???? TEST"},
            {"type": "text", "page_number": 1, "md": "1.1. Clause text"},
            {"type": "text", "page_number": 2, "md": "2.1. Clause text"},
        ],
        "markdown": "# ???? TEST\n1.1. Clause text\n2.1. Clause text",
    }

    overview = make_overview_extraction(
        page_count=2,
        scopes=[
            make_scope(
                "main_document",
                page_start=1,
                page_end=2,
            )
        ],
    )
    scope = make_scope_extraction(
        namespace_id="main_document",
        page_count=2,
        page_start=1,
        page_end=2,
        section_path="main_document/1/1",
        item_index=1,
    )
    agent = FakeDocumentStructureExtractionAgent(
        overview_extraction=overview,
        scope_extractions_by_namespace={
            "main_document": scope,
        },
    )

    result = run_document_structure_extraction_workflow(
        payload,
        agent=agent,
    )

    assert len(agent.overview_calls) == 1
    assert len(agent.scope_calls) == 1
    assert result.scope_inputs_count == 1
    assert result.scope_extractions_count == 1
    assert result.scope_inputs[0]["stage_id"] == "scope_main_document_p1_2"
    assert result.merged_extraction.document_profile == DocumentProfile.SIMPLE_STANDARD
    assert result.merged_extraction.page_count == 2
    assert result.merged_extraction.sections[0].namespaced_path == "main_document/1/1"
    assert result.merged_extraction.diagnostics["workflow_scope_inputs_count"] == 1
    assert result.merged_extraction.diagnostics["workflow_scope_stage_ids"] == [
        "scope_main_document_p1_2"
    ]


def test_workflow_creates_scope_windows_for_large_scope():
    payload = {
        "job_id": "job-large",
        "status": "COMPLETED",
        "job_metadata": {"pdf-pages": 7},
        "items": [
            {
                "type": "text",
                "page_number": index + 1,
                "md": f"{index + 1}. Window item",
            }
            for index in range(7)
        ],
        "markdown": "large document",
    }

    overview = make_overview_extraction(
        page_count=7,
        scopes=[
            make_scope(
                "main_document",
                page_start=1,
                page_end=7,
            )
        ],
    )

    scope = make_scope_extraction(
        namespace_id="main_document",
        page_count=7,
        page_start=1,
        page_end=7,
        section_path="main_document/1/1",
        item_index=0,
    )

    agent = FakeDocumentStructureExtractionAgent(
        overview_extraction=overview,
        scope_extractions_by_namespace={
            "main_document": scope,
        },
    )

    result = run_document_structure_extraction_workflow(
        payload,
        agent=agent,
        scope_max_window_items=3,
        scope_overlap_items=1,
    )

    assert len(agent.scope_calls) == 3
    assert result.scope_inputs_count == 3
    assert result.merged_extraction.diagnostics["workflow_scope_stage_ids"] == [
        "scope_main_document_p1_3_w01",
        "scope_main_document_p3_5_w02",
        "scope_main_document_p5_7_w03",
    ]
    assert result.merged_extraction.diagnostics["duplicate_sections_merged"] == 2
    assert result.merged_extraction.sections[0].namespaced_path == "main_document/1/1"


def test_workflow_accepts_dict_outputs_from_agent():
    payload = {
        "job_id": "job-dict",
        "status": "COMPLETED",
        "job_metadata": {"pdf-pages": 1},
        "items": [
            {"type": "text", "page_number": 1, "md": "1.1. Clause text"},
        ],
        "markdown": "1.1. Clause text",
    }

    overview = make_overview_extraction(
        page_count=1,
        scopes=[
            make_scope(
                "main_document",
                page_start=1,
                page_end=1,
            )
        ],
    )
    scope = make_scope_extraction(
        namespace_id="main_document",
        page_count=1,
        page_start=1,
        page_end=1,
        section_path="main_document/1/1",
        item_index=0,
    )

    agent = FakeDocumentStructureExtractionAgent(
        overview_extraction=overview.model_dump(mode="json"),
        scope_extractions_by_namespace={
            "main_document": scope.model_dump(mode="json"),
        },
    )

    result = run_document_structure_extraction_workflow(
        payload,
        agent=agent,
    )

    assert result.overview_extraction.numbering_scopes[0].namespace_id == "main_document"
    assert result.scope_extractions[0].sections[0].namespaced_path == "main_document/1/1"
    assert result.merged_extraction.sections[0].namespaced_path == "main_document/1/1"

def test_workflow_scope_failure_includes_stage_context():
    payload = {
        "job_id": "job-failure",
        "status": "COMPLETED",
        "job_metadata": {"pdf-pages": 2},
        "items": [
            {"type": "heading", "page_number": 1, "md": "# TEST"},
            {"type": "text", "page_number": 1, "md": "1.1. Clause text"},
            {"type": "text", "page_number": 2, "md": "2.1. Clause text"},
        ],
        "markdown": "# TEST\n1.1. Clause text\n2.1. Clause text",
    }

    overview = make_overview_extraction(
        page_count=2,
        scopes=[
            make_scope(
                "main_document",
                page_start=1,
                page_end=2,
            )
        ],
    )

    class FailingScopeAgent:
        def __init__(self) -> None:
            self.overview_calls: list[dict[str, Any]] = []
            self.scope_calls: list[dict[str, Any]] = []

        def extract_overview(
            self,
            overview_input: dict[str, Any],
        ) -> DocumentStructureExtraction:
            self.overview_calls.append(overview_input)
            return overview

        def extract_scope(
            self,
            scope_input: dict[str, Any],
        ) -> DocumentStructureExtraction:
            self.scope_calls.append(scope_input)
            raise RuntimeError("fake extract failure")

    agent = FailingScopeAgent()

    with pytest.raises(RuntimeError) as exc_info:
        run_document_structure_extraction_workflow(
            payload,
            agent=agent,
        )

    message = str(exc_info.value)

    assert "document structure scope extraction failed" in message
    assert "stage_id='scope_main_document_p1_2'" in message
    assert "namespace_id='main_document'" in message
    assert "page_start=1" in message
    assert "page_end=2" in message
    assert "items_count=3" in message
    assert "error_type=RuntimeError" in message
    assert "fake extract failure" in message

def test_workflow_overview_failure_includes_stage_context():
    payload = {
        "job_id": "job-overview-failure",
        "status": "COMPLETED",
        "job_metadata": {"pdf-pages": 2},
        "items": [
            {"type": "heading", "page_number": 1, "md": "# TEST"},
            {"type": "text", "page_number": 1, "md": "1.1. Clause text"},
            {"type": "text", "page_number": 2, "md": "2.1. Clause text"},
        ],
        "markdown": "# TEST\n1.1. Clause text\n2.1. Clause text",
    }

    class FailingOverviewAgent:
        def extract_overview(
            self,
            overview_input: dict[str, Any],
        ) -> DocumentStructureExtraction:
            raise RuntimeError("fake overview failure")

        def extract_scope(
            self,
            scope_input: dict[str, Any],
        ) -> DocumentStructureExtraction:
            raise AssertionError("scope extraction should not be called")

    with pytest.raises(RuntimeError) as exc_info:
        run_document_structure_extraction_workflow(
            payload,
            agent=FailingOverviewAgent(),
        )

    message = str(exc_info.value)

    assert "document structure overview extraction failed" in message
    assert "stage_id='overview'" in message
    assert "stage_type='overview'" in message
    assert "job_id='job-overview-failure'" in message
    assert "page_count=2" in message
    assert "items_count=3" in message
    assert "error_type=RuntimeError" in message
    assert "fake overview failure" in message
