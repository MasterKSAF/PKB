from fastapi import FastAPI, HTTPException
from pydantic import ValidationError

from convertor_validator_service_lama.clients.llama_cloud_boundary import MissingLlamaCloudApiKeyError
from convertor_validator_service_lama.clients.llama_extract_rest_client import (
    LlamaExtractJobFailedError,
    LlamaExtractPollingTimeoutError,
    LlamaExtractResponseError,
    MissingLlamaExtractProjectIdError,
)
from convertor_validator_service_lama.clients.llama_parse_rest_client import (
    LlamaParseJobFailedError,
    LlamaParsePollingTimeoutError,
    LlamaParseResponseError,
)
from convertor_validator_service_lama.models.extract_job import ExtractJobPollingConfig, ExtractJobResult
from convertor_validator_service_lama.models.parse_job import ParseJobPollingConfig, ParseJobResult
from convertor_validator_service_lama.models.contracts import (
    DocumentStructureWorkflowDryRunRequest,
    DocumentStructureWorkflowDryRunResponse,
    DocumentStructureWorkflowRunRequest,
    DocumentStructureWorkflowRunResponse,
    DryRunResponse,
    ExtractPassDryRunRequest,
    ExtractPassDryRunResponse,
    ExtractPassRunRequest,
    ExtractPassesDryRunRequest,
    ExtractPassesDryRunResponse,
    ExtractPassesRunRequest,
    ExtractPassPlanResponse,
    HealthResponse,
    ParseJobDryRunRequest,
    ParseJobDryRunResponse,
    ParseJobRequest,
    RagBuilderBuildDryRunResponse,
    RichDocumentPackageDryRunRequest,
    RichDocumentPackageDryRunResponse,
    RichDocumentPackagePlanResponse,
)
from convertor_validator_service_lama.services.document_structure_workflow_dry_run import (
    build_document_structure_workflow_dry_run_response,
)
from convertor_validator_service_lama.services.document_structure_workflow_runtime import (
    LlamaExtractDocumentStructureWorkflowRuntimeConfig,
    run_llama_extract_document_structure_workflow,
)
from convertor_validator_service_lama.services.document_audit_bundle import (
    build_document_conversion_audit_bundle,
)
from convertor_validator_service_lama.services.llama_extract_structured_json_backend import (
    LlamaExtractStructuredJsonResultError,
    MissingLlamaExtractParseJobIdError,
)
from convertor_validator_service_lama.services.lama_validator_service import (
    build_dry_run_response,
    build_extract_pass_dry_run_response,
    build_extract_passes_dry_run_response,
    build_extract_pass_plan_response,
    build_parse_job_dry_run_response,
    build_rich_document_package_dry_run_response,
    build_rich_document_package_plan_response,
    run_all_extract_passes_with_polling,
    run_extract_pass_with_polling,
    run_parse_job_with_polling,
)


from convertor_validator_service_lama.models.rag_builder_downcast import (
    RagBuilderDowncastResult,
)
from convertor_validator_service_lama.models.rich_document_package import (
    RichDocumentPackage,
    RichDocumentPackageAssemblyRequest,
    RichDocumentPackageAssemblyResult,
)
from convertor_validator_service_lama.services.rag_builder_buildrequest_adapter import (
    build_rag_builder_buildrequest_payload,
)
from convertor_validator_service_lama.services.rag_builder_contract_audit import (
    build_rag_builder_buildrequest_gap_report,
)
from convertor_validator_service_lama.services.rag_builder_downcast_service import (
    downcast_rich_package_to_rag_builder,
)
from convertor_validator_service_lama.services.rag_builder_build_dry_run import (
    build_rag_builder_build_dry_run_response,
)
from convertor_validator_service_lama.services.rich_document_package_assembler import (
    assemble_rich_document_package,
)


app = FastAPI(
    title="convertor_validator_service_lama",
    version="0.1.0",
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@app.get("/dry-run", response_model=DryRunResponse)
def dry_run() -> DryRunResponse:
    return build_dry_run_response()


@app.post("/parse-job/dry-run", response_model=ParseJobDryRunResponse)
def parse_job_dry_run(request: ParseJobDryRunRequest) -> ParseJobDryRunResponse:
    return build_parse_job_dry_run_response(request)


@app.post("/parse-job", response_model=ParseJobResult)
def parse_job(request: ParseJobRequest) -> ParseJobResult:
    polling_config = ParseJobPollingConfig(
        max_attempts=request.max_attempts,
        interval_seconds=request.interval_seconds,
    )

    try:
        return run_parse_job_with_polling(
            source_pdf_path=request.source_pdf_path,
            expand=request.expand,
            polling_config=polling_config,
        )
    except MissingLlamaCloudApiKeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Source PDF was not found: {exc}") from exc
    except LlamaParsePollingTimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except LlamaParseJobFailedError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except LlamaParseResponseError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc




@app.post("/extract-pass", response_model=ExtractJobResult)
def extract_pass(request: ExtractPassRunRequest) -> ExtractJobResult:
    polling_config = ExtractJobPollingConfig(
        max_attempts=request.max_attempts,
        interval_seconds=request.interval_seconds,
    )

    try:
        return run_extract_pass_with_polling(
            parse_job_id=request.parse_job_id,
            pass_name=request.pass_name,
            extraction_schema=request.extraction_schema,
            instructions=request.instructions,
            schema_name=request.schema_name,
            expand=request.expand,
            polling_config=polling_config,
        )
    except (MissingLlamaCloudApiKeyError, MissingLlamaExtractProjectIdError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LlamaExtractPollingTimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except LlamaExtractJobFailedError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except LlamaExtractResponseError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

@app.post("/extract-pass/dry-run", response_model=ExtractPassDryRunResponse)
def extract_pass_dry_run(request: ExtractPassDryRunRequest) -> ExtractPassDryRunResponse:
    return build_extract_pass_dry_run_response(request)




@app.post("/extract-passes", response_model=dict[str, ExtractJobResult])
def extract_passes(request: ExtractPassesRunRequest) -> dict[str, ExtractJobResult]:
    polling_config = ExtractJobPollingConfig(
        max_attempts=request.max_attempts,
        interval_seconds=request.interval_seconds,
    )

    try:
        return run_all_extract_passes_with_polling(
            parse_job_id=request.parse_job_id,
            extraction_schemas=request.extraction_schemas,
            instructions_by_pass=request.instructions_by_pass,
            schema_names_by_pass=request.schema_names_by_pass,
            expand=request.expand,
            polling_config=polling_config,
        )
    except (MissingLlamaCloudApiKeyError, MissingLlamaExtractProjectIdError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LlamaExtractPollingTimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except LlamaExtractJobFailedError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except LlamaExtractResponseError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

@app.post("/extract-passes/dry-run", response_model=ExtractPassesDryRunResponse)
def extract_passes_dry_run(request: ExtractPassesDryRunRequest) -> ExtractPassesDryRunResponse:
    return build_extract_passes_dry_run_response(request)


@app.get("/extract-passes/plan", response_model=ExtractPassPlanResponse)
def extract_passes_plan() -> ExtractPassPlanResponse:
    return build_extract_pass_plan_response()



@app.post(
    "/document-structure-workflow",
    response_model=DocumentStructureWorkflowRunResponse,
)
def document_structure_workflow(
    request: DocumentStructureWorkflowRunRequest,
) -> DocumentStructureWorkflowRunResponse:
    polling_config = ExtractJobPollingConfig(
        max_attempts=request.max_attempts,
        interval_seconds=request.interval_seconds,
    )

    try:
        result = run_llama_extract_document_structure_workflow(
            request.parse_result_payload,
            config=LlamaExtractDocumentStructureWorkflowRuntimeConfig(
                parse_job_id=request.parse_job_id,
                document_hint=request.document_hint,
                pass_name=request.pass_name,
                schema_name=request.schema_name,
                expand=request.expand,
                polling_config=polling_config,
                include_metadata_in_instructions=(
                    request.include_metadata_in_instructions
                ),
                overview_max_items=request.overview_max_items,
                scope_max_items=request.scope_max_items,
                scope_max_window_items=request.scope_max_window_items,
                scope_overlap_items=request.scope_overlap_items,
                item_text_chars=request.item_text_chars,
                markdown_excerpt_chars=request.markdown_excerpt_chars,
            ),
        )
    except (
        MissingLlamaCloudApiKeyError,
        MissingLlamaExtractProjectIdError,
        MissingLlamaExtractParseJobIdError,
    ) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LlamaExtractPollingTimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except LlamaExtractJobFailedError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except (
        LlamaExtractResponseError,
        LlamaExtractStructuredJsonResultError,
        ValidationError,
        ValueError,
    ) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return _build_document_structure_workflow_run_response(
        request=request,
        result=result,
    )


@app.post(
    "/document-structure-workflow/dry-run",
    response_model=DocumentStructureWorkflowDryRunResponse,
)
def document_structure_workflow_dry_run(
    request: DocumentStructureWorkflowDryRunRequest,
) -> DocumentStructureWorkflowDryRunResponse:
    return build_document_structure_workflow_dry_run_response(request)


@app.post("/rich-document-package", response_model=RichDocumentPackageAssemblyResult)
def rich_document_package(
    request: RichDocumentPackageAssemblyRequest,
) -> RichDocumentPackageAssemblyResult:
    return assemble_rich_document_package(request)


@app.post("/rag-builder-payload", response_model=RagBuilderDowncastResult)
def rag_builder_payload(request: RichDocumentPackage) -> RagBuilderDowncastResult:
    return downcast_rich_package_to_rag_builder(request)


@app.post("/rag-builder-buildrequest")
def rag_builder_buildrequest(
    request: RichDocumentPackage,
    document_id: int,
    pkb_code: str = "-1",
) -> dict[str, object]:
    downcast_result = downcast_rich_package_to_rag_builder(request)
    buildrequest_payload = build_rag_builder_buildrequest_payload(
        downcast_result.payload.model_dump(mode="json"),
        document_id=document_id,
        pkb_code=pkb_code,
    )

    return {
        "payload": buildrequest_payload,
        "warnings": downcast_result.warnings,
        "gap_report": build_rag_builder_buildrequest_gap_report(buildrequest_payload),
    }


@app.post("/document-audit-bundle")
def document_audit_bundle(
    request: RichDocumentPackage,
    document_id: int,
    pkb_code: str = "-1",
) -> dict[str, object]:
    return build_document_conversion_audit_bundle(
        request,
        document_id=document_id,
        pkb_code=pkb_code,
    )


@app.post(
    "/rag-builder-build/dry-run",
    response_model=RagBuilderBuildDryRunResponse,
)
def rag_builder_build_dry_run(
    request: RichDocumentPackage,
    document_id: int,
    pkb_code: str = "-1",
    rag_builder_base_url: str | None = None,
) -> RagBuilderBuildDryRunResponse:
    return build_rag_builder_build_dry_run_response(
        request,
        document_id=document_id,
        pkb_code=pkb_code,
        rag_builder_base_url=rag_builder_base_url,
    )


@app.post("/rich-document-package/dry-run", response_model=RichDocumentPackageDryRunResponse)
def rich_document_package_dry_run(request: RichDocumentPackageDryRunRequest) -> RichDocumentPackageDryRunResponse:
    return build_rich_document_package_dry_run_response(request)


@app.get("/rich-document-package/plan", response_model=RichDocumentPackagePlanResponse)
def rich_document_package_plan() -> RichDocumentPackagePlanResponse:
    return build_rich_document_package_plan_response()

def _build_document_structure_workflow_run_response(
    *,
    request: DocumentStructureWorkflowRunRequest,
    result,
) -> DocumentStructureWorkflowRunResponse:
    merged = result.merged_extraction
    diagnostics = merged.diagnostics

    return DocumentStructureWorkflowRunResponse(
        parse_job_id=_first_str(
            request.parse_job_id,
            request.parse_result_payload.get("job_id"),
        ),
        document_profile=_enum_or_str(merged.document_profile),
        page_count=merged.page_count,
        numbering_scopes_count=len(merged.numbering_scopes),
        item_classifications_count=len(merged.item_classifications),
        sections_count=len(merged.sections),
        issues_count=len(merged.issues),
        scope_inputs_count=result.scope_inputs_count,
        scope_extractions_count=result.scope_extractions_count,
        overview_items_preview_count=_as_int(
            diagnostics.get("workflow_overview_items_preview_count")
        ),
        overview_page_overview_count=_as_int(
            diagnostics.get("workflow_page_overview_count")
        ),
        scope_stage_ids=[
            item
            for item in diagnostics.get("workflow_scope_stage_ids", [])
            if isinstance(item, str)
        ],
        merged_extraction=merged.model_dump(mode="json"),
    )


def _enum_or_str(value) -> str:
    enum_value = getattr(value, "value", None)
    if isinstance(enum_value, str):
        return enum_value

    if isinstance(value, str):
        return value

    return str(value)


def _as_int(value) -> int:
    if isinstance(value, bool):
        return 0

    if isinstance(value, int):
        return value

    return 0


def _first_str(*values) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()

    return None
