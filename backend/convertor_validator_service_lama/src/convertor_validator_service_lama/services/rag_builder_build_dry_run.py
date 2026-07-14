from __future__ import annotations

from convertor_validator_service_lama.core.settings import get_settings
from convertor_validator_service_lama.models.contracts import (
    RagBuilderBuildDryRunResponse,
)
from convertor_validator_service_lama.models.rich_document_package import (
    RichDocumentPackage,
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


_RAG_BUILDER_BUILD_ENDPOINT = "/api/v1/rag/build"


def build_rag_builder_build_dry_run_response(
    request: RichDocumentPackage,
    *,
    document_id: int,
    pkb_code: str = "-1",
    rag_builder_base_url: str | None = None,
) -> RagBuilderBuildDryRunResponse:
    """Build the future RAG Builder request contract without a network call."""

    settings = get_settings()
    base_url = _normalize_base_url(
        rag_builder_base_url or settings.rag_builder_base_url
    )

    downcast_result = downcast_rich_package_to_rag_builder(request)
    buildrequest_payload = build_rag_builder_buildrequest_payload(
        downcast_result.payload.model_dump(mode="json"),
        document_id=document_id,
        pkb_code=pkb_code,
    )

    return RagBuilderBuildDryRunResponse(
        target_url=f"{base_url}{_RAG_BUILDER_BUILD_ENDPOINT}",
        network_call_performed=False,
        payload=buildrequest_payload,
        warnings=[
            warning.model_dump(mode="json")
            for warning in downcast_result.warnings
        ],
        gap_report=build_rag_builder_buildrequest_gap_report(buildrequest_payload),
    )


def _normalize_base_url(value: str) -> str:
    return value.rstrip("/")
