import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from convertor_validator_service_lama.api import app as app_module
from convertor_validator_service_lama.clients.llama_cloud_boundary import (
    MissingLlamaCloudApiKeyError,
)
from convertor_validator_service_lama.clients.llama_extract_rest_client import (
    LlamaExtractJobFailedError,
    LlamaExtractPollingTimeoutError,
    LlamaExtractResponseError,
    MissingLlamaExtractProjectIdError,
)
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
from convertor_validator_service_lama.models.extract_job import ExtractJobPollingConfig
from convertor_validator_service_lama.services.document_structure_extraction_workflow import (
    DocumentStructureExtractionWorkflowResult,
)
from convertor_validator_service_lama.services.document_structure_workflow_runtime import (
    LlamaExtractDocumentStructureWorkflowRuntimeConfig,
)
from convertor_validator_service_lama.services.llama_extract_structured_json_backend import (
    LlamaExtractStructuredJsonResultError,
    MissingLlamaExtractParseJobIdError,
)


def make_extraction() -> DocumentStructureExtraction:
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
        item_classifications=[
            ItemClassificationExtraction(
                item_index=0,
                role=ItemRole.NORMATIVE_CLAUSE,
                namespace_id="main_document",
                clause="1.1",
                is_normative_clause=True,
                source_span=ParseItemSpan(page=1, item_index=0),
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
                content_item_indices=[0],
                source_spans=[ParseItemSpan(page=1, item_index=0)],
                confidence=0.9,
                reason="Fake section.",
            )
        ],
    )
    extraction.diagnostics.update(
        {
            "workflow_overview_items_preview_count": 3,
            "workflow_page_overview_count": 2,
            "workflow_scope_stage_ids": ["scope_main_document_p1_2"],
        }
    )
    return extraction


def make_workflow_result() -> DocumentStructureExtractionWorkflowResult:
    extraction = make_extraction()
    return DocumentStructureExtractionWorkflowResult(
        overview_input={"items_preview_count": 3},
        overview_extraction=extraction,
        scope_inputs=[{"stage_id": "scope_main_document_p1_2"}],
        scope_extractions=[extraction],
        merged_extraction=extraction,
    )


def test_document_structure_workflow_endpoint_runs_runtime(monkeypatch):
    captured: dict[str, object] = {}

    def fake_run_llama_extract_document_structure_workflow(
        parse_result_payload: dict,
        *,
        config: LlamaExtractDocumentStructureWorkflowRuntimeConfig | None = None,
    ) -> DocumentStructureExtractionWorkflowResult:
        captured["parse_result_payload"] = parse_result_payload
        captured["config"] = config
        return make_workflow_result()

    monkeypatch.setattr(
        app_module,
        "run_llama_extract_document_structure_workflow",
        fake_run_llama_extract_document_structure_workflow,
    )

    client = TestClient(app_module.app)

    response = client.post(
        "/document-structure-workflow",
        json={
            "parse_result_payload": {
                "job_id": "parse-job-from-payload",
                "status": "COMPLETED",
            },
            "parse_job_id": "parse-job-from-request",
            "document_hint": "GOST test",
            "pass_name": "sections",
            "schema_name": "document_structure_extraction_v1",
            "expand": ["extract_result"],
            "max_attempts": 3,
            "interval_seconds": 0.0,
            "include_metadata_in_instructions": False,
            "overview_max_items": 11,
            "scope_max_items": 12,
            "scope_max_window_items": 13,
            "scope_overlap_items": 2,
            "item_text_chars": 100,
            "markdown_excerpt_chars": 1000,
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["mode"] == "document_structure_workflow_run"
    assert body["parse_job_id"] == "parse-job-from-request"
    assert body["document_profile"] == "simple_standard"
    assert body["page_count"] == 2
    assert body["numbering_scopes_count"] == 1
    assert body["item_classifications_count"] == 1
    assert body["sections_count"] == 1
    assert body["issues_count"] == 0
    assert body["scope_inputs_count"] == 1
    assert body["scope_extractions_count"] == 1
    assert body["overview_items_preview_count"] == 3
    assert body["overview_page_overview_count"] == 2
    assert body["scope_stage_ids"] == ["scope_main_document_p1_2"]
    assert body["merged_extraction"]["sections"][0]["namespaced_path"] == "main_document/1/1"

    assert captured["parse_result_payload"] == {
        "job_id": "parse-job-from-payload",
        "status": "COMPLETED",
    }

    config = captured["config"]
    assert config == LlamaExtractDocumentStructureWorkflowRuntimeConfig(
        parse_job_id="parse-job-from-request",
        document_hint="GOST test",
        pass_name="sections",
        schema_name="document_structure_extraction_v1",
        expand=["extract_result"],
        polling_config=ExtractJobPollingConfig(
            max_attempts=3,
            interval_seconds=0.0,
        ),
        include_metadata_in_instructions=False,
        overview_max_items=11,
        scope_max_items=12,
        scope_max_window_items=13,
        scope_overlap_items=2,
        item_text_chars=100,
        markdown_excerpt_chars=1000,
    )


def test_document_structure_workflow_endpoint_can_use_parse_job_id_from_payload(monkeypatch):
    captured: dict[str, object] = {}

    def fake_run_llama_extract_document_structure_workflow(
        parse_result_payload: dict,
        *,
        config: LlamaExtractDocumentStructureWorkflowRuntimeConfig | None = None,
    ) -> DocumentStructureExtractionWorkflowResult:
        captured["config"] = config
        return make_workflow_result()

    monkeypatch.setattr(
        app_module,
        "run_llama_extract_document_structure_workflow",
        fake_run_llama_extract_document_structure_workflow,
    )

    client = TestClient(app_module.app)

    response = client.post(
        "/document-structure-workflow",
        json={
            "parse_result_payload": {
                "job_id": "parse-job-from-payload",
                "status": "COMPLETED",
            }
        },
    )

    assert response.status_code == 200
    assert response.json()["parse_job_id"] == "parse-job-from-payload"

    config = captured["config"]
    assert config.parse_job_id is None


@pytest.mark.parametrize(
    ("exception", "expected_status_code"),
    [
        (MissingLlamaCloudApiKeyError("missing api key"), 400),
        (MissingLlamaExtractProjectIdError("missing extract project id"), 400),
        (MissingLlamaExtractParseJobIdError("missing parse job id"), 400),
        (LlamaExtractPollingTimeoutError("polling timeout"), 504),
        (LlamaExtractJobFailedError("job failed"), 502),
        (LlamaExtractResponseError("bad upstream response"), 502),
        (LlamaExtractStructuredJsonResultError("bad structured result"), 502),
        (ValueError("invalid merged extraction"), 502),
    ],
)
def test_document_structure_workflow_endpoint_maps_runtime_errors(
    monkeypatch,
    exception: Exception,
    expected_status_code: int,
):
    def fake_run_llama_extract_document_structure_workflow(
        parse_result_payload: dict,
        *,
        config: LlamaExtractDocumentStructureWorkflowRuntimeConfig | None = None,
    ) -> DocumentStructureExtractionWorkflowResult:
        raise exception

    monkeypatch.setattr(
        app_module,
        "run_llama_extract_document_structure_workflow",
        fake_run_llama_extract_document_structure_workflow,
    )

    client = TestClient(app_module.app)

    response = client.post(
        "/document-structure-workflow",
        json={
            "parse_result_payload": {
                "job_id": "parse-job-from-payload",
                "status": "COMPLETED",
            }
        },
    )

    assert response.status_code == expected_status_code
    assert response.json()["detail"]


def test_document_structure_workflow_endpoint_rejects_invalid_request():
    client = TestClient(app_module.app)

    response = client.post(
        "/document-structure-workflow",
        json={
            "parse_result_payload": {},
            "max_attempts": 0,
        },
    )

    assert response.status_code == 422
