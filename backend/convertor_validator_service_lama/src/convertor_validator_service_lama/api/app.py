from fastapi import FastAPI

from convertor_validator_service_lama.models.contracts import DryRunResponse, HealthResponse
from convertor_validator_service_lama.services.lama_validator_service import build_dry_run_response


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
