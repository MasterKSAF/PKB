from convertor_validator_service_lama.clients.llama_parse_client import LlamaParseClient
from convertor_validator_service_lama.core.settings import get_settings
from convertor_validator_service_lama.models.contracts import (
    DryRunResponse,
    ExtractPassPlanItem,
    ExtractPassPlanResponse,
    ParseJobDryRunRequest,
    ParseJobDryRunResponse,
    PipelineStep,
    RichDocumentArtifactPlanItem,
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
