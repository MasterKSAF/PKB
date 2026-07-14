from convertor_validator_service_lama.models.rich_document_package import (
    RichDocumentPackage,
    RichDocumentPackageArtifact,
)
from convertor_validator_service_lama.services.rag_builder_downcast_service import (
    downcast_rich_package_to_rag_builder,
)


def _artifact(key: str, content: object) -> RichDocumentPackageArtifact:
    return RichDocumentPackageArtifact.model_construct(
        artifact_key=key,
        produced_by=key,
        source="test",
        content=content,
        raw_response={},
    )


def _package(*, artifacts: dict[str, RichDocumentPackageArtifact]) -> RichDocumentPackage:
    return RichDocumentPackage.model_construct(
        package_name="test_package",
        parse_job_id="parse-job-1",
        document_code="GOST 10054-82",
        source_pdf_path="test.pdf",
        artifacts=artifacts,
        document_structure=None,
        parse_result={},
        extract_results={},
        final_correction_policy=None,
    )


def test_downcast_uses_title_metadata_artifact_for_document_payload() -> None:
    package = _package(
        artifacts={
            "title_metadata": _artifact(
                "title_metadata",
                {
                    "document_code": "GOST 10054-82",
                    "title": "Waterproof abrasive paper",
                    "full_title": "Waterproof abrasive paper. Specifications",
                    "normalized_title": "Waterproof abrasive paper",
                    "page_count": 5,
                },
            ),
            "metadata": _artifact(
                "metadata",
                {
                    "pages": [
                        {"page_number": 1, "confidence": 0.5},
                        {"page_number": 2, "confidence": 0.6},
                    ]
                },
            ),
            "sections": _artifact(
                "sections",
                {
                    "sections": [
                        {
                            "section_id": "section-1",
                            "clause": "1.1",
                            "title": "Sizes",
                            "content": {"text": "Section text."},
                        }
                    ]
                },
            ),
        }
    )

    result = downcast_rich_package_to_rag_builder(package)

    assert result.payload.document.document_code == "GOST 10054-82"
    assert result.payload.document.title == "Waterproof abrasive paper"
    assert result.payload.document.page_count == 5
    assert [warning.code for warning in result.warnings] == []


def test_downcast_attaches_child_clause_reference_to_nearest_existing_parent_section() -> None:
    package = _package(
        artifacts={
            "title_metadata": _artifact(
                "title_metadata",
                {
                    "document_code": "GOST 10054-82",
                    "title": "Waterproof abrasive paper",
                },
            ),
            "sections": _artifact(
                "sections",
                {
                    "sections": [
                        {
                            "section_id": "section-4-1",
                            "clause": "4.1",
                            "title": "Test methods",
                            "content": {"text": "Text for clause 4.1."},
                        },
                        {
                            "section_id": "section-4-2",
                            "clause": "4.2",
                            "title": "Cutting capacity method",
                            "content": {"text": "Text for clause 4.2."},
                        },
                    ]
                },
            ),
            "references": _artifact(
                "references",
                {
                    "references": [
                        {
                            "section_id": "4.1.1",
                            "reference_text": "REF-6456-82",
                            "target_document_code": "REF-6456-82",
                            "reference_type": "normative_reference",
                            "context": "test by REF-6456-82",
                            "note": "Child clause reference",
                        }
                    ]
                },
            ),
        }
    )

    result = downcast_rich_package_to_rag_builder(package)

    sections_by_clause = {
        section.raw.get("clause"): section
        for section in result.payload.sections
    }

    parent_section = sections_by_clause["4.1"]
    sibling_section = sections_by_clause["4.2"]

    assert len(parent_section.references) == 1
    assert parent_section.references[0].target_doc_code == "REF-6456-82"
    assert sibling_section.references == []

def test_downcast_child_clause_reference_fallback_stays_within_namespace() -> None:
    package = _package(
        artifacts={
            "title_metadata": _artifact(
                "title_metadata",
                {
                    "document_code": "DOC-1",
                    "title": "Namespaced document",
                },
            ),
            "sections": _artifact(
                "sections",
                {
                    "sections": [
                        {
                            "section_id": "main-4-1",
                            "clause": "main_document::4.1",
                            "title": "Main test methods",
                            "content": {"text": "Main clause text."},
                        },
                        {
                            "section_id": "appendix-4-1",
                            "clause": "appendix_A::4.1",
                            "title": "Appendix test methods",
                            "content": {"text": "Appendix clause text."},
                        },
                    ]
                },
            ),
            "references": _artifact(
                "references",
                {
                    "references": [
                        {
                            "section_id": "main_document::4.1.1",
                            "reference_text": "REF-MAIN",
                            "target_document_code": "REF-MAIN",
                            "reference_type": "normative_reference",
                            "context": "main child reference",
                        },
                        {
                            "section_id": "appendix_A::4.1.1",
                            "reference_text": "REF-APPENDIX",
                            "target_document_code": "REF-APPENDIX",
                            "reference_type": "normative_reference",
                            "context": "appendix child reference",
                        },
                    ]
                },
            ),
        }
    )

    result = downcast_rich_package_to_rag_builder(package)

    sections_by_clause = {
        section.raw.get("clause"): section
        for section in result.payload.sections
    }

    assert [
        reference.target_doc_code
        for reference in sections_by_clause["main_document::4.1"].references
    ] == ["REF-MAIN"]

    assert [
        reference.target_doc_code
        for reference in sections_by_clause["appendix_A::4.1"].references
    ] == ["REF-APPENDIX"]


def test_downcast_child_clause_reference_fallback_does_not_attach_to_top_level_parent() -> None:
    package = _package(
        artifacts={
            "title_metadata": _artifact(
                "title_metadata",
                {
                    "document_code": "DOC-1",
                    "title": "Namespaced document",
                },
            ),
            "sections": _artifact(
                "sections",
                {
                    "sections": [
                        {
                            "section_id": "main-4",
                            "clause": "main_document::4",
                            "title": "Top level section",
                            "content": {"text": "Top level text."},
                        }
                    ]
                },
            ),
            "references": _artifact(
                "references",
                {
                    "references": [
                        {
                            "section_id": "main_document::4.1",
                            "reference_text": "REF-CHILD",
                            "target_document_code": "REF-CHILD",
                            "reference_type": "normative_reference",
                            "context": "child reference",
                        }
                    ]
                },
            ),
        }
    )

    result = downcast_rich_package_to_rag_builder(package)

    assert result.payload.sections[0].references == []

def test_downcast_child_clause_reference_fallback_does_not_treat_slash_path_as_namespace() -> None:
    package = _package(
        artifacts={
            "title_metadata": _artifact(
                "title_metadata",
                {
                    "document_code": "DOC-1",
                    "title": "Slash path document",
                },
            ),
            "sections": _artifact(
                "sections",
                {
                    "sections": [
                        {
                            "section_id": "path-4-1",
                            "clause": "main_document/4.1",
                            "title": "Path-like clause",
                            "content": {"text": "Path-like clause text."},
                        }
                    ]
                },
            ),
            "references": _artifact(
                "references",
                {
                    "references": [
                        {
                            "section_id": "main_document/4.1.1",
                            "reference_text": "REF-PATH",
                            "target_document_code": "REF-PATH",
                            "reference_type": "normative_reference",
                            "context": "slash path reference",
                        }
                    ]
                },
            ),
        }
    )

    result = downcast_rich_package_to_rag_builder(package)

    assert result.payload.sections[0].references == []

