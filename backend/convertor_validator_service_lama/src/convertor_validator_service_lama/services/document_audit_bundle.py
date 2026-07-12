from __future__ import annotations

from typing import Any

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


def build_document_conversion_audit_bundle(
    package: RichDocumentPackage,
    *,
    document_id: int,
    pkb_code: str = "-1",
) -> dict[str, Any]:
    downcast_result = downcast_rich_package_to_rag_builder(package)
    rag_builder_payload = build_rag_builder_buildrequest_payload(
        downcast_result.payload.model_dump(mode="json"),
        document_id=document_id,
        pkb_code=pkb_code,
    )

    return {
        "bundle_schema": "document_conversion_audit_bundle_v1",
        "input": _build_input_block(package),
        "service_1_rich": _build_service_1_rich_block(package),
        "service_2_rag_builder": {
            "rag_builder_buildrequest": rag_builder_payload,
            "rag_builder_contract_gap_report": (
                build_rag_builder_buildrequest_gap_report(rag_builder_payload)
            ),
            "warnings": [
                warning.model_dump(mode="json")
                for warning in downcast_result.warnings
            ],
        },
        "llm_audit": {
            "audit_prompt_md": _build_default_llm_audit_prompt(),
            "audit_result_md": None,
        },
    }


def _build_input_block(package: RichDocumentPackage) -> dict[str, Any]:
    return {
        "source_pdf_path": package.source_pdf_path,
        "document_code": package.document_code,
        "parse_job_id": package.parse_job_id,
    }


def _build_service_1_rich_block(package: RichDocumentPackage) -> dict[str, Any]:
    structure = package.document_structure

    return {
        "rich_document_package": package.model_dump(mode="json"),
        "parse_result": package.parse_result.model_dump(mode="json"),
        "extract_artifacts": {
            key: artifact.model_dump(mode="json")
            for key, artifact in package.artifacts.items()
        },
        "asset_references": {
            "images": [
                image.model_dump(mode="json")
                for image in structure.images
            ],
            "tables": [
                table.model_dump(mode="json")
                for table in structure.tables
            ],
            "formulas": [
                formula.model_dump(mode="json")
                for formula in structure.formulas
            ],
        },
        "quality_report": structure.quality_report,
        "correction_proposals": structure.correction_proposals,
        "diagnostics": structure.diagnostics,
    }


def _build_default_llm_audit_prompt() -> str:
    return """# Document conversion audit

Compare the input PDF, rich_document_package.json, and rag_builder_buildrequest.json.

Check:
1. whether document structure was preserved;
2. whether sections, tables, images, formulas, notes, and references are complete;
3. whether source provenance is sufficient for citations;
4. whether the RAG Builder payload loses important rich structure;
5. what should be fixed in Llama extraction;
6. what should be added to RAG Builder.

Return:
- critical issues;
- important but non-blocking issues;
- recommended extraction improvements;
- recommended RAG Builder improvements.
"""
