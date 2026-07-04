from convertor_validator_service_lama.models.rich_document_package import (
    RichDocumentPackage,
    RichDocumentPackageArtifact,
)
from convertor_validator_service_lama.services.rag_builder_downcast_service import (
    downcast_rich_package_to_rag_builder,
)


def _artifact(
    artifact_key: str,
    content: object,
    source: str = "extract_pass",
    produced_by: str = "test",
) -> RichDocumentPackageArtifact:
    return RichDocumentPackageArtifact(
        artifact_key=artifact_key,
        source=source,
        produced_by=produced_by,
        content=content,
    )


def test_downcast_rich_package_maps_document_metadata() -> None:
    package = RichDocumentPackage.model_construct(
        parse_job_id="parse-job-1",
        source_pdf_path="source.pdf",
        document_code="GOST-TEST",
        artifacts=[
            _artifact(
                "metadata",
                {
                    "title": "Test document",
                    "page_count": 3,
                },
                source="parse_result",
                produced_by="parse_result",
            )
        ],
        final_correction_policy="python_validator_assembler_applies_final_corrections",
    )

    result = downcast_rich_package_to_rag_builder(package)

    assert result.payload.document.document_code == "GOST-TEST"
    assert result.payload.document.title == "Test document"
    assert result.payload.document.page_count == 3
    assert result.payload.document.source_pdf_path == "source.pdf"
    assert result.payload.document.extra["parse_job_id"] == "parse-job-1"
    assert result.payload.document.extra["final_correction_policy"] == (
        "python_validator_assembler_applies_final_corrections"
    )


def test_downcast_rich_package_maps_sections_tables_images_formulas_and_refs() -> None:
    package = RichDocumentPackage.model_construct(
        parse_job_id="parse-job-1",
        source_pdf_path="source.pdf",
        document_code="GOST-TEST",
        artifacts=[
            _artifact(
                "metadata",
                {
                    "title": "Test document",
                    "page_count": "5",
                },
                source="parse_result",
                produced_by="parse_result",
            ),
            _artifact(
                "sections",
                {
                    "sections": [
                        {
                            "section_id": "s1",
                            "title": "1. Scope",
                            "text": "Scope text",
                            "level": 1,
                            "page_start": 1,
                            "page_end": 2,
                            "path": "1",
                        }
                    ]
                },
            ),
            _artifact(
                "tables",
                {
                    "tables": [
                        {
                            "table_id": "t1",
                            "caption": "Table 1",
                            "page": 2,
                        }
                    ]
                },
            ),
            _artifact(
                "images",
                {
                    "images": [
                        {
                            "image_id": "img1",
                            "caption": "Figure 1",
                            "page": 3,
                        }
                    ]
                },
            ),
            _artifact(
                "formulas",
                {
                    "formulas": [
                        {
                            "formula_id": "f1",
                            "expression": "a=b",
                            "page": 4,
                        }
                    ]
                },
            ),
            _artifact(
                "cross_references",
                {
                    "cross_references": [
                        {
                            "reference_id": "r1",
                            "source": "s1",
                            "target": "t1",
                            "reference_type": "table",
                        }
                    ]
                },
            ),
        ],
        final_correction_policy="python_validator_assembler_applies_final_corrections",
    )

    result = downcast_rich_package_to_rag_builder(package)

    assert result.payload.document.document_code == "GOST-TEST"
    assert result.payload.document.page_count == 5

    assert result.payload.sections[0].section_id == "s1"
    assert result.payload.sections[0].title == "1. Scope"
    assert result.payload.sections[0].text == "Scope text"
    assert result.payload.sections[0].level == 1
    assert result.payload.sections[0].page_start == 1
    assert result.payload.sections[0].page_end == 2
    assert result.payload.sections[0].path == "1"

    assert result.payload.tables[0].table_id == "t1"
    assert result.payload.tables[0].caption == "Table 1"

    assert result.payload.images[0].image_id == "img1"
    assert result.payload.images[0].caption == "Figure 1"

    assert result.payload.formulas[0].formula_id == "f1"
    assert result.payload.formulas[0].expression == "a=b"

    assert result.payload.cross_references[0].reference_id == "r1"
    assert result.payload.cross_references[0].source == "s1"
    assert result.payload.cross_references[0].target == "t1"
    assert result.payload.cross_references[0].reference_type == "table"

    assert result.warnings == []


def test_downcast_rich_package_warns_when_title_and_sections_are_missing() -> None:
    package = RichDocumentPackage.model_construct(
        parse_job_id="parse-job-1",
        source_pdf_path="source.pdf",
        document_code="GOST-TEST",
        artifacts=[],
        final_correction_policy="python_validator_assembler_applies_final_corrections",
    )

    result = downcast_rich_package_to_rag_builder(package)

    assert result.payload.document.document_code == "GOST-TEST"
    assert result.payload.document.title is None
    assert result.payload.sections == []

    warning_codes = {warning.code for warning in result.warnings}
    assert warning_codes == {
        "missing_document_title",
        "missing_sections",
    }


def test_downcast_rich_package_generates_stable_fallback_ids() -> None:
    package = RichDocumentPackage.model_construct(
        parse_job_id="parse-job-1",
        source_pdf_path="source.pdf",
        document_code="GOST-TEST",
        artifacts=[
            _artifact(
                "metadata",
                {"title": "Test document"},
                source="parse_result",
                produced_by="parse_result",
            ),
            _artifact(
                "sections",
                {
                    "sections": [
                        {"title": "Section without id"},
                    ]
                },
            ),
            _artifact(
                "tables",
                {
                    "tables": [
                        {"caption": "Table without id"},
                    ]
                },
            ),
        ],
        final_correction_policy="python_validator_assembler_applies_final_corrections",
    )

    result = downcast_rich_package_to_rag_builder(package)

    assert result.payload.sections[0].section_id == "section-1"
    assert result.payload.tables[0].table_id == "table-1"