from pydantic import ValidationError
import pytest

from convertor_validator_service_lama.models.rich_document_package import (
    RichDocumentBoundary,
    RichDocumentCrossReference,
    RichDocumentFormula,
    RichDocumentImage,
    RichDocumentNestedDocument,
    RichDocumentNote,
    RichDocumentPackage,
    RichDocumentReference,
    RichDocumentSection,
    RichDocumentStructure,
    RichDocumentTable,
    RichDocumentTableCell,
    RichDocumentTableOfContentsItem,
    RichDocumentTableOfContentsBlock,
)


def test_rich_document_structure_defaults_are_empty() -> None:
    structure = RichDocumentStructure()

    assert structure.document_boundaries == []
    assert structure.table_of_contents_blocks == []
    assert structure.table_of_contents == []
    assert structure.nested_documents == []
    assert structure.sections == []
    assert structure.tables == []
    assert structure.images == []
    assert structure.formulas == []
    assert structure.notes == []
    assert structure.references == []
    assert structure.cross_references == []
    assert structure.quality_report is None
    assert structure.correction_proposals == []


def test_rich_document_structure_preserves_document_boundaries_and_toc() -> None:
    structure = RichDocumentStructure(
        document_boundaries=[
            RichDocumentBoundary(
                boundary_id="boundary-1",
                boundary_type="main_document",
                title="Main document",
                page_start=1,
                page_end=10,
                raw={"kind": "main_document"},
            )
        ],
        table_of_contents=[
            RichDocumentTableOfContentsItem(
                item_id="toc-1",
                title="1. Scope",
                level=1,
                page=1,
                path="1",
                target_section_id="section-1",
                raw={"title": "1. Scope"},
            )
        ],
    )

    assert structure.document_boundaries[0].boundary_type == "main_document"
    assert structure.table_of_contents[0].title == "1. Scope"
    assert structure.table_of_contents[0].target_section_id == "section-1"


def test_rich_document_structure_preserves_multiple_table_of_contents_blocks() -> None:
    structure = RichDocumentStructure(
        table_of_contents_blocks=[
            RichDocumentTableOfContentsBlock(
                toc_id="toc-main",
                title="Table of contents",
                namespace_id="front_matter",
                page_start=1,
                page_end=1,
                items=[
                    RichDocumentTableOfContentsItem(
                        item_id="toc-main-1",
                        title="1 Scope",
                        level=1,
                        page=2,
                        path="main/1",
                    )
                ],
                raw={"source": "front matter"},
            ),
            RichDocumentTableOfContentsBlock(
                toc_id="toc-appendix",
                title="Appendix table of contents",
                namespace_id="appendix_a",
                page_start=10,
                page_end=10,
                items=[
                    RichDocumentTableOfContentsItem(
                        item_id="toc-appendix-1",
                        title="A.1 Additional requirements",
                        level=1,
                        page=11,
                        path="appendix_a/a_1",
                    )
                ],
                raw={"source": "appendix"},
            ),
        ]
    )

    assert len(structure.table_of_contents_blocks) == 2
    assert structure.table_of_contents_blocks[0].toc_id == "toc-main"
    assert structure.table_of_contents_blocks[1].namespace_id == "appendix_a"
    assert structure.table_of_contents_blocks[1].items[0].title == "A.1 Additional requirements"


def test_rich_document_structure_preserves_nested_documents() -> None:
    structure = RichDocumentStructure(
        nested_documents=[
            RichDocumentNestedDocument(
                nested_document_id="nested-1",
                document_code="APPENDIX-A",
                title="Appendix A",
                page_start=11,
                page_end=12,
                parent_boundary_id="boundary-1",
                raw={"source": "appendix"},
            )
        ]
    )

    assert structure.nested_documents[0].document_code == "APPENDIX-A"
    assert structure.nested_documents[0].parent_boundary_id == "boundary-1"


def test_rich_document_table_cell_can_contain_images_and_formulas() -> None:
    table = RichDocumentTable(
        table_id="table-1",
        caption="Table 1",
        page=2,
        cells=[
            RichDocumentTableCell(
                row_index=0,
                column_index=1,
                text="Cell text",
                images=[
                    RichDocumentImage(
                        image_id="image-in-cell-1",
                        caption="Cell image",
                        page=2,
                    )
                ],
                formulas=[
                    RichDocumentFormula(
                        formula_id="formula-in-cell-1",
                        expression="a=b",
                        page=2,
                    )
                ],
                raw={"cell": "raw"},
            )
        ],
        raw={"table": "raw"},
    )

    assert table.cells[0].text == "Cell text"
    assert table.cells[0].images[0].image_id == "image-in-cell-1"
    assert table.cells[0].formulas[0].expression == "a=b"


def test_rich_document_structure_preserves_notes() -> None:
    structure = RichDocumentStructure(
        notes=[
            RichDocumentNote(
                note_id="note-1",
                namespace_id="main_document",
                section_id="section-1",
                text="Note text",
                page=2,
                bbox=[0.1, 0.2, 0.3, 0.4],
                raw={"source": "notes_pass"},
            )
        ]
    )

    assert structure.notes[0].note_id == "note-1"
    assert structure.notes[0].section_id == "section-1"
    assert structure.notes[0].text == "Note text"
    assert structure.notes[0].bbox == [0.1, 0.2, 0.3, 0.4]


def test_rich_document_structure_preserves_references() -> None:
    structure = RichDocumentStructure(
        references=[
            RichDocumentReference(
                reference_id="reference-1",
                namespace_id="main_document",
                section_id="section-1",
                reference_text="GOST 123",
                target_document_code="GOST 123",
                target_document_codes=["GOST 123"],
                target_clause="1.2",
                reference_type="normative_reference",
                page=3,
                bbox=[0.1, 0.2, 0.3, 0.4],
                raw={"source": "references_pass"},
            )
        ]
    )

    assert structure.references[0].reference_id == "reference-1"
    assert structure.references[0].reference_text == "GOST 123"
    assert structure.references[0].target_document_code == "GOST 123"
    assert structure.references[0].target_document_codes == ["GOST 123"]
    assert structure.references[0].target_clause == "1.2"
    assert structure.references[0].reference_type == "normative_reference"


def test_rich_document_structure_preserves_sections_and_cross_references() -> None:
    structure = RichDocumentStructure(
        sections=[
            RichDocumentSection(
                section_id="section-1",
                clause="1",
                title="1. Scope",
                level=1,
                path="1",
                page_start=1,
                page_end=1,
                section_type="text",
                content={"text": "Scope text"},
                raw={"source": "sections_pass"},
            )
        ],
        cross_references=[
            RichDocumentCrossReference(
                reference_id="ref-1",
                source_id="section-1",
                target_document_code="ГОСТ 123",
                reference_type="normative_reference",
                context="See ГОСТ 123",
                raw={"target": "ГОСТ 123"},
            )
        ],
    )

    assert structure.sections[0].section_id == "section-1"
    assert structure.cross_references[0].target_document_code == "ГОСТ 123"


def test_rich_document_structure_preserves_validation_outputs() -> None:
    structure = RichDocumentStructure(
        quality_report={"score": 0.95},
        correction_proposals=[
            {
                "kind": "replace_text",
                "target": "section-1",
            }
        ],
    )

    assert structure.quality_report == {"score": 0.95}
    assert structure.correction_proposals[0]["kind"] == "replace_text"


def test_rich_document_package_has_document_structure_default() -> None:
    package = RichDocumentPackage.model_construct(
        parse_job_id="parse-job-1",
        parse_result=None,
    )

    assert isinstance(package.document_structure, RichDocumentStructure)


@pytest.mark.parametrize(
    "model, payload",
    [
        (RichDocumentBoundary, {"page_start": -1}),
        (RichDocumentTableOfContentsItem, {"title": "", "level": 1}),
        (RichDocumentTableOfContentsItem, {"title": "1. Scope", "level": -1}),
        (RichDocumentTableCell, {"row_index": -1, "column_index": 0}),
        (RichDocumentTableCell, {"row_index": 0, "column_index": -1}),
    ],
)
def test_rich_document_structure_rejects_invalid_values(model, payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        model(**payload)