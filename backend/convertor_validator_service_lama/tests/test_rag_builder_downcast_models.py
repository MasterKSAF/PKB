from pydantic import ValidationError
import pytest

from convertor_validator_service_lama.models.rag_builder_downcast import (
    RagBuilderCompatiblePayload,
    RagBuilderCrossReferencePayload,
    RagBuilderDocumentPayload,
    RagBuilderDowncastResult,
    RagBuilderDowncastWarning,
    RagBuilderFormulaPayload,
    RagBuilderImagePayload,
    RagBuilderPayloadMetadata,
    RagBuilderSectionPayload,
    RagBuilderTablePayload,
)


def test_rag_builder_payload_metadata_defaults() -> None:
    metadata = RagBuilderPayloadMetadata()

    assert metadata.schema_name == "rag_builder_compatible_payload"
    assert metadata.source_package_name == "rich_document_package.json"
    assert metadata.generated_by == "convertor_validator_service_lama"
    assert metadata.notes == []


def test_rag_builder_document_payload_accepts_minimal_document_data() -> None:
    document = RagBuilderDocumentPayload(
        document_code="GOST-TEST",
        title="Test document",
        page_count=2,
        source_pdf_path="document.pdf",
        extra={"era": "USSR"},
    )

    assert document.document_code == "GOST-TEST"
    assert document.title == "Test document"
    assert document.page_count == 2
    assert document.source_pdf_path == "document.pdf"
    assert document.extra == {"era": "USSR"}


def test_rag_builder_compatible_payload_holds_extracted_entities() -> None:
    payload = RagBuilderCompatiblePayload(
        document=RagBuilderDocumentPayload(document_code="GOST-TEST"),
        sections=[
            RagBuilderSectionPayload(
                section_id="section-1",
                title="1. Scope",
                text="Scope text",
                level=1,
                page_start=1,
                page_end=1,
                path="1",
                raw={"title": "1. Scope"},
            )
        ],
        tables=[
            RagBuilderTablePayload(
                table_id="table-1",
                caption="Table 1",
                page=1,
                raw={"caption": "Table 1"},
            )
        ],
        images=[
            RagBuilderImagePayload(
                image_id="image-1",
                caption="Figure 1",
                page=1,
                raw={"caption": "Figure 1"},
            )
        ],
        formulas=[
            RagBuilderFormulaPayload(
                formula_id="formula-1",
                expression="a=b",
                page=1,
                raw={"expression": "a=b"},
            )
        ],
        cross_references=[
            RagBuilderCrossReferencePayload(
                reference_id="reference-1",
                source="section-1",
                target="table-1",
                reference_type="table",
                raw={"target": "table-1"},
            )
        ],
    )

    assert payload.document.document_code == "GOST-TEST"
    assert payload.sections[0].section_id == "section-1"
    assert payload.tables[0].table_id == "table-1"
    assert payload.images[0].image_id == "image-1"
    assert payload.formulas[0].formula_id == "formula-1"
    assert payload.cross_references[0].reference_id == "reference-1"


def test_rag_builder_downcast_result_holds_payload_and_warnings() -> None:
    result = RagBuilderDowncastResult(
        payload=RagBuilderCompatiblePayload(),
        warnings=[
            RagBuilderDowncastWarning(
                code="missing_sections",
                message="No sections artifact was found.",
                source_artifact="sections",
            )
        ],
    )

    assert result.payload.metadata.schema_name == "rag_builder_compatible_payload"
    assert result.warnings[0].code == "missing_sections"
    assert result.warnings[0].source_artifact == "sections"


@pytest.mark.parametrize(
    "model, field_name",
    [
        (RagBuilderSectionPayload, "section_id"),
        (RagBuilderTablePayload, "table_id"),
        (RagBuilderImagePayload, "image_id"),
        (RagBuilderFormulaPayload, "formula_id"),
        (RagBuilderCrossReferencePayload, "reference_id"),
    ],
)
def test_required_entity_ids_must_not_be_empty(model, field_name: str) -> None:
    with pytest.raises(ValidationError):
        model(**{field_name: ""})