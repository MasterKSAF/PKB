from fastapi import FastAPI

from convertor_validator_service_lama.models.parse_job import ParseJobPollingConfig, ParseJobResult
from convertor_validator_service_lama.models.contracts import (
    DryRunResponse,
    ExtractPassDryRunRequest,
    ExtractPassDryRunResponse,
    ExtractPassesDryRunRequest,
    ExtractPassesDryRunResponse,
    ExtractPassPlanResponse,
    HealthResponse,
    ParseJobDryRunRequest,
    ParseJobDryRunResponse,
    ParseJobRequest,
    RichDocumentPackageDryRunRequest,
    RichDocumentPackageDryRunResponse,
    RichDocumentPackagePlanResponse,
)
from convertor_validator_service_lama.services.lama_validator_service import (
    build_dry_run_response,
    build_extract_pass_dry_run_response,
    build_extract_passes_dry_run_response,
    build_extract_pass_plan_response,
    build_parse_job_dry_run_response,
    build_rich_document_package_dry_run_response,
    build_rich_document_package_plan_response,
    run_parse_job_with_polling,
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
    return run_parse_job_with_polling(
        source_pdf_path=request.source_pdf_path,
        expand=request.expand,
        polling_config=polling_config,
    )


@app.post("/extract-pass/dry-run", response_model=ExtractPassDryRunResponse)
def extract_pass_dry_run(request: ExtractPassDryRunRequest) -> ExtractPassDryRunResponse:
    return build_extract_pass_dry_run_response(request)


@app.post("/extract-passes/dry-run", response_model=ExtractPassesDryRunResponse)
def extract_passes_dry_run(request: ExtractPassesDryRunRequest) -> ExtractPassesDryRunResponse:
    return build_extract_passes_dry_run_response(request)


@app.get("/extract-passes/plan", response_model=ExtractPassPlanResponse)
def extract_passes_plan() -> ExtractPassPlanResponse:
    return build_extract_pass_plan_response()


@app.post("/rich-document-package/dry-run", response_model=RichDocumentPackageDryRunResponse)
def rich_document_package_dry_run(request: RichDocumentPackageDryRunRequest) -> RichDocumentPackageDryRunResponse:
    return build_rich_document_package_dry_run_response(request)


@app.get("/rich-document-package/plan", response_model=RichDocumentPackagePlanResponse)
def rich_document_package_plan() -> RichDocumentPackagePlanResponse:
    return build_rich_document_package_plan_response()
