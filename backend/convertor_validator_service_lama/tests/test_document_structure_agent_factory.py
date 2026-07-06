from __future__ import annotations

from typing import Any

from convertor_validator_service_lama.core.settings import Settings
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
from convertor_validator_service_lama.models.extract_job import (
    ExtractJobPollingConfig,
    ExtractJobResult,
    ExtractJobStatus,
    ExtractJobSubmitResponse,
    ExtractPassRequest,
)
from convertor_validator_service_lama.services.document_structure_agent_factory import (
    LlamaExtractDocumentStructureAgentFactoryConfig,
    build_llama_extract_document_structure_agent,
)


class FakeLlamaExtractClient:
    def __init__(self, result_payloads: list[dict[str, Any]]) -> None:
        self.result_payloads = result_payloads
        self.start_requests: list[ExtractPassRequest] = []
        self.poll_calls: list[dict[str, Any]] = []
        self.closed = False

    def start_extract_job(self, request: ExtractPassRequest) -> ExtractJobSubmitResponse:
        self.start_requests.append(request)
        return ExtractJobSubmitResponse(
            job_id=f"extract-job-{len(self.start_requests)}",
            pass_name=request.pass_name,
            status=ExtractJobStatus.pending,
        )

    def poll_extract_job(
        self,
        job_id: str,
        pass_name: str,
        project_id: str,
        expand: list[str] | None = None,
        config: ExtractJobPollingConfig | None = None,
    ) -> ExtractJobResult:
        self.poll_calls.append(
            {
                "job_id": job_id,
                "pass_name": pass_name,
                "project_id": project_id,
                "expand": expand,
                "config": config,
            }
        )

        if not self.result_payloads:
            raise AssertionError("Fake client has no more result payloads.")

        return ExtractJobResult(
            job_id=job_id,
            pass_name=pass_name,
            status=ExtractJobStatus.completed,
            result=self.result_payloads.pop(0),
        )

    def close(self) -> None:
        self.closed = True


def make_settings() -> Settings:
    return Settings(
        cloud_api_key="test-key",
        extract_base_url="https://llama.test",
        extract_project_id="project-123",
    )


def make_overview_output() -> dict[str, Any]:
    return DocumentStructureExtraction(
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
    ).model_dump(mode="json")


def make_scope_output() -> dict[str, Any]:
    return DocumentStructureExtraction(
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
    ).model_dump(mode="json")


def test_factory_builds_document_structure_agent_backed_by_llama_extract():
    client = FakeLlamaExtractClient(result_payloads=[make_overview_output()])
    polling_config = ExtractJobPollingConfig(max_attempts=2, interval_seconds=0.0)

    bundle = build_llama_extract_document_structure_agent(
        settings=make_settings(),
        client=client,
        config=LlamaExtractDocumentStructureAgentFactoryConfig(
            parse_job_id="parse-job-123",
            document_hint="GOST test",
            pass_name="sections",
            schema_name="document_structure_extraction_v1",
            expand=["extract_result"],
            polling_config=polling_config,
        ),
    )

    result = bundle.agent.extract_overview(
        {
            "job_id": "ignored-because-config-parse-job-id-wins",
            "page_count": 2,
            "items_preview_count": 2,
            "page_overview": [{"page": 1}, {"page": 2}],
            "parse_items_preview": [
                {"item_index": 0, "type": "heading", "text": "GOST TEST"},
                {"item_index": 1, "type": "text", "text": "1.1. Clause"},
            ],
            "markdown_excerpt": "# GOST TEST\n1.1. Clause",
            "goal": "Determine profile and numbering scopes.",
        }
    )

    assert result.document_profile == DocumentProfile.SIMPLE_STANDARD

    request = client.start_requests[0]
    assert request.parse_job_id == "parse-job-123"
    assert request.pass_name == "sections"
    assert request.project_id == "project-123"
    assert request.schema_name == "document_structure_extraction_v1"
    assert request.extraction_schema["title"] == "DocumentStructureExtraction"
    assert "GOST test" in (request.instructions or "")
    assert "stage_type=overview" in (request.instructions or "")
    assert "agent_stage_type: overview" in (request.instructions or "")

    assert client.poll_calls == [
        {
            "job_id": "extract-job-1",
            "pass_name": "sections",
            "project_id": "project-123",
            "expand": ["extract_result"],
            "config": polling_config,
        }
    ]

    bundle.close()
    assert client.closed is False


def test_factory_allows_parse_job_id_from_stage_metadata():
    client = FakeLlamaExtractClient(result_payloads=[make_scope_output()])

    bundle = build_llama_extract_document_structure_agent(
        settings=make_settings(),
        client=client,
        config=LlamaExtractDocumentStructureAgentFactoryConfig(
            parse_job_id=None,
        ),
    )

    result = bundle.agent.extract_scope(
        {
            "job_id": "parse-job-from-stage-metadata",
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
    assert client.start_requests[0].parse_job_id == "parse-job-from-stage-metadata"
    assert client.poll_calls[0]["expand"] == ["extract_result"]


def test_factory_can_omit_metadata_from_instructions():
    client = FakeLlamaExtractClient(result_payloads=[make_overview_output()])

    bundle = build_llama_extract_document_structure_agent(
        settings=make_settings(),
        client=client,
        config=LlamaExtractDocumentStructureAgentFactoryConfig(
            parse_job_id="parse-job-123",
            include_metadata_in_instructions=False,
        ),
    )

    bundle.agent.extract_overview(
        {
            "job_id": "parse-job-123",
            "page_count": 2,
            "items_preview_count": 0,
            "page_overview": [],
            "parse_items_preview": [],
            "markdown_excerpt": "",
            "goal": "Determine profile and numbering scopes.",
        }
    )

    assert "agent_stage_type: overview" not in (
        client.start_requests[0].instructions or ""
    )
