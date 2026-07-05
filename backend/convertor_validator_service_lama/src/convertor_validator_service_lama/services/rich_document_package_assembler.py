from typing import Any

from convertor_validator_service_lama.models.rich_document_package import (
    RichDocumentBoundary,
    RichDocumentCrossReference,
    RichDocumentFormula,
    RichDocumentImage,
    RichDocumentNestedDocument,
    RichDocumentNamespace,
    RichDocumentPackage,
    RichDocumentPackageArtifact,
    RichDocumentPackageAssemblyRequest,
    RichDocumentPackageAssemblyResult,
    RichDocumentSection,
    RichDocumentStructure,
    RichDocumentTable,
    RichDocumentTableCell,
    RichDocumentTableOfContentsItem,
)
from convertor_validator_service_lama.services.document_structure_assembler import (
    assemble_document_structure_from_parse_items,
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
        validation_content = (
            validation_result.result
            if isinstance(validation_result.result, dict)
            else {}
        )

        quality_report = validation_content.get("quality_report")
        if quality_report is not None:
            artifacts["quality_report"] = RichDocumentPackageArtifact(
                artifact_key="quality_report",
                produced_by="validation_critic",
                source="python_validator",
                content=quality_report,
                raw_response=validation_result.raw_response,
            )

        correction_proposals = validation_content.get("correction_proposals")
        if correction_proposals is not None:
            artifacts["correction_proposals"] = RichDocumentPackageArtifact(
                artifact_key="correction_proposals",
                produced_by="validation_critic",
                source="python_validator",
                content=correction_proposals,
                raw_response=validation_result.raw_response,
            )

    document_structure = build_document_structure_from_artifacts(
        artifacts,
        parse_items=parse_result.items,
        parse_page_count=_parse_page_count(parse_result.metadata, parse_result.job_metadata),
    )

    package = RichDocumentPackage(
        parse_job_id=parse_result.job_id,
        source_pdf_path=request.source_pdf_path,
        document_code=request.document_code,
        parse_result=parse_result,
        extract_results=request.extract_results,
        artifacts=artifacts,
        document_structure=document_structure,
    )

    return RichDocumentPackageAssemblyResult(
        package=package,
        artifact_count=len(artifacts),
    )


def build_document_structure_from_artifacts(
    artifacts: dict[str, RichDocumentPackageArtifact],
    *,
    parse_items: list[dict[str, Any]] | None = None,
    parse_page_count: int | None = None,
) -> RichDocumentStructure:
    parse_item_structure = _build_parse_item_structure(
        parse_items=parse_items or [],
        page_count=parse_page_count,
    )

    parse_namespaces = _build_namespaces_from_rows(
        parse_item_structure.get("namespaces", [])
    )
    parse_sections = _build_sections_from_rows(
        parse_item_structure.get("sections", [])
    )

    extract_sections = _build_sections(artifacts.get("sections"))

    diagnostics: dict[str, Any] = {}
    if parse_item_structure:
        diagnostics["parse_item_structure"] = parse_item_structure.get("diagnostics", {})

    return RichDocumentStructure(
        namespaces=parse_namespaces,
        document_boundaries=_build_document_boundaries(
            artifacts.get("document_boundaries")
        ),
        table_of_contents=_build_table_of_contents(
            artifacts.get("table_of_contents")
        ),
        nested_documents=_build_nested_documents(
            artifacts.get("nested_documents")
        ),
        sections=extract_sections or parse_sections,
        tables=_build_tables(artifacts.get("tables")),
        images=_build_images_from_artifact(artifacts.get("images")),
        formulas=_build_formulas_from_artifact(artifacts.get("formulas")),
        cross_references=_build_cross_references(
            artifacts.get("cross_references")
        ),
        quality_report=_build_quality_report(artifacts.get("quality_report")),
        correction_proposals=_build_correction_proposals(
            artifacts.get("correction_proposals")
        ),
        diagnostics=diagnostics,
    )


def _build_parse_item_structure(
    *,
    parse_items: list[dict[str, Any]],
    page_count: int | None,
) -> dict[str, Any]:
    if not parse_items:
        return {}

    return assemble_document_structure_from_parse_items(
        parse_items,
        page_count=page_count,
    )


def _parse_page_count(
    metadata: dict[str, Any],
    job_metadata: dict[str, Any],
) -> int | None:
    candidates = (
        job_metadata.get("pdf-pages"),
        job_metadata.get("page_count"),
        job_metadata.get("pages"),
        metadata.get("page_count"),
        metadata.get("pages_count"),
        metadata.get("pdf_pages"),
    )

    for value in candidates:
        if isinstance(value, bool):
            continue

        if isinstance(value, int):
            return value

        if isinstance(value, str) and value.strip().isdigit():
            return int(value.strip())

    pages = metadata.get("pages")
    if isinstance(pages, list):
        return len(pages)

    return None


def _build_namespaces_from_rows(rows: list[Any]) -> list[RichDocumentNamespace]:
    namespaces: list[RichDocumentNamespace] = []

    for row in rows:
        if not isinstance(row, dict):
            continue

        namespace_id = _first_str(row.get("namespace_id"), row.get("id"))
        if namespace_id is None:
            continue

        namespaces.append(
            RichDocumentNamespace(
                namespace_id=namespace_id,
                title=_first_str(row.get("title"), row.get("name")),
                page_start=_first_int(row.get("page_start")),
                page_end=_first_int(row.get("page_end")),
                start_heading_id=_first_str(row.get("start_heading_id")),
                start_item_index=_first_int(row.get("start_item_index")),
                end_item_index_exclusive=_first_int(row.get("end_item_index_exclusive")),
                ordinal=_first_int(row.get("ordinal")),
                raw=row,
            )
        )

    return namespaces


def _build_document_boundaries(
    artifact: RichDocumentPackageArtifact | None,
) -> list[RichDocumentBoundary]:
    rows = _artifact_content_as_list(
        artifact,
        preferred_keys=("document_boundaries", "boundaries", "items", "data"),
    )

    boundaries: list[RichDocumentBoundary] = []
    for row in rows:
        if not isinstance(row, dict):
            continue

        boundaries.append(
            RichDocumentBoundary(
                boundary_id=_first_str(
                    row.get("boundary_id"),
                    row.get("id"),
                    row.get("uid"),
                ),
                boundary_type=_first_str(
                    row.get("boundary_type"),
                    row.get("type"),
                    row.get("kind"),
                ),
                title=_first_str(row.get("title"), row.get("name")),
                page_start=_first_int(row.get("page_start"), row.get("page")),
                page_end=_first_int(row.get("page_end"), row.get("page")),
                raw=row,
            )
        )

    return boundaries


def _build_table_of_contents(
    artifact: RichDocumentPackageArtifact | None,
) -> list[RichDocumentTableOfContentsItem]:
    rows = _artifact_content_as_list(
        artifact,
        preferred_keys=("table_of_contents", "toc", "items", "data"),
    )

    items: list[RichDocumentTableOfContentsItem] = []
    for row in rows:
        if not isinstance(row, dict):
            continue

        title = _first_str(row.get("title"), row.get("heading"), row.get("text"))
        if title is None:
            continue

        items.append(
            RichDocumentTableOfContentsItem(
                item_id=_first_str(row.get("item_id"), row.get("id"), row.get("uid")),
                title=title,
                level=_first_int(row.get("level"), row.get("depth"), fallback=0) or 0,
                page=_first_int(row.get("page")),
                path=_first_str(row.get("path"), row.get("section_path")),
                target_section_id=_first_str(
                    row.get("target_section_id"),
                    row.get("section_id"),
                    row.get("target_id"),
                ),
                raw=row,
            )
        )

    return items


def _build_nested_documents(
    artifact: RichDocumentPackageArtifact | None,
) -> list[RichDocumentNestedDocument]:
    rows = _artifact_content_as_list(
        artifact,
        preferred_keys=("nested_documents", "documents", "items", "data"),
    )

    documents: list[RichDocumentNestedDocument] = []
    for row in rows:
        if not isinstance(row, dict):
            continue

        documents.append(
            RichDocumentNestedDocument(
                nested_document_id=_first_str(
                    row.get("nested_document_id"),
                    row.get("document_id"),
                    row.get("id"),
                    row.get("uid"),
                ),
                document_code=_first_str(
                    row.get("document_code"),
                    row.get("doc_code"),
                    row.get("code"),
                ),
                title=_first_str(row.get("title"), row.get("name")),
                page_start=_first_int(row.get("page_start"), row.get("page")),
                page_end=_first_int(row.get("page_end"), row.get("page")),
                parent_boundary_id=_first_str(row.get("parent_boundary_id")),
                raw=row,
            )
        )

    return documents


def _build_sections(
    artifact: RichDocumentPackageArtifact | None,
) -> list[RichDocumentSection]:
    rows = _artifact_content_as_list(
        artifact,
        preferred_keys=("sections", "items", "data"),
    )

    return _build_sections_from_rows(rows)


def _build_sections_from_rows(rows: list[Any]) -> list[RichDocumentSection]:
    sections: list[RichDocumentSection] = []

    for row in rows:
        if not isinstance(row, dict):
            continue

        sections.append(
            RichDocumentSection(
                section_id=_first_str(
                    row.get("section_id"),
                    row.get("id"),
                    row.get("uid"),
                    row.get("number"),
                ),
                parent_section_id=_first_str(
                    row.get("parent_section_id"),
                    row.get("parent_id"),
                ),
                clause=_first_str(row.get("clause"), row.get("number")),
                title=_first_str(row.get("title"), row.get("heading")),
                level=_first_int(
                    row.get("level"),
                    row.get("depth"),
                    row.get("markdown_level"),
                ),
                path=_first_str(
                    row.get("namespaced_path"),
                    row.get("path"),
                    row.get("section_path"),
                ),
                page_start=_first_int(row.get("page_start"), row.get("page")),
                page_end=_first_int(row.get("page_end"), row.get("page")),
                bbox=_bbox(row.get("bbox")) or _bbox_from_source_spans(
                    row.get("source_spans")
                ),
                section_type=_first_str(
                    row.get("section_type"),
                    row.get("type"),
                    row.get("kind"),
                ),
                content=row.get("content", row.get("content_text", row.get("text"))),
                raw=row,
            )
        )

    return sections


def _bbox_from_source_spans(value: Any) -> list[float] | None:
    if not isinstance(value, list):
        return None

    for row in value:
        if not isinstance(row, dict):
            continue

        normalized_bbox = row.get("normalized_bbox")
        if not isinstance(normalized_bbox, dict):
            continue

        keys = ("x", "y", "w", "h")
        if all(isinstance(normalized_bbox.get(key), (int, float)) for key in keys):
            return [float(normalized_bbox[key]) for key in keys]

    return None


def _build_tables(
    artifact: RichDocumentPackageArtifact | None,
) -> list[RichDocumentTable]:
    rows = _artifact_content_as_list(
        artifact,
        preferred_keys=("tables", "items", "data"),
    )

    tables: list[RichDocumentTable] = []
    for row in rows:
        if not isinstance(row, dict):
            continue

        tables.append(
            RichDocumentTable(
                table_id=_first_str(row.get("table_id"), row.get("id"), row.get("uid")),
                caption=_first_str(row.get("caption"), row.get("title")),
                page=_first_int(row.get("page")),
                bbox=_bbox(row.get("bbox")),
                cells=_build_table_cells(row.get("cells")),
                rows=_list_of_dicts(row.get("rows")),
                raw=row,
            )
        )

    return tables


def _build_table_cells(value: Any) -> list[RichDocumentTableCell]:
    cells: list[RichDocumentTableCell] = []

    for fallback_index, row in enumerate(_list_from_value(value)):
        if not isinstance(row, dict):
            continue

        cells.append(
            RichDocumentTableCell(
                row_index=_first_int(
                    row.get("row_index"),
                    row.get("row"),
                    fallback=0,
                ) or 0,
                column_index=_first_int(
                    row.get("column_index"),
                    row.get("column"),
                    fallback=fallback_index,
                ) or fallback_index,
                text=_first_str(row.get("text"), row.get("content")),
                markdown=_first_str(row.get("markdown"), row.get("md")),
                images=_build_images_from_rows(_list_from_value(row.get("images"))),
                formulas=_build_formulas_from_rows(_list_from_value(row.get("formulas"))),
                raw=row,
            )
        )

    return cells


def _build_images_from_artifact(
    artifact: RichDocumentPackageArtifact | None,
) -> list[RichDocumentImage]:
    rows = _artifact_content_as_list(
        artifact,
        preferred_keys=("images", "figures", "items", "data"),
    )

    return _build_images_from_rows(rows)


def _build_images_from_rows(rows: list[Any]) -> list[RichDocumentImage]:
    images: list[RichDocumentImage] = []

    for row in rows:
        if not isinstance(row, dict):
            continue

        images.append(
            RichDocumentImage(
                image_id=_first_str(
                    row.get("image_id"),
                    row.get("figure_id"),
                    row.get("id"),
                    row.get("uid"),
                ),
                caption=_first_str(row.get("caption"), row.get("title")),
                alt_text=_first_str(row.get("alt_text"), row.get("description")),
                page=_first_int(row.get("page")),
                bbox=_bbox(row.get("bbox")),
                storage_uri=_first_str(
                    row.get("storage_uri"),
                    row.get("uri"),
                    row.get("url"),
                ),
                raw=row,
            )
        )

    return images


def _build_formulas_from_artifact(
    artifact: RichDocumentPackageArtifact | None,
) -> list[RichDocumentFormula]:
    rows = _artifact_content_as_list(
        artifact,
        preferred_keys=("formulas", "items", "data"),
    )

    return _build_formulas_from_rows(rows)


def _build_formulas_from_rows(rows: list[Any]) -> list[RichDocumentFormula]:
    formulas: list[RichDocumentFormula] = []

    for row in rows:
        if not isinstance(row, dict):
            continue

        formulas.append(
            RichDocumentFormula(
                formula_id=_first_str(
                    row.get("formula_id"),
                    row.get("id"),
                    row.get("uid"),
                ),
                expression=_first_str(row.get("expression"), row.get("text")),
                latex=_first_str(row.get("latex")),
                page=_first_int(row.get("page")),
                bbox=_bbox(row.get("bbox")),
                parameters=_list_of_dicts(row.get("parameters")),
                raw=row,
            )
        )

    return formulas


def _build_cross_references(
    artifact: RichDocumentPackageArtifact | None,
) -> list[RichDocumentCrossReference]:
    rows = _artifact_content_as_list(
        artifact,
        preferred_keys=("cross_references", "references", "items", "data"),
    )

    references: list[RichDocumentCrossReference] = []
    for row in rows:
        if not isinstance(row, dict):
            continue

        references.append(
            RichDocumentCrossReference(
                reference_id=_first_str(row.get("reference_id"), row.get("id"), row.get("uid")),
                source_id=_first_str(row.get("source_id"), row.get("source")),
                target_id=_first_str(row.get("target_id"), row.get("target")),
                target_document_code=_first_str(
                    row.get("target_document_code"),
                    row.get("target_doc_code"),
                    row.get("doc_code"),
                ),
                reference_type=_first_str(
                    row.get("reference_type"),
                    row.get("type"),
                    row.get("kind"),
                ),
                context=_first_str(row.get("context")),
                note=_first_str(row.get("note")),
                raw=row,
            )
        )

    return references


def _build_quality_report(
    artifact: RichDocumentPackageArtifact | None,
) -> dict[str, Any] | None:
    if artifact is None:
        return None

    content = artifact.content
    if isinstance(content, dict):
        return content

    return {"value": content}


def _build_correction_proposals(
    artifact: RichDocumentPackageArtifact | None,
) -> list[dict[str, Any]]:
    if artifact is None:
        return []

    content = artifact.content
    if isinstance(content, list):
        return [row for row in content if isinstance(row, dict)]

    if isinstance(content, dict):
        return [content]

    return []


def _artifact_content_as_list(
    artifact: RichDocumentPackageArtifact | None,
    preferred_keys: tuple[str, ...],
) -> list[Any]:
    if artifact is None:
        return []

    return _content_as_list(artifact.content, preferred_keys)


def _content_as_list(
    content: Any,
    preferred_keys: tuple[str, ...],
) -> list[Any]:
    if isinstance(content, list):
        return content

    if isinstance(content, dict):
        for key in preferred_keys:
            value = content.get(key)
            if isinstance(value, list):
                return value

    return []


def _list_from_value(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value

    return []


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return [row for row in _list_from_value(value) if isinstance(row, dict)]


def _bbox(value: Any) -> list[float] | None:
    if not isinstance(value, list):
        return None

    result: list[float] = []
    for item in value:
        if isinstance(item, bool):
            return None

        if isinstance(item, (int, float)):
            result.append(float(item))
            continue

        return None

    return result


def _first_str(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()

        if isinstance(value, bool):
            continue

        if isinstance(value, int):
            return str(value)

    return None


def _first_int(*values: Any, fallback: int | None = None) -> int | None:
    for value in values:
        if isinstance(value, bool):
            continue

        if isinstance(value, int):
            return value

        if isinstance(value, str) and value.strip().isdigit():
            return int(value.strip())

    return fallback