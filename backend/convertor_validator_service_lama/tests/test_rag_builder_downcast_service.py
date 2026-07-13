from convertor_validator_service_lama.models.rich_document_package import (
    RichDocumentPackage,
    RichDocumentPackageArtifact,
    RichDocumentSection,
    RichDocumentStructure,
)
from convertor_validator_service_lama.services.rag_builder_downcast_service import (
    downcast_rich_package_to_rag_builder,
)
from convertor_validator_service_lama.services.reference_normalizer import (
    expand_gost_document_codes_from_values,
)
from gost_20868_fixture_helpers import (
    gost_20868_chunk_container_extract_results,
    load_gost_20868_formula_chunk_container,
)






def _expected_rag_reference_target_codes(section: dict[str, object]) -> list[str]:
    direct_codes: list[str] = []

    for reference in section.get("references", []):
        if not isinstance(reference, dict):
            continue

        target_doc_code = reference.get("target_doc_code")
        if isinstance(target_doc_code, str):
            direct_codes.append(target_doc_code)

    range_codes = _expanded_codes_from_reference_endpoints(direct_codes)
    if range_codes is not None:
        return range_codes

    result: list[str] = []
    for target_doc_code in direct_codes:
        expanded_codes = expand_gost_document_codes_from_values(
            None,
            target_doc_code,
        )

        if expanded_codes:
            result.extend(expanded_codes)
        else:
            result.append(target_doc_code)

    return result


def _expanded_codes_from_reference_endpoints(
    direct_codes: list[str],
) -> list[str] | None:
    if len(direct_codes) != 2:
        return None

    range_text = f"{direct_codes[0]} - {direct_codes[1]}"
    expanded_codes = expand_gost_document_codes_from_values(
        range_text,
        range_text,
    )

    if len(expanded_codes) > len(direct_codes):
        return expanded_codes

    return None

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


def test_downcast_rich_package_maps_gost_20868_fixture_layers() -> None:
    data = load_gost_20868_formula_chunk_container()
    extract_results = gost_20868_chunk_container_extract_results(data)

    artifacts = [
        _artifact(
            "metadata",
            {
                "title": data["document"]["title"],
                "page_count": data["document"]["page_count"],
            },
            source="parse_result",
            produced_by="parse_result",
        )
    ]

    for artifact_key, extract_result in extract_results.items():
        artifacts.append(
            _artifact(
                artifact_key,
                extract_result.result,
                produced_by=artifact_key,
            )
        )

    package = RichDocumentPackage.model_construct(
        parse_job_id="parse-job-gost-20868",
        source_pdf_path="gost_20868_81.pdf",
        document_code=data["document"]["doc_code"],
        artifacts=artifacts,
        final_correction_policy="python_validator_assembler_applies_final_corrections",
    )

    result = downcast_rich_package_to_rag_builder(package)
    payload = result.payload

    assert payload.document.document_code == data["document"]["doc_code"]
    assert payload.document.title == data["document"]["title"]
    assert payload.document.page_count == data["document"]["page_count"]

    section_clauses = {
        section.raw["clause"]
        for section in payload.sections
    }
    assert {"title", "1", "6", "6.1", "9"}.issubset(section_clauses)

    assert [image.image_id for image in payload.images] == [
        "figure-1",
        "figure-2",
    ]

    assert len(payload.tables) == 1
    assert payload.tables[0].table_id == "table-1"

    assert len(payload.formulas) == 1
    assert payload.formulas[0].formula_id == "formula-test"
    assert payload.formulas[0].expression == "D = L / 2"

    sections_by_clause = {
        section.raw["clause"]: section
        for section in payload.sections
    }
    expected_references_by_clause = {
        section["clause"]: _expected_rag_reference_target_codes(section)
        for section in data["sections"]
        if section.get("references")
    }

    assert set(expected_references_by_clause) == {"2", "3", "4", "6.1"}
    assert sum(
        len(target_doc_codes)
        for target_doc_codes in expected_references_by_clause.values()
    ) == 10
    assert expected_references_by_clause["6.1"] == ["table_1"]

    for clause, expected_target_doc_codes in expected_references_by_clause.items():
        assert [
            reference.target_doc_code
            for reference in sections_by_clause[clause].references
        ] == expected_target_doc_codes

    assert payload.cross_references == []
    assert result.warnings == []


def test_downcast_rich_package_uses_document_structure_sections_when_artifact_missing() -> None:
    package = RichDocumentPackage.model_construct(
        parse_job_id="parse-job-1",
        source_pdf_path="source.pdf",
        document_code="GOST-TEST",
        artifacts=[
            _artifact(
                "metadata",
                {
                    "title": "Test document",
                    "page_count": 2,
                },
                source="parse_result",
                produced_by="parse_result",
            ),
        ],
        document_structure=RichDocumentStructure(
            sections=[
                RichDocumentSection(
                    section_id="main_document/1",
                    clause="1",
                    title="1. Scope",
                    level=1,
                    path="main_document/1",
                    page_start=1,
                    page_end=1,
                    content={
                        "source_spans": [
                            {
                                "text_preview": "Scope text from document structure."
                            }
                        ]
                    },
                )
            ]
        ),
        final_correction_policy="python_validator_assembler_applies_final_corrections",
    )

    result = downcast_rich_package_to_rag_builder(package)

    assert result.payload.sections[0].section_id == "main_document/1"
    assert result.payload.sections[0].title == "1. Scope"
    assert result.payload.sections[0].text == "Scope text from document structure."
    assert result.payload.sections[0].level == 1
    assert result.payload.sections[0].page_start == 1
    assert result.payload.sections[0].page_end == 1
    assert result.payload.sections[0].path == "main_document/1"
    assert result.warnings == []


def test_downcast_attaches_references_by_clause_when_section_id_differs() -> None:
    package = RichDocumentPackage.model_construct(
        parse_job_id="parse-job-1",
        source_pdf_path="source.pdf",
        document_code="GOST-TEST",
        artifacts=[
            _artifact(
                "metadata",
                {
                    "title": "Test document",
                    "page_count": 2,
                },
                source="parse_result",
                produced_by="parse_result",
            ),
            _artifact(
                "references",
                {
                    "references": [
                        {
                            "section_id": "2",
                            "reference_text": "GOST 20862-81 - GOST 20867-81",
                            "target_document_codes": [
                                "GOST 20862-81",
                                "GOST 20863-81",
                                "GOST 20864-81",
                                "GOST 20865-81",
                                "GOST 20866-81",
                                "GOST 20867-81",
                            ],
                            "reference_type": "standard_range",
                        }
                    ]
                },
            ),
        ],
        document_structure=RichDocumentStructure(
            sections=[
                RichDocumentSection(
                    section_id="main_document/2",
                    clause="2",
                    title="2. Normative references",
                    path="main_document/2",
                    page_start=1,
                    page_end=1,
                    content={
                        "source_spans": [
                            {
                                "text_preview": "2. GOST 20862-81 - GOST 20867-81",
                            }
                        ]
                    },
                )
            ]
        ),
        final_correction_policy="python_validator_assembler_applies_final_corrections",
    )

    result = downcast_rich_package_to_rag_builder(package)

    section = result.payload.sections[0]

    assert section.section_id == "main_document/2"
    assert [
        reference.target_doc_code
        for reference in section.references
    ] == [
        "GOST 20862-81",
        "GOST 20863-81",
        "GOST 20864-81",
        "GOST 20865-81",
        "GOST 20866-81",
        "GOST 20867-81",
    ]
    assert section.references[0].context == "GOST 20862-81 - GOST 20867-81"
    assert result.warnings == []


def test_downcast_filters_self_reference_from_section_references() -> None:
    package = RichDocumentPackage.model_construct(
        parse_job_id="parse-job-1",
        source_pdf_path="source.pdf",
        document_code="GOST 20868-81",
        artifacts=[
            _artifact(
                "metadata",
                {
                    "title": "Test document",
                    "page_count": 2,
                },
                source="parse_result",
                produced_by="parse_result",
            ),
            _artifact(
                "references",
                {
                    "references": [
                        {
                            "section_id": "2",
                            "reference_text": "\u0413\u041e\u0421\u0422 20868\u201481",
                            "target_document_code": "\u0413\u041e\u0421\u0422 20868\u201481",
                            "reference_type": "standard",
                        },
                        {
                            "section_id": "2",
                            "reference_text": "\u0413\u041e\u0421\u0422 20862-81",
                            "target_document_code": "\u0413\u041e\u0421\u0422 20862-81",
                            "reference_type": "standard",
                        },
                    ]
                },
            ),
        ],
        document_structure=RichDocumentStructure(
            sections=[
                RichDocumentSection(
                    section_id="main_document/2",
                    clause="2",
                    title="2. Normative references",
                    path="main_document/2",
                    page_start=1,
                    page_end=1,
                    content={"text": "Clause 2"},
                )
            ]
        ),
        final_correction_policy="python_validator_assembler_applies_final_corrections",
    )

    result = downcast_rich_package_to_rag_builder(package)

    section = result.payload.sections[0]

    assert [
        reference.target_doc_code
        for reference in section.references
    ] == ["\u0413\u041e\u0421\u0422 20862-81"]


def test_downcast_expands_reference_ranges_for_rag_section_references() -> None:
    package = RichDocumentPackage.model_construct(
        parse_job_id="parse-job-1",
        source_pdf_path="source.pdf",
        document_code="GOST 20868-81",
        artifacts=[
            _artifact(
                "metadata",
                {
                    "title": "Test document",
                    "page_count": 2,
                },
                source="parse_result",
                produced_by="parse_result",
            ),
            _artifact(
                "references",
                {
                    "references": [
                        {
                            "section_id": "2",
                            "reference_text": "\u0413\u041e\u0421\u0422 20862-81 \u2014 \u0413\u041e\u0421\u0422 20867-81",
                            "target_document_code": "\u0413\u041e\u0421\u0422 20862-81 \u2014 \u0413\u041e\u0421\u0422 20867-81",
                            "reference_type": "standard_range",
                        }
                    ]
                },
            ),
        ],
        document_structure=RichDocumentStructure(
            sections=[
                RichDocumentSection(
                    section_id="main_document/2",
                    clause="2",
                    title="2. Normative references",
                    path="main_document/2",
                    page_start=1,
                    page_end=1,
                    content={"text": "Clause 2"},
                )
            ]
        ),
        final_correction_policy="python_validator_assembler_applies_final_corrections",
    )

    result = downcast_rich_package_to_rag_builder(package)

    section = result.payload.sections[0]

    assert [
        reference.target_doc_code
        for reference in section.references
    ] == [
        "\u0413\u041e\u0421\u0422 20862-81",
        "\u0413\u041e\u0421\u0422 20863-81",
        "\u0413\u041e\u0421\u0422 20864-81",
        "\u0413\u041e\u0421\u0422 20865-81",
        "\u0413\u041e\u0421\u0422 20866-81",
        "\u0413\u041e\u0421\u0422 20867-81",
    ]
    assert [
        reference.type
        for reference in section.references
    ] == ["standard_range"] * 6
    assert [
        reference.context
        for reference in section.references
    ] == ["\u0413\u041e\u0421\u0422 20862-81 \u2014 \u0413\u041e\u0421\u0422 20867-81"] * 6
