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
from convertor_validator_service_lama.services.document_structure_workflow_runtime import (
    LlamaExtractDocumentStructureWorkflowRuntimeConfig,
    run_llama_extract_document_structure_workflow,
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


def make_payload(*, pages: int = 2, items_count: int = 3) -> dict[str, Any]:
    return {
        "job_id": "parse-job-from-payload",
        "status": "COMPLETED",
        "job_metadata": {"pdf-pages": pages},
        "items": [
            {
                "type": "text",
                "page_number": min(index + 1, pages),
                "md": f"{index + 1}. Test item",
            }
            for index in range(items_count)
        ],
        "markdown": "test document",
    }


def make_overview_output(
    *,
    page_count: int = 2,
    page_end: int = 2,
) -> dict[str, Any]:
    return DocumentStructureExtraction(
        document_profile=DocumentProfile.SIMPLE_STANDARD,
        page_count=page_count,
        numbering_scopes=[
            NumberingScopeExtraction(
                namespace_id="main_document",
                title="Main document",
                scope_type=NumberingScopeType.MAIN_DOCUMENT,
                page_start=1,
                page_end=page_end,
                confidence=0.95,
                reason="Fake overview.",
            )
        ],
    ).model_dump(mode="json")


def make_scope_output(
    *,
    page_count: int = 2,
    item_index: int = 1,
) -> dict[str, Any]:
    return DocumentStructureExtraction(
        document_profile=DocumentProfile.UNKNOWN,
        page_count=page_count,
        numbering_scopes=[
            NumberingScopeExtraction(
                namespace_id="main_document",
                title="Main document",
                scope_type=NumberingScopeType.MAIN_DOCUMENT,
                page_start=1,
                page_end=page_count,
                confidence=0.95,
                reason="Fake scope.",
            )
        ],
        item_classifications=[
            ItemClassificationExtraction(
                item_index=item_index,
                role=ItemRole.NORMATIVE_CLAUSE,
                namespace_id="main_document",
                clause="1.1",
                is_normative_clause=True,
                source_span=ParseItemSpan(page=1, item_index=item_index),
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
                content_item_indices=[item_index],
                source_spans=[
                    ParseItemSpan(page=1, item_index=item_index),
                ],
                confidence=0.9,
                reason="Fake section.",
            )
        ],
    ).model_dump(mode="json")


def test_runtime_runs_llama_extract_document_structure_workflow():
    polling_config = ExtractJobPollingConfig(max_attempts=2, interval_seconds=0.0)
    client = FakeLlamaExtractClient(
        result_payloads=[
            make_overview_output(),
            make_scope_output(),
        ]
    )

    result = run_llama_extract_document_structure_workflow(
        make_payload(),
        settings=make_settings(),
        client=client,
        config=LlamaExtractDocumentStructureWorkflowRuntimeConfig(
            parse_job_id="parse-job-from-config",
            document_hint="GOST test",
            expand=["extract_result"],
            polling_config=polling_config,
        ),
    )

    assert result.merged_extraction.document_profile == DocumentProfile.SIMPLE_STANDARD
    assert result.merged_extraction.sections[0].namespaced_path == "main_document/1/1"
    assert result.scope_inputs_count == 1
    assert result.scope_extractions_count == 1

    assert [request.parse_job_id for request in client.start_requests] == [
        "parse-job-from-config",
        "parse-job-from-config",
    ]
    assert [request.pass_name for request in client.start_requests] == [
        "sections",
        "sections",
    ]
    assert "GOST test" in (client.start_requests[0].instructions or "")
    assert "stage_type=overview" in (client.start_requests[0].instructions or "")
    assert "stage_type=scope" in (client.start_requests[1].instructions or "")

    assert client.poll_calls == [
        {
            "job_id": "extract-job-1",
            "pass_name": "sections",
            "project_id": "project-123",
            "expand": ["extract_result"],
            "config": polling_config,
        },
        {
            "job_id": "extract-job-2",
            "pass_name": "sections",
            "project_id": "project-123",
            "expand": ["extract_result"],
            "config": polling_config,
        },
    ]

    assert client.closed is False


def test_runtime_can_use_parse_job_id_from_payload_metadata():
    client = FakeLlamaExtractClient(
        result_payloads=[
            make_overview_output(),
            make_scope_output(),
        ]
    )

    result = run_llama_extract_document_structure_workflow(
        make_payload(),
        settings=make_settings(),
        client=client,
        config=LlamaExtractDocumentStructureWorkflowRuntimeConfig(
            parse_job_id=None,
        ),
    )

    assert result.merged_extraction.sections[0].namespaced_path == "main_document/1/1"
    assert [request.parse_job_id for request in client.start_requests] == [
        "parse-job-from-payload",
        "parse-job-from-payload",
    ]


def test_runtime_uses_window_settings_for_large_scope():
    client = FakeLlamaExtractClient(
        result_payloads=[
            make_overview_output(page_count=7, page_end=7),
            make_scope_output(page_count=7, item_index=0),
            make_scope_output(page_count=7, item_index=2),
            make_scope_output(page_count=7, item_index=4),
        ]
    )

    result = run_llama_extract_document_structure_workflow(
        make_payload(pages=7, items_count=7),
        settings=make_settings(),
        client=client,
        config=LlamaExtractDocumentStructureWorkflowRuntimeConfig(
            parse_job_id="parse-job-windowed",
            scope_max_window_items=3,
            scope_overlap_items=1,
        ),
    )

    assert result.scope_inputs_count == 3
    assert result.merged_extraction.diagnostics["workflow_scope_stage_ids"] == [
        "scope_main_document_p1_3_w01",
        "scope_main_document_p3_5_w02",
        "scope_main_document_p5_7_w03",
    ]
    assert len(client.start_requests) == 4
    assert [request.parse_job_id for request in client.start_requests] == [
        "parse-job-windowed",
        "parse-job-windowed",
        "parse-job-windowed",
        "parse-job-windowed",
    ]
