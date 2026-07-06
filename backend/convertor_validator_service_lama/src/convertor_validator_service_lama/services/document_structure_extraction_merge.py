from __future__ import annotations

from typing import Any

from convertor_validator_service_lama.models.document_structure_extraction import (
    DocumentProfile,
    DocumentStructureExtraction,
    ExtractionIssue,
    IssueSeverity,
    ItemClassificationExtraction,
    NumberingScopeExtraction,
    ParseItemSpan,
    SectionExtraction,
)


def merge_document_structure_extractions(
    *,
    overview_extraction: DocumentStructureExtraction | dict[str, Any] | None = None,
    scope_extractions: list[DocumentStructureExtraction | dict[str, Any]] | None = None,
    page_count: int | None = None,
) -> DocumentStructureExtraction:
    """Merge staged DocumentStructureExtraction outputs.

    This function is deterministic and does not call an LLM.

    Expected workflow:
    - overview extraction provides document_profile and numbering_scopes;
    - scope/window extractions provide item classifications and sections;
    - overlapping windows may return the same sections/items, so this layer
      deduplicates and merges them before final Pydantic validation.
    """

    extractions = _collect_extractions(
        overview_extraction=overview_extraction,
        scope_extractions=scope_extractions or [],
    )

    if not extractions:
        raise ValueError("at least one extraction is required")

    issues: list[ExtractionIssue] = []
    diagnostics: dict[str, Any] = {
        "input_extractions_count": len(extractions),
        "duplicate_numbering_scopes_merged": 0,
        "duplicate_item_classifications_merged": 0,
        "duplicate_sections_merged": 0,
        "section_source_spans_merged": 0,
        "section_content_item_indices_merged": 0,
    }

    document_profile = _select_document_profile(
        overview_extraction=_coerce_optional_extraction(overview_extraction),
        extractions=extractions,
    )
    merged_page_count = _select_page_count(
        explicit_page_count=page_count,
        extractions=extractions,
    )

    numbering_scopes = _merge_numbering_scopes(
        extractions,
        issues=issues,
        diagnostics=diagnostics,
    )
    item_classifications = _merge_item_classifications(
        extractions,
        issues=issues,
        diagnostics=diagnostics,
    )
    sections = _merge_sections(
        extractions,
        issues=issues,
        diagnostics=diagnostics,
    )

    for extraction in extractions:
        issues.extend(extraction.issues)

    diagnostics.update(
        {
            "merged_numbering_scopes_count": len(numbering_scopes),
            "merged_item_classifications_count": len(item_classifications),
            "merged_sections_count": len(sections),
            "issues_count": len(issues),
        }
    )

    return DocumentStructureExtraction(
        document_profile=document_profile,
        page_count=merged_page_count,
        numbering_scopes=numbering_scopes,
        item_classifications=item_classifications,
        sections=sections,
        issues=issues,
        diagnostics=diagnostics,
    )


def _collect_extractions(
    *,
    overview_extraction: DocumentStructureExtraction | dict[str, Any] | None,
    scope_extractions: list[DocumentStructureExtraction | dict[str, Any]],
) -> list[DocumentStructureExtraction]:
    result: list[DocumentStructureExtraction] = []

    overview = _coerce_optional_extraction(overview_extraction)
    if overview is not None:
        result.append(overview)

    for extraction in scope_extractions:
        result.append(_coerce_extraction(extraction))

    return result


def _coerce_optional_extraction(
    extraction: DocumentStructureExtraction | dict[str, Any] | None,
) -> DocumentStructureExtraction | None:
    if extraction is None:
        return None

    return _coerce_extraction(extraction)


def _coerce_extraction(
    extraction: DocumentStructureExtraction | dict[str, Any],
) -> DocumentStructureExtraction:
    if isinstance(extraction, DocumentStructureExtraction):
        return extraction

    if isinstance(extraction, dict):
        return DocumentStructureExtraction.model_validate(extraction)

    raise TypeError(f"unsupported extraction type: {type(extraction)!r}")


def _select_document_profile(
    *,
    overview_extraction: DocumentStructureExtraction | None,
    extractions: list[DocumentStructureExtraction],
) -> DocumentProfile:
    if (
        overview_extraction is not None
        and overview_extraction.document_profile != DocumentProfile.UNKNOWN
    ):
        return overview_extraction.document_profile

    for extraction in extractions:
        if extraction.document_profile != DocumentProfile.UNKNOWN:
            return extraction.document_profile

    return DocumentProfile.UNKNOWN


def _select_page_count(
    *,
    explicit_page_count: int | None,
    extractions: list[DocumentStructureExtraction],
) -> int | None:
    if explicit_page_count is not None:
        return explicit_page_count

    page_counts = [
        extraction.page_count
        for extraction in extractions
        if extraction.page_count is not None
    ]

    if not page_counts:
        return None

    return max(page_counts)


def _merge_numbering_scopes(
    extractions: list[DocumentStructureExtraction],
    *,
    issues: list[ExtractionIssue],
    diagnostics: dict[str, Any],
) -> list[NumberingScopeExtraction]:
    scopes_by_id: dict[str, NumberingScopeExtraction] = {}
    order: list[str] = []

    for extraction in extractions:
        for scope in extraction.numbering_scopes:
            existing = scopes_by_id.get(scope.namespace_id)

            if existing is None:
                scopes_by_id[scope.namespace_id] = scope
                order.append(scope.namespace_id)
                continue

            diagnostics["duplicate_numbering_scopes_merged"] += 1

            if _scope_range_signature(existing) != _scope_range_signature(scope):
                issues.append(
                    ExtractionIssue(
                        severity=IssueSeverity.WARNING,
                        code="merge_conflicting_numbering_scope",
                        message=(
                            "Numbering scope was returned more than once with "
                            f"different ranges: {scope.namespace_id}"
                        ),
                        evidence={
                            "namespace_id": scope.namespace_id,
                            "existing": _scope_range_signature(existing),
                            "incoming": _scope_range_signature(scope),
                        },
                    )
                )

            if scope.confidence > existing.confidence:
                scopes_by_id[scope.namespace_id] = scope

    return [
        scopes_by_id[namespace_id]
        for namespace_id in order
    ]


def _merge_item_classifications(
    extractions: list[DocumentStructureExtraction],
    *,
    issues: list[ExtractionIssue],
    diagnostics: dict[str, Any],
) -> list[ItemClassificationExtraction]:
    classifications_by_index: dict[int, ItemClassificationExtraction] = {}

    for extraction in extractions:
        for classification in extraction.item_classifications:
            existing = classifications_by_index.get(classification.item_index)

            if existing is None:
                classifications_by_index[classification.item_index] = classification
                continue

            diagnostics["duplicate_item_classifications_merged"] += 1

            merged = _merge_item_classification(
                existing,
                classification,
                issues=issues,
            )
            classifications_by_index[classification.item_index] = merged

    return [
        classifications_by_index[item_index]
        for item_index in sorted(classifications_by_index)
    ]


def _merge_item_classification(
    left: ItemClassificationExtraction,
    right: ItemClassificationExtraction,
    *,
    issues: list[ExtractionIssue],
) -> ItemClassificationExtraction:
    best = left if left.confidence >= right.confidence else right
    other = right if best is left else left

    merged_issues = _merge_issues(left.issues, right.issues)

    if left.role != right.role or left.is_normative_clause != right.is_normative_clause:
        issue = ExtractionIssue(
            severity=IssueSeverity.WARNING,
            code="merge_conflicting_item_classification",
            message=(
                "Overlapping extraction windows returned conflicting "
                f"classifications for item_index={left.item_index}"
            ),
            page=(
                best.source_span.page
                if best.source_span is not None
                else None
            ),
            item_index=left.item_index,
            evidence={
                "left_role": left.role,
                "right_role": right.role,
                "left_confidence": left.confidence,
                "right_confidence": right.confidence,
                "selected_role": best.role,
            },
        )
        merged_issues.append(issue)
        issues.append(issue)

    source_span = best.source_span or other.source_span

    return best.model_copy(
        update={
            "source_span": source_span,
            "issues": merged_issues,
            "confidence": max(left.confidence, right.confidence),
            "reason": best.reason,
        }
    )


def _merge_sections(
    extractions: list[DocumentStructureExtraction],
    *,
    issues: list[ExtractionIssue],
    diagnostics: dict[str, Any],
) -> list[SectionExtraction]:
    sections_by_path: dict[str, SectionExtraction] = {}
    order: list[str] = []

    for extraction in extractions:
        for section in extraction.sections:
            existing = sections_by_path.get(section.namespaced_path)

            if existing is None:
                sections_by_path[section.namespaced_path] = section
                order.append(section.namespaced_path)
                continue

            diagnostics["duplicate_sections_merged"] += 1

            merged = _merge_section(
                existing,
                section,
                issues=issues,
                diagnostics=diagnostics,
            )
            sections_by_path[section.namespaced_path] = merged

    return [
        sections_by_path[namespaced_path]
        for namespaced_path in order
    ]


def _merge_section(
    left: SectionExtraction,
    right: SectionExtraction,
    *,
    issues: list[ExtractionIssue],
    diagnostics: dict[str, Any],
) -> SectionExtraction:
    best = left if left.confidence >= right.confidence else right

    merged_content_item_indices = _merge_sorted_ints(
        left.content_item_indices,
        right.content_item_indices,
    )
    merged_source_spans = _merge_source_spans(
        left.source_spans,
        right.source_spans,
    )
    merged_issues = _merge_issues(left.issues, right.issues)

    diagnostics["section_source_spans_merged"] += max(
        0,
        len(left.source_spans) + len(right.source_spans) - len(merged_source_spans),
    )
    diagnostics["section_content_item_indices_merged"] += max(
        0,
        len(left.content_item_indices)
        + len(right.content_item_indices)
        - len(merged_content_item_indices),
    )

    if left.section_kind != right.section_kind:
        issue = ExtractionIssue(
            severity=IssueSeverity.WARNING,
            code="merge_conflicting_section_kind",
            message=(
                "Overlapping extraction windows returned conflicting "
                f"section kinds for {left.namespaced_path}"
            ),
            evidence={
                "namespaced_path": left.namespaced_path,
                "left_section_kind": left.section_kind,
                "right_section_kind": right.section_kind,
                "selected_section_kind": best.section_kind,
            },
        )
        merged_issues.append(issue)
        issues.append(issue)

    if left.clause != right.clause:
        issue = ExtractionIssue(
            severity=IssueSeverity.WARNING,
            code="merge_conflicting_section_clause",
            message=(
                "Overlapping extraction windows returned conflicting "
                f"clauses for {left.namespaced_path}"
            ),
            evidence={
                "namespaced_path": left.namespaced_path,
                "left_clause": left.clause,
                "right_clause": right.clause,
                "selected_clause": best.clause,
            },
        )
        merged_issues.append(issue)
        issues.append(issue)

    return best.model_copy(
        update={
            "content_item_indices": merged_content_item_indices,
            "source_spans": merged_source_spans,
            "issues": merged_issues,
            "confidence": max(left.confidence, right.confidence),
            "reason": best.reason,
        }
    )


def _merge_source_spans(
    left: list[ParseItemSpan],
    right: list[ParseItemSpan],
) -> list[ParseItemSpan]:
    spans_by_key: dict[tuple[Any, ...], ParseItemSpan] = {}
    order: list[tuple[Any, ...]] = []

    for span in [*left, *right]:
        key = _span_key(span)

        if key not in spans_by_key:
            spans_by_key[key] = span
            order.append(key)
            continue

        existing = spans_by_key[key]
        if existing.text_preview is None and span.text_preview is not None:
            spans_by_key[key] = span

    return [
        spans_by_key[key]
        for key in order
    ]


def _span_key(span: ParseItemSpan) -> tuple[Any, ...]:
    return (
        span.page,
        span.item_index,
        _tuple_or_none(span.bbox),
        _tuple_or_none(span.normalized_bbox),
    )


def _merge_issues(
    left: list[ExtractionIssue],
    right: list[ExtractionIssue],
) -> list[ExtractionIssue]:
    issues_by_key: dict[tuple[Any, ...], ExtractionIssue] = {}
    order: list[tuple[Any, ...]] = []

    for issue in [*left, *right]:
        key = (
            issue.severity,
            issue.code,
            issue.message,
            issue.page,
            issue.item_index,
        )

        if key not in issues_by_key:
            issues_by_key[key] = issue
            order.append(key)

    return [
        issues_by_key[key]
        for key in order
    ]


def _merge_sorted_ints(
    left: list[int],
    right: list[int],
) -> list[int]:
    return sorted(set(left) | set(right))


def _scope_range_signature(
    scope: NumberingScopeExtraction,
) -> dict[str, Any]:
    return {
        "page_start": scope.page_start,
        "page_end": scope.page_end,
        "start_item_index": scope.start_item_index,
        "end_item_index_exclusive": scope.end_item_index_exclusive,
    }


def _tuple_or_none(value: list[float] | None) -> tuple[float, ...] | None:
    if value is None:
        return None

    return tuple(value)
