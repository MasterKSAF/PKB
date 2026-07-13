from typing import Any

from convertor_validator_service_lama.models.rag_builder_downcast import (
    RagBuilderCompatiblePayload,
    RagBuilderCrossReferencePayload,
    RagBuilderDocumentPayload,
    RagBuilderDowncastResult,
    RagBuilderDowncastWarning,
    RagBuilderFormulaPayload,
    RagBuilderImagePayload,
    RagBuilderPayloadMetadata,
    RagBuilderReferencePayload,
    RagBuilderSectionPayload,
    RagBuilderTablePayload,
)
from convertor_validator_service_lama.models.rich_document_package import (
    RichDocumentPackage,
    RichDocumentPackageArtifact,
)
from convertor_validator_service_lama.services.reference_normalizer import (
    document_codes_equal,
    expand_gost_document_codes_from_values,
)


def downcast_rich_package_to_rag_builder(
    package: RichDocumentPackage,
) -> RagBuilderDowncastResult:
    warnings: list[RagBuilderDowncastWarning] = []

    artifacts_by_name = _artifacts_by_name(package.artifacts)

    metadata_content = _artifact_content_as_dict(artifacts_by_name.get("metadata"))
    raw_parse_content = _artifact_content_as_dict(artifacts_by_name.get("parse_raw_response"))

    document = _build_document_payload(
        package=package,
        metadata_content=metadata_content,
        raw_parse_content=raw_parse_content,
        warnings=warnings,
    )

    references_by_section = _build_references_by_section(
        artifacts_by_name.get("references"),
        current_document_code=document.document_code,
    )
    sections = _build_sections_payload(
        artifact=artifacts_by_name.get("sections"),
        structure_sections=_rich_document_structure_sections(package),
        references_by_section=references_by_section,
        warnings=warnings,
    )
    tables = _build_tables_payload(artifacts_by_name.get("tables"))
    images = _build_images_payload(artifacts_by_name.get("images"))
    formulas = _build_formulas_payload(artifacts_by_name.get("formulas"))
    cross_references = _build_cross_references_payload(
        artifacts_by_name.get("cross_references")
    )

    payload = RagBuilderCompatiblePayload(
        metadata=RagBuilderPayloadMetadata(
            notes=[
                "Downcast from rich_document_package.json.",
                "No RAG Builder network call was performed.",
            ]
        ),
        document=document,
        sections=sections,
        tables=tables,
        images=images,
        formulas=formulas,
        cross_references=cross_references,
    )

    return RagBuilderDowncastResult(payload=payload, warnings=warnings)


def _artifacts_by_name(
    artifacts: Any,
) -> dict[str, RichDocumentPackageArtifact]:
    result: dict[str, RichDocumentPackageArtifact] = {}

    if isinstance(artifacts, dict):
        for fallback_key, artifact in artifacts.items():
            if not isinstance(artifact, RichDocumentPackageArtifact):
                continue

            key = _first_str(
                getattr(artifact, "artifact_key", None),
                fallback_key if isinstance(fallback_key, str) else None,
            )
            if key is not None:
                result[key] = artifact

        return result

    if isinstance(artifacts, list):
        for artifact in artifacts:
            if not isinstance(artifact, RichDocumentPackageArtifact):
                continue

            key = _first_str(
                getattr(artifact, "artifact_key", None),
                getattr(artifact, "name", None),
            )
            if key is not None:
                result[key] = artifact

    return result


def _artifact_content_as_dict(
    artifact: RichDocumentPackageArtifact | None,
) -> dict[str, Any]:
    if artifact is None:
        return {}

    content = artifact.content
    if isinstance(content, dict):
        return content

    return {}


def _artifact_content_as_list(
    artifact: RichDocumentPackageArtifact | None,
    preferred_keys: tuple[str, ...],
) -> list[Any]:
    if artifact is None:
        return []

    content = artifact.content

    if isinstance(content, list):
        return content

    if isinstance(content, dict):
        for key in preferred_keys:
            value = content.get(key)
            if isinstance(value, list):
                return value

    return []


def _build_document_payload(
    package: RichDocumentPackage,
    metadata_content: dict[str, Any],
    raw_parse_content: dict[str, Any],
    warnings: list[RagBuilderDowncastWarning],
) -> RagBuilderDocumentPayload:
    document_code = _first_str(
        getattr(package, "doc_code", None),
        getattr(package, "source_doc_code", None),
        getattr(package, "document_code", None),
        metadata_content.get("document_code"),
        metadata_content.get("doc_code"),
        metadata_content.get("code"),
        raw_parse_content.get("document_code"),
        raw_parse_content.get("doc_code"),
    )

    title = _first_str(
        metadata_content.get("title"),
        metadata_content.get("document_title"),
        raw_parse_content.get("title"),
        raw_parse_content.get("document_title"),
    )

    page_count = _first_int(
        metadata_content.get("page_count"),
        metadata_content.get("pages"),
        raw_parse_content.get("page_count"),
        raw_parse_content.get("pages"),
    )

    if title is None:
        warnings.append(
            RagBuilderDowncastWarning(
                code="missing_document_title",
                message="Document title was not found in package metadata.",
                source_artifact="metadata",
            )
        )

    return RagBuilderDocumentPayload(
        document_code=document_code,
        title=title,
        page_count=page_count,
        source_pdf_path=getattr(package, "source_pdf_path", None),
        extra={
            "parse_job_id": package.parse_job_id,
            "final_correction_policy": getattr(
                package,
                "final_correction_policy",
                None,
            ),
        },
    )


def _build_sections_payload(
    artifact: RichDocumentPackageArtifact | None,
    structure_sections: list[Any] | None,
    references_by_section: dict[str, list[RagBuilderReferencePayload]],
    warnings: list[RagBuilderDowncastWarning],
) -> list[RagBuilderSectionPayload]:
    rows = _artifact_content_as_list(
        artifact,
        preferred_keys=("sections", "items", "data"),
    )

    if not rows:
        rows = _section_rows_from_rich_structure(structure_sections)

    if not rows:
        warnings.append(
            RagBuilderDowncastWarning(
                code="missing_sections",
                message=(
                    "No sections artifact or rich document structure sections "
                    "were found."
                ),
                source_artifact="sections",
            )
        )
        return []

    sections: list[RagBuilderSectionPayload] = []
    for index, source_row in enumerate(rows, start=1):
        row = _row_as_dict(source_row)
        if not row:
            continue

        section_id = _first_str(
            row.get("section_id"),
            row.get("id"),
            row.get("uid"),
            row.get("number"),
            fallback=f"section-{index}",
        )

        sections.append(
            RagBuilderSectionPayload(
                section_id=section_id,
                title=_first_str(row.get("title"), row.get("heading")),
                text=_section_text_from_row(row),
                level=_first_int(row.get("level"), row.get("depth")),
                page_start=_first_int(row.get("page_start"), row.get("page")),
                page_end=_first_int(row.get("page_end"), row.get("page")),
                path=_first_str(row.get("path"), row.get("section_path")),
                references=_references_for_section(
                    row,
                    section_id=section_id,
                    references_by_section=references_by_section,
                ),
                raw=row,
            )
        )

    return sections






def _references_for_section(
    row: dict[str, Any],
    *,
    section_id: str,
    references_by_section: dict[str, list[RagBuilderReferencePayload]],
) -> list[RagBuilderReferencePayload]:
    exact_references = _references_from_keys(
        _section_reference_exact_lookup_keys(row, section_id=section_id),
        references_by_section=references_by_section,
    )

    if exact_references:
        return exact_references

    return _references_from_keys(
        _section_reference_fallback_lookup_keys(row, section_id=section_id),
        references_by_section=references_by_section,
    )


def _references_from_keys(
    keys: list[str],
    *,
    references_by_section: dict[str, list[RagBuilderReferencePayload]],
) -> list[RagBuilderReferencePayload]:
    result: list[RagBuilderReferencePayload] = []
    seen: set[tuple[str | None, str | None, str | None]] = set()

    for key in keys:
        for reference in references_by_section.get(key, []):
            identity = (
                reference.target_doc_code,
                reference.type,
                reference.context,
            )
            if identity in seen:
                continue

            result.append(reference)
            seen.add(identity)

    return result


def _section_reference_exact_lookup_keys(
    row: dict[str, Any],
    *,
    section_id: str,
) -> list[str]:
    raw = row.get("raw")
    if not isinstance(raw, dict):
        raw = {}

    return _unique_strings(
        [
            section_id,
            row.get("section_id"),
            row.get("id"),
            row.get("uid"),
            raw.get("section_id"),
            raw.get("id"),
            raw.get("uid"),
        ]
    )


def _section_reference_fallback_lookup_keys(
    row: dict[str, Any],
    *,
    section_id: str,
) -> list[str]:
    raw = row.get("raw")
    if not isinstance(raw, dict):
        raw = {}

    return _unique_strings(
        [
            row.get("clause"),
            row.get("number"),
            row.get("path"),
            row.get("section_path"),
            raw.get("clause"),
            raw.get("number"),
            raw.get("namespaced_path"),
            raw.get("path"),
            raw.get("section_path"),
            section_id,
        ]
    )

def _rich_document_structure_sections(package: RichDocumentPackage) -> list[Any]:
    structure = getattr(package, "document_structure", None)
    sections = getattr(structure, "sections", None)

    if isinstance(sections, list):
        return sections

    return []


def _section_rows_from_rich_structure(value: list[Any] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for item in value or []:
        row = _row_as_dict(item)
        if row:
            rows.append(row)

    return rows


def _row_as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value

    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return model_dump(mode="json")

    return {}


def _section_text_from_row(row: dict[str, Any]) -> str | None:
    content = row.get("content")
    content_text: str | None = None

    if isinstance(content, dict):
        content_text = _first_str(
            content.get("text"),
            content.get("markdown"),
            content.get("content_text"),
            _source_span_text_preview(content.get("source_spans")),
        )
    elif isinstance(content, str):
        content_text = content

    return _first_str(
        row.get("text"),
        content_text,
        row.get("body"),
        row.get("content_text"),
    )


def _source_span_text_preview(value: Any) -> str | None:
    if not isinstance(value, list):
        return None

    previews = [
        preview
        for preview in (
            _first_str(row.get("text_preview"))
            for row in value
            if isinstance(row, dict)
        )
        if preview is not None
    ]

    if not previews:
        return None

    return "\n".join(previews)


def _build_references_by_section(
    artifact: RichDocumentPackageArtifact | None,
    *,
    current_document_code: str | None = None,
) -> dict[str, list[RagBuilderReferencePayload]]:
    rows = _artifact_content_as_list(
        artifact,
        preferred_keys=("references", "normative_references", "items", "data"),
    )

    references_by_section: dict[str, list[RagBuilderReferencePayload]] = {}

    for row in rows:
        if not isinstance(row, dict):
            continue

        section_id = _first_str(row.get("section_id"), row.get("source_section_id"))
        if section_id is None:
            continue

        reference_type = _first_str(
            row.get("reference_type"),
            row.get("type"),
            row.get("kind"),
        )
        if reference_type is None:
            continue

        context = _first_str(
            row.get("reference_text"),
            row.get("text"),
            row.get("context"),
        )

        target_codes = [
            target_doc_code
            for target_doc_code in _target_doc_codes_from_reference_row(row)
            if not document_codes_equal(target_doc_code, current_document_code)
        ]
        for target_doc_code in target_codes:
            references_by_section.setdefault(section_id, []).append(
                RagBuilderReferencePayload(
                    target_document_id=_first_int(row.get("target_document_id")),
                    target_doc_code=target_doc_code,
                    type=reference_type,
                    context=context,
                    note=_first_str(row.get("note")),
                    raw=row,
                )
            )

    return references_by_section


def _target_doc_codes_from_reference_row(row: dict[str, Any]) -> list[str]:
    raw_codes = row.get("target_document_codes")
    if isinstance(raw_codes, list):
        codes: list[str] = []
        for value in raw_codes:
            code = _first_str(value)
            if code is None:
                continue

            codes.extend(
                expand_gost_document_codes_from_values(
                    row.get("reference_text"),
                    code,
                )
            )

        if codes:
            return _unique_strings(codes)

    target_doc_code = _first_str(
        row.get("target_document_code"),
        row.get("target_doc_code"),
        row.get("document_code"),
        row.get("doc_code"),
    )
    if target_doc_code is None:
        return []

    expanded_codes = expand_gost_document_codes_from_values(
        row.get("reference_text"),
        target_doc_code,
    )
    if expanded_codes:
        return _unique_strings(expanded_codes)

    return [target_doc_code]


def _build_tables_payload(
    artifact: RichDocumentPackageArtifact | None,
) -> list[RagBuilderTablePayload]:
    rows = _artifact_content_as_list(
        artifact,
        preferred_keys=("tables", "items", "data"),
    )

    tables: list[RagBuilderTablePayload] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue

        tables.append(
            RagBuilderTablePayload(
                table_id=_first_str(
                    row.get("table_id"),
                    row.get("id"),
                    row.get("uid"),
                    fallback=f"table-{index}",
                ),
                caption=_first_str(row.get("caption"), row.get("title")),
                page=_first_int(row.get("page")),
                raw=row,
            )
        )

    return tables


def _build_images_payload(
    artifact: RichDocumentPackageArtifact | None,
) -> list[RagBuilderImagePayload]:
    rows = _artifact_content_as_list(
        artifact,
        preferred_keys=("images", "figures", "items", "data"),
    )

    images: list[RagBuilderImagePayload] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue

        images.append(
            RagBuilderImagePayload(
                image_id=_first_str(
                    row.get("image_id"),
                    row.get("figure_id"),
                    row.get("id"),
                    row.get("uid"),
                    fallback=f"image-{index}",
                ),
                caption=_first_str(row.get("caption"), row.get("title")),
                page=_first_int(row.get("page")),
                raw=row,
            )
        )

    return images


def _build_formulas_payload(
    artifact: RichDocumentPackageArtifact | None,
) -> list[RagBuilderFormulaPayload]:
    rows = _artifact_content_as_list(
        artifact,
        preferred_keys=("formulas", "items", "data"),
    )

    formulas: list[RagBuilderFormulaPayload] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue

        formulas.append(
            RagBuilderFormulaPayload(
                formula_id=_first_str(
                    row.get("formula_id"),
                    row.get("id"),
                    row.get("uid"),
                    fallback=f"formula-{index}",
                ),
                expression=_first_str(
                    row.get("expression"),
                    row.get("latex"),
                    row.get("text"),
                ),
                page=_first_int(row.get("page")),
                raw=row,
            )
        )

    return formulas


def _build_cross_references_payload(
    artifact: RichDocumentPackageArtifact | None,
) -> list[RagBuilderCrossReferencePayload]:
    rows = _artifact_content_as_list(
        artifact,
        preferred_keys=("cross_references", "references", "items", "data"),
    )

    references: list[RagBuilderCrossReferencePayload] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue

        references.append(
            RagBuilderCrossReferencePayload(
                reference_id=_first_str(
                    row.get("reference_id"),
                    row.get("id"),
                    row.get("uid"),
                    fallback=f"reference-{index}",
                ),
                source=_first_str(row.get("source"), row.get("source_id")),
                target=_first_str(row.get("target"), row.get("target_id")),
                reference_type=_first_str(
                    row.get("reference_type"),
                    row.get("type"),
                    row.get("kind"),
                ),
                raw=row,
            )
        )

    return references




def _unique_strings(values: list[Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        if not isinstance(value, str):
            continue

        cleaned = value.strip()
        if not cleaned or cleaned in seen:
            continue

        result.append(cleaned)
        seen.add(cleaned)

    return result

def _first_str(*values: Any, fallback: str | None = None) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()

    return fallback


def _first_int(*values: Any) -> int | None:
    for value in values:
        if isinstance(value, bool):
            continue

        if isinstance(value, int):
            return value

        if isinstance(value, str) and value.strip().isdigit():
            return int(value.strip())

    return None
