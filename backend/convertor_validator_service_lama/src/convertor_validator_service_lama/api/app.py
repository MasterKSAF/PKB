from fastapi import FastAPI, HTTPException

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
    run_all_extract_passes_with_polling,
    run_extract_pass_with_polling,
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


@app.post("/rich-document-package/dry-run", response_model=RichDocumentPackageDryRunResponse)
def rich_document_package_dry_run(request: RichDocumentPackageDryRunRequest) -> RichDocumentPackageDryRunResponse:
    return build_rich_document_package_dry_run_response(request)


@app.get("/rich-document-package/plan", response_model=RichDocumentPackagePlanResponse)
def rich_document_package_plan() -> RichDocumentPackagePlanResponse:
    return build_rich_document_package_plan_response()
