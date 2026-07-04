from convertor_validator_service_lama.models.extract_job import (
    ExtractJobResult,
    ExtractJobStatus,
)
from convertor_validator_service_lama.models.parse_job import (
    ParseJobResult,
    ParseJobStatus,
)
from convertor_validator_service_lama.models.rich_document_package import (
    RichDocumentPackageAssemblyRequest,
)
from convertor_validator_service_lama.services.rich_document_package_assembler import (
    assemble_rich_document_package,
)


def _parse_result() -> ParseJobResult:
    return ParseJobResult(
        job_id="parse-job-123",
        status=ParseJobStatus.completed,
        markdown="# Parsed document",
        items=[{"type": "heading", "value": "1. Scope"}],
        metadata={"page_count": 2},
        job_metadata={"duration_seconds": 10},
        raw_response={
            "job": {"id": "parse-job-123", "status": "COMPLETED"},
            "result": {"markdown": "# Parsed document"},
        },
    )


def _extract_result(pass_name: str, result: dict) -> ExtractJobResult:
    return ExtractJobResult(
        job_id=f"extract-job-{pass_name}",
        pass_name=pass_name,
        status=ExtractJobStatus.completed,
        result=result,
        raw_response={
            "job": {"id": f"extract-job-{pass_name}", "status": "COMPLETED"},
            "extract_result": result,
        },
    )


def test_assemble_rich_document_package_builds_parse_artifacts() -> None:
    result = assemble_rich_document_package(
        RichDocumentPackageAssemblyRequest(
            source_pdf_path="document.pdf",
            document_code="GOST-TEST",
            parse_result=_parse_result(),
        )
    )

    package = result.package

    assert package.package_name == "rich_document_package.json"
    assert package.parse_job_id == "parse-job-123"
    assert package.source_pdf_path == "document.pdf"
    assert package.document_code == "GOST-TEST"

    assert package.artifacts["parse_raw_response"].source == "parse_result"
    assert package.artifacts["markdown"].content == "# Parsed document"
    assert package.artifacts["items"].content == [{"type": "heading", "value": "1. Scope"}]
    assert package.artifacts["metadata"].content == {"page_count": 2}
    assert package.artifacts["job_metadata"].content == {"duration_seconds": 10}

    assert result.artifact_count == 5


def test_assemble_rich_document_package_adds_extract_pass_artifacts() -> None:
    sections = _extract_result(
        "sections",
        {"sections": [{"title": "1. Scope"}]},
    )
    tables = _extract_result(
        "tables",
        {"tables": [{"caption": "Table 1"}]},
    )

    result = assemble_rich_document_package(
        RichDocumentPackageAssemblyRequest(
            parse_result=_parse_result(),
            extract_results={
                "sections": sections,
                "tables": tables,
            },
        )
    )

    package = result.package

    assert package.extract_results["sections"].job_id == "extract-job-sections"
    assert package.extract_results["tables"].job_id == "extract-job-tables"

    assert package.artifacts["sections"].source == "extract_pass"
    assert package.artifacts["sections"].produced_by == "sections"
    assert package.artifacts["sections"].content == {"sections": [{"title": "1. Scope"}]}

    assert package.artifacts["tables"].source == "extract_pass"
    assert package.artifacts["tables"].produced_by == "tables"
    assert package.artifacts["tables"].content == {"tables": [{"caption": "Table 1"}]}

    assert result.artifact_count == 7


def test_assemble_rich_document_package_extracts_validation_critic_outputs() -> None:
    validation_critic = _extract_result(
        "validation_critic",
        {
            "quality_report": {"status": "needs_review"},
            "correction_proposals": [{"field": "title", "proposal": "fix spacing"}],
        },
    )

    result = assemble_rich_document_package(
        RichDocumentPackageAssemblyRequest(
            parse_result=_parse_result(),
            extract_results={"validation_critic": validation_critic},
        )
    )

    package = result.package

    assert package.artifacts["validation_critic"].source == "extract_pass"

    assert package.artifacts["quality_report"].source == "python_validator"
    assert package.artifacts["quality_report"].produced_by == "validation_critic"
    assert package.artifacts["quality_report"].content == {"status": "needs_review"}

    assert package.artifacts["correction_proposals"].source == "python_validator"
    assert package.artifacts["correction_proposals"].produced_by == "validation_critic"
    assert package.artifacts["correction_proposals"].content == [
        {"field": "title", "proposal": "fix spacing"}
    ]

    assert result.artifact_count == 8


def test_assemble_rich_document_package_keeps_final_correction_policy() -> None:
    result = assemble_rich_document_package(
        RichDocumentPackageAssemblyRequest(
            parse_result=_parse_result(),
        )
    )

    assert (
        result.package.final_correction_policy
        == "python_validator_assembler_applies_final_corrections"
    )