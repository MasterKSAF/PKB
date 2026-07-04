from collections.abc import Sequence

from convertor_validator_service_lama.clients.llama_extract_client import LlamaExtractClient
from convertor_validator_service_lama.clients.llama_parse_client import LlamaParseClient
from convertor_validator_service_lama.clients.llama_parse_rest_client import LlamaParseRestClient
from convertor_validator_service_lama.core.settings import get_settings
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
        ExtractPassPlanItem(name="title_metadata", output_key="title_metadata"),
        ExtractPassPlanItem(name="table_of_contents", output_key="table_of_contents"),
        ExtractPassPlanItem(name="sections", output_key="sections"),
        ExtractPassPlanItem(name="tables", output_key="tables"),
        ExtractPassPlanItem(name="images", output_key="images"),
        ExtractPassPlanItem(name="formulas", output_key="formulas"),
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
        RichDocumentArtifactPlanItem(artifact_key="title_metadata", produced_by="title_metadata", source="extract_pass"),
        RichDocumentArtifactPlanItem(artifact_key="table_of_contents", produced_by="table_of_contents", source="extract_pass"),
        RichDocumentArtifactPlanItem(artifact_key="sections", produced_by="sections", source="extract_pass"),
        RichDocumentArtifactPlanItem(artifact_key="tables", produced_by="tables", source="extract_pass"),
        RichDocumentArtifactPlanItem(artifact_key="images", produced_by="images", source="extract_pass"),
        RichDocumentArtifactPlanItem(artifact_key="formulas", produced_by="formulas", source="extract_pass"),
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
