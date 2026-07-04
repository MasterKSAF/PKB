from convertor_validator_service_lama.models.extract_job import (
    ExtractJobResult,
    ExtractJobStatus,
)
from convertor_validator_service_lama.models.parse_job import (
    ParseJobResult,
    ParseJobStatus,
)
from convertor_validator_service_lama.models.rich_document_package import (
    RichDocumentPackage,
    RichDocumentPackageArtifact,
    RichDocumentPackageAssemblyRequest,
    RichDocumentPackageAssemblyResult,
)


def _parse_result() -> ParseJobResult:
    return ParseJobResult(
        job_id="parse-job-123",
        status=ParseJobStatus.completed,
        markdown="# Parsed document",
        raw_response={"job": {"id": "parse-job-123", "status": "COMPLETED"}},
    )


def _extract_result() -> ExtractJobResult:
    return ExtractJobResult(
        job_id="extract-job-sections",
        pass_name="sections",
        status=ExtractJobStatus.completed,
        result={"sections": [{"title": "1. Scope"}]},
        raw_response={"job": {"id": "extract-job-sections", "status": "COMPLETED"}},
    )


def test_rich_document_package_artifact_accepts_content_and_raw_response() -> None:
    artifact = RichDocumentPackageArtifact(
        artifact_key="sections",
        produced_by="sections",
        source="extract_pass",
        content={"sections": [{"title": "1. Scope"}]},
        raw_response={"raw": True},
    )

    assert artifact.artifact_key == "sections"
    assert artifact.produced_by == "sections"
    assert artifact.source == "extract_pass"
    assert artifact.content == {"sections": [{"title": "1. Scope"}]}
    assert artifact.raw_response == {"raw": True}


def test_rich_document_package_holds_parse_and_extract_results() -> None:
    package = RichDocumentPackage(
        parse_job_id="parse-job-123",
        source_pdf_path="document.pdf",
        document_code="GOST-TEST",
        parse_result=_parse_result(),
        extract_results={"sections": _extract_result()},
        artifacts={
            "sections": RichDocumentPackageArtifact(
                artifact_key="sections",
                produced_by="sections",
                source="extract_pass",
                content={"sections": [{"title": "1. Scope"}]},
            )
        },
    )

    assert package.package_name == "rich_document_package.json"
    assert package.parse_job_id == "parse-job-123"
    assert package.source_pdf_path == "document.pdf"
    assert package.document_code == "GOST-TEST"
    assert package.parse_result.job_id == "parse-job-123"
    assert package.extract_results["sections"].job_id == "extract-job-sections"
    assert package.artifacts["sections"].source == "extract_pass"
    assert package.final_correction_policy == "python_validator_assembler_applies_final_corrections"


def test_rich_document_package_assembly_request_defaults_extract_results() -> None:
    request = RichDocumentPackageAssemblyRequest(
        parse_result=_parse_result(),
    )

    assert request.source_pdf_path is None
    assert request.document_code is None
    assert request.extract_results == {}


def test_rich_document_package_assembly_result_reports_artifact_count() -> None:
    package = RichDocumentPackage(
        parse_job_id="parse-job-123",
        parse_result=_parse_result(),
        extract_results={"sections": _extract_result()},
    )

    result = RichDocumentPackageAssemblyResult(
        package=package,
        artifact_count=0,
    )

    assert result.package.parse_job_id == "parse-job-123"
    assert result.artifact_count == 0