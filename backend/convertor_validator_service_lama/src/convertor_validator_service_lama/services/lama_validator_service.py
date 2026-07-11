from collections.abc import Sequence

from convertor_validator_service_lama.clients.llama_extract_client import LlamaExtractClient
from convertor_validator_service_lama.clients.llama_extract_rest_client import LlamaExtractRestClient, MissingLlamaExtractProjectIdError
from convertor_validator_service_lama.clients.llama_parse_client import LlamaParseClient
from convertor_validator_service_lama.clients.llama_parse_rest_client import LlamaParseRestClient
from convertor_validator_service_lama.core.settings import get_settings
from convertor_validator_service_lama.models.extract_job import ExtractJobPollingConfig, ExtractJobResult, ExtractPassRequest
from convertor_validator_service_lama.models.parse_job import ParseJobPollingConfig, ParseJobResult
from convertor_validator_service_lama.models.contracts import (
    DryRunResponse,
    ExtractPassPlanItem,
    ExtractPassPlanResponse,
    ExtractPassDryRunRequest,
    ExtractPassDryRunResponse,
    ExtractPassesDryRunRequest,
    ExtractPassesDryRunResponse,
    ParseJobDryRunRequest,
    ParseJobDryRunResponse,
    PipelineStep,
    RichDocumentArtifactPlanItem,
    RichDocumentPackageDryRunRequest,
    RichDocumentPackageDryRunResponse,
    RichDocumentPackagePlanResponse,
)


def build_dry_run_response() -> DryRunResponse:
    steps = [
        PipelineStep(name="llama_parse_source_pdf", description="LlamaParse processes the original source PDF."),
        PipelineStep(name="store_parse_job_id", description="Store parse_job_id and raw parser artifacts."),
        PipelineStep(name="llama_extract_by_parse_job_id", description="Run LlamaExtract passes by parse_job_id.", uses_parse_job_id=True),
        PipelineStep(name="python_validator_assembler", description="Build rich_document_package.json and apply corrections in Python.", uses_parse_job_id=True)
    ]
    return DryRunResponse(planned_steps=steps)


def build_parse_job_dry_run_response(request: ParseJobDryRunRequest) -> ParseJobDryRunResponse:
    client = LlamaParseClient(get_settings())
    parse_payload = client.build_parse_payload(request.source_pdf_path)
    return ParseJobDryRunResponse(
        source_pdf_path=request.source_pdf_path,
        parse_payload=parse_payload,
    )


def build_extract_pass_dry_run_response(
    request: ExtractPassDryRunRequest,
) -> ExtractPassDryRunResponse:
    client = LlamaExtractClient(get_settings())
    extract_payload = client.build_extract_payload(
        parse_job_id=request.parse_job_id,
        pass_name=request.pass_name,
    )
    return ExtractPassDryRunResponse(
        parse_job_id=request.parse_job_id,
        pass_name=request.pass_name,
        extract_payload=extract_payload,
    )


def build_extract_passes_dry_run_response(
    request: ExtractPassesDryRunRequest,
) -> ExtractPassesDryRunResponse:
    client = LlamaExtractClient(get_settings())
    pass_plan = build_extract_pass_plan_response()
    extract_payloads = [
        client.build_extract_payload(
            parse_job_id=request.parse_job_id,
            pass_name=item.name,
        )
        for item in pass_plan.passes
    ]
    return ExtractPassesDryRunResponse(
        parse_job_id=request.parse_job_id,
        extract_payloads=extract_payloads,
    )


def build_extract_pass_plan_response() -> ExtractPassPlanResponse:
    passes = [
        ExtractPassPlanItem(name="document_boundaries", output_key="document_boundaries"),
        ExtractPassPlanItem(name="nested_documents", output_key="nested_documents"),
        ExtractPassPlanItem(name="title_metadata", output_key="title_metadata"),
        ExtractPassPlanItem(name="table_of_contents", output_key="table_of_contents"),
        ExtractPassPlanItem(name="table_of_contents_blocks", output_key="table_of_contents_blocks"),
        ExtractPassPlanItem(name="sections", output_key="sections"),
        ExtractPassPlanItem(name="tables", output_key="tables"),
        ExtractPassPlanItem(name="images", output_key="images"),
        ExtractPassPlanItem(name="formulas", output_key="formulas"),
        ExtractPassPlanItem(name="notes", output_key="notes"),
        ExtractPassPlanItem(name="references", output_key="references"),
        ExtractPassPlanItem(name="cross_references", output_key="cross_references"),
        ExtractPassPlanItem(name="validation_critic", output_key="validation_critic")
    ]
    return ExtractPassPlanResponse(passes=passes)


def build_rich_document_package_dry_run_response(
    request: RichDocumentPackageDryRunRequest,
) -> RichDocumentPackageDryRunResponse:
    parse_request = ParseJobDryRunRequest(
        source_pdf_path=request.source_pdf_path,
        document_code=request.document_code,
    )
    parse_response = build_parse_job_dry_run_response(parse_request)
    extract_request = ExtractPassesDryRunRequest(
        parse_job_id=parse_response.expected_parse_job_id,
    )
    extract_response = build_extract_passes_dry_run_response(extract_request)
    return RichDocumentPackageDryRunResponse(
        source_pdf_path=request.source_pdf_path,
        parse_job_id=parse_response.expected_parse_job_id,
        parse_payload=parse_response.parse_payload,
        extract_payloads=extract_response.extract_payloads,
    )


def build_rich_document_package_plan_response() -> RichDocumentPackagePlanResponse:
    artifacts = [
        RichDocumentArtifactPlanItem(artifact_key="parse_job_id", produced_by="llama_parse_source_pdf", source="parse_job_id"),
        RichDocumentArtifactPlanItem(artifact_key="raw_artifacts", produced_by="llama_parse_source_pdf", source="parse_job_id"),
        RichDocumentArtifactPlanItem(artifact_key="document_boundaries", produced_by="document_boundaries", source="extract_pass"),
        RichDocumentArtifactPlanItem(artifact_key="nested_documents", produced_by="nested_documents", source="extract_pass"),
        RichDocumentArtifactPlanItem(artifact_key="document_structure_extraction", produced_by="document_structure_extraction_workflow", source="python_validator"),
        RichDocumentArtifactPlanItem(artifact_key="title_metadata", produced_by="title_metadata", source="extract_pass"),
        RichDocumentArtifactPlanItem(artifact_key="table_of_contents", produced_by="table_of_contents", source="extract_pass"),
        RichDocumentArtifactPlanItem(artifact_key="table_of_contents_blocks", produced_by="table_of_contents_blocks", source="extract_pass"),
        RichDocumentArtifactPlanItem(artifact_key="sections", produced_by="sections", source="extract_pass"),
        RichDocumentArtifactPlanItem(artifact_key="tables", produced_by="tables", source="extract_pass"),
        RichDocumentArtifactPlanItem(artifact_key="images", produced_by="images", source="extract_pass"),
        RichDocumentArtifactPlanItem(artifact_key="formulas", produced_by="formulas", source="extract_pass"),
        RichDocumentArtifactPlanItem(artifact_key="notes", produced_by="notes", source="extract_pass"),
        RichDocumentArtifactPlanItem(artifact_key="references", produced_by="references", source="extract_pass"),
        RichDocumentArtifactPlanItem(artifact_key="cross_references", produced_by="cross_references", source="extract_pass"),
        RichDocumentArtifactPlanItem(artifact_key="quality_report", produced_by="python_validator_critic", source="python_validator"),
        RichDocumentArtifactPlanItem(artifact_key="correction_proposals", produced_by="python_validator_critic", source="python_validator")
    ]
    return RichDocumentPackagePlanResponse(artifacts=artifacts)

def run_parse_job_with_polling(
    source_pdf_path: str,
    expand: Sequence[str] | None = None,
    polling_config: ParseJobPollingConfig | None = None,
    client: LlamaParseRestClient | None = None,
) -> ParseJobResult:
    parse_client = client or LlamaParseRestClient(get_settings())
    should_close_client = client is None

    try:
        file_id = parse_client.upload_file(source_pdf_path)
        submit_response = parse_client.start_parse_job(file_id=file_id)
        return parse_client.poll_parse_job(
            job_id=submit_response.job_id,
            expand=expand,
            config=polling_config,
        )
    finally:
        if should_close_client:
            parse_client.close()





_NESTED_DOCUMENTS_EXTRACTION_INSTRUCTIONS = (
    "Extract embedded, appended or nested documents from the parsed technical "
    "document. Preserve each nested document as a separate object. Do not "
    "flatten nested document namespaces into the parent document. Capture "
    "nested_document_id, document_code, title, page_start, page_end and "
    "parent_boundary_id when available."
)


def _default_nested_documents_extraction_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "nested_documents": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "nested_document_id": {"type": "string"},
                        "document_code": {"type": "string"},
                        "title": {"type": "string"},
                        "page_start": {"type": "integer"},
                        "page_end": {"type": "integer"},
                        "parent_boundary_id": {"type": "string"},
                    },
                    "required": ["title"],
                },
            },
        },
        "required": ["nested_documents"],
    }

_TOC_BLOCKS_EXTRACTION_INSTRUCTIONS = (
    "Extract all table-of-contents blocks from the parsed technical document. "
    "Preserve separate TOC blocks as separate objects. Do not merge the main "
    "document TOC with appendix or nested-document TOCs. Each TOC block should "
    "contain toc_id, title, namespace_id, page_start, page_end and items. Each "
    "item should preserve title, level, page, path and target_section_id when "
    "available."
)


def _default_table_of_contents_blocks_extraction_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "table_of_contents_blocks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "toc_id": {"type": "string"},
                        "title": {"type": "string"},
                        "namespace_id": {"type": "string"},
                        "page_start": {"type": "integer"},
                        "page_end": {"type": "integer"},
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "item_id": {"type": "string"},
                                    "title": {"type": "string"},
                                    "level": {"type": "integer"},
                                    "page": {"type": "integer"},
                                    "path": {"type": "string"},
                                    "target_section_id": {"type": "string"},
                                },
                                "required": ["title"],
                            },
                        },
                    },
                    "required": ["toc_id", "items"],
                },
            },
        },
        "required": ["table_of_contents_blocks"],
    }

_NOTES_EXTRACTION_INSTRUCTIONS = (
    "Extract notes, remarks, footnotes and normative document notes from the "
    "parsed technical document. Preserve the original note text exactly. "
    "Return only actual notes; do not use this pass for normal body clauses, "
    "tables, figures, formulas or external normative references."
)


def _default_notes_extraction_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "notes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "note_id": {"type": "string"},
                        "namespace_id": {"type": "string"},
                        "section_id": {"type": "string"},
                        "text": {"type": "string"},
                        "page": {"type": "integer"},
                        "bbox": {
                            "type": "array",
                            "items": {"type": "number"},
                        },
                    },
                    "required": ["text"],
                },
            },
        },
        "required": ["notes"],
    }

_REFERENCES_EXTRACTION_INSTRUCTIONS = (
    "Extract external normative document references from the parsed technical "
    "document. Focus on references to GOST, OST, ISO, ASTM, DNV and similar "
    "external standards. Preserve the original reference text exactly. If the "
    "text contains a document range such as GOST 20862-81 - GOST 20867-81, "
    "keep the full range in reference_text and put the best detected target "
    "document or range into target_document_code. Do not use this pass for "
    "internal same-document links; those belong to cross_references."
)


def _default_references_extraction_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "references": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "reference_id": {"type": "string"},
                        "namespace_id": {"type": "string"},
                        "section_id": {"type": "string"},
                        "reference_text": {"type": "string"},
                        "target_document_code": {"type": "string"},
                        "target_clause": {"type": "string"},
                        "reference_type": {"type": "string"},
                        "page": {"type": "integer"},
                        "bbox": {
                            "type": "array",
                            "items": {"type": "number"},
                        },
                    },
                    "required": ["reference_text"],
                },
            },
        },
        "required": ["references"],
    }


def _default_extraction_schema(
    pass_name: LlamaExtractPassName,
) -> dict[str, object]:
    if pass_name == "nested_documents":
        return _default_nested_documents_extraction_schema()

    if pass_name == "table_of_contents_blocks":
        return _default_table_of_contents_blocks_extraction_schema()

    if pass_name == "notes":
        return _default_notes_extraction_schema()

    if pass_name == "references":
        return _default_references_extraction_schema()

    return {}


def _default_instructions(pass_name: LlamaExtractPassName) -> str | None:
    if pass_name == "nested_documents":
        return _NESTED_DOCUMENTS_EXTRACTION_INSTRUCTIONS

    if pass_name == "table_of_contents_blocks":
        return _TOC_BLOCKS_EXTRACTION_INSTRUCTIONS

    if pass_name == "notes":
        return _NOTES_EXTRACTION_INSTRUCTIONS

    if pass_name == "references":
        return _REFERENCES_EXTRACTION_INSTRUCTIONS

    return None


def _resolve_extraction_schema(
    pass_name: LlamaExtractPassName,
    extraction_schema: dict[str, object] | None,
) -> dict[str, object]:
    if extraction_schema:
        return extraction_schema

    return _default_extraction_schema(pass_name)


def _resolve_instructions(
    pass_name: LlamaExtractPassName,
    instructions: str | None,
) -> str | None:
    if instructions:
        return instructions

    return _default_instructions(pass_name)


def run_extract_pass_with_polling(
    parse_job_id: str,
    pass_name: LlamaExtractPassName,
    extraction_schema: dict[str, object] | None = None,
    instructions: str | None = None,
    schema_name: str | None = None,
    expand: Sequence[str] | None = None,
    polling_config: ExtractJobPollingConfig | None = None,
    client: LlamaExtractRestClient | None = None,
) -> ExtractJobResult:
    settings = get_settings()
    project_id = settings.extract_project_id

    if not project_id:
        raise MissingLlamaExtractProjectIdError("LAMA_EXTRACT_PROJECT_ID is required for LlamaExtract network calls.")

    extract_client = client or LlamaExtractRestClient(settings)
    should_close_client = client is None
    resolved_extraction_schema = _resolve_extraction_schema(
        pass_name,
        extraction_schema,
    )
    resolved_instructions = _resolve_instructions(pass_name, instructions)

    try:
        request = ExtractPassRequest(
            parse_job_id=parse_job_id,
            pass_name=pass_name,
            project_id=project_id,
            schema_name=schema_name,
            extraction_schema=resolved_extraction_schema,
            instructions=resolved_instructions,
        )
        submit_response = extract_client.start_extract_job(request)
        return extract_client.poll_extract_job(
            job_id=submit_response.job_id,
            pass_name=pass_name,
            project_id=project_id,
            expand=expand,
            config=polling_config,
        )
    finally:
        if should_close_client:
            extract_client.close()

def run_all_extract_passes_with_polling(
    parse_job_id: str,
    extraction_schemas: dict[str, dict[str, object]] | None = None,
    instructions_by_pass: dict[str, str] | None = None,
    schema_names_by_pass: dict[str, str] | None = None,
    expand: Sequence[str] | None = None,
    polling_config: ExtractJobPollingConfig | None = None,
    client: LlamaExtractRestClient | None = None,
) -> dict[str, ExtractJobResult]:
    results: dict[str, ExtractJobResult] = {}
    pass_plan = build_extract_pass_plan_response()

    for pass_item in pass_plan.passes:
        pass_name = pass_item.name
        result = run_extract_pass_with_polling(
            parse_job_id=parse_job_id,
            pass_name=pass_name,
            extraction_schema=(extraction_schemas or {}).get(pass_name),
            instructions=(instructions_by_pass or {}).get(pass_name),
            schema_name=(schema_names_by_pass or {}).get(pass_name),
            expand=expand,
            polling_config=polling_config,
            client=client,
        )
        results[pass_name] = result

    return results
