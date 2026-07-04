from convertor_validator_service_lama.models.rich_document_package import (
    RichDocumentPackage,
    RichDocumentPackageArtifact,
    RichDocumentPackageAssemblyRequest,
    RichDocumentPackageAssemblyResult,
)


def assemble_rich_document_package(
    request: RichDocumentPackageAssemblyRequest,
) -> RichDocumentPackageAssemblyResult:
    artifacts: dict[str, RichDocumentPackageArtifact] = {}

    parse_result = request.parse_result

    artifacts["parse_raw_response"] = RichDocumentPackageArtifact(
        artifact_key="parse_raw_response",
        produced_by="llama_parse_source_pdf",
        source="parse_result",
        content=parse_result.raw_response,
        raw_response=parse_result.raw_response,
    )

    if parse_result.markdown is not None:
        artifacts["markdown"] = RichDocumentPackageArtifact(
            artifact_key="markdown",
            produced_by="llama_parse_source_pdf",
            source="parse_result",
            content=parse_result.markdown,
            raw_response=parse_result.raw_response,
        )

    if parse_result.items:
        artifacts["items"] = RichDocumentPackageArtifact(
            artifact_key="items",
            produced_by="llama_parse_source_pdf",
            source="parse_result",
            content=parse_result.items,
            raw_response=parse_result.raw_response,
        )

    if parse_result.metadata:
        artifacts["metadata"] = RichDocumentPackageArtifact(
            artifact_key="metadata",
            produced_by="llama_parse_source_pdf",
            source="parse_result",
            content=parse_result.metadata,
            raw_response=parse_result.raw_response,
        )

    if parse_result.job_metadata:
        artifacts["job_metadata"] = RichDocumentPackageArtifact(
            artifact_key="job_metadata",
            produced_by="llama_parse_source_pdf",
            source="parse_result",
            content=parse_result.job_metadata,
            raw_response=parse_result.raw_response,
        )

    for pass_name, extract_result in request.extract_results.items():
        artifacts[pass_name] = RichDocumentPackageArtifact(
            artifact_key=pass_name,
            produced_by=pass_name,
            source="extract_pass",
            content=extract_result.result,
            raw_response=extract_result.raw_response,
        )

    validation_result = request.extract_results.get("validation_critic")
    if validation_result:
        quality_report = validation_result.result.get("quality_report")
        if quality_report is not None:
            artifacts["quality_report"] = RichDocumentPackageArtifact(
                artifact_key="quality_report",
                produced_by="validation_critic",
                source="python_validator",
                content=quality_report,
                raw_response=validation_result.raw_response,
            )

        correction_proposals = validation_result.result.get("correction_proposals")
        if correction_proposals is not None:
            artifacts["correction_proposals"] = RichDocumentPackageArtifact(
                artifact_key="correction_proposals",
                produced_by="validation_critic",
                source="python_validator",
                content=correction_proposals,
                raw_response=validation_result.raw_response,
            )

    package = RichDocumentPackage(
        parse_job_id=parse_result.job_id,
        source_pdf_path=request.source_pdf_path,
        document_code=request.document_code,
        parse_result=parse_result,
        extract_results=request.extract_results,
        artifacts=artifacts,
    )

    return RichDocumentPackageAssemblyResult(
        package=package,
        artifact_count=len(artifacts),
    )