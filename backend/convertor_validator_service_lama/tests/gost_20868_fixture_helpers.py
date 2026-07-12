import json
from pathlib import Path

from convertor_validator_service_lama.models.extract_job import ExtractJobResult


_FIXTURE_DIR = Path(__file__).parent / "fixtures" / "gost_20868_81"


def load_gost_20868_v2_chunk_container() -> dict[str, object]:
    fixture_path = _FIXTURE_DIR / "chunk_container_v2.json"
    return json.loads(fixture_path.read_text(encoding="utf-8"))


def load_gost_20868_formula_chunk_container() -> dict[str, object]:
    fixture_path = _FIXTURE_DIR / "chunk_container_formulas.json"
    return json.loads(fixture_path.read_text(encoding="utf-8"))


def gost_20868_chunk_container_extract_results(
    data: dict[str, object],
) -> dict[str, ExtractJobResult]:
    sections = data["sections"]

    rich_sections = []
    images = []
    tables = []
    notes = []
    references = []
    formulas = []

    for section in sections:
        section_id = str(section["section_id"])
        section_type = section["type"]
        clause = section["clause"]
        content = section.get("content") or {}

        if section_type == "image":
            images.append(
                {
                    "image_id": clause,
                    "caption": content.get("caption"),
                    "page": section.get("page"),
                    "raw": section,
                }
            )
            continue

        if section_type == "table":
            cells = []
            headers = content.get("headers") or []
            rows = content.get("rows") or []

            for column_index, header in enumerate(headers):
                cells.append(
                    {
                        "row_index": 0,
                        "column_index": column_index,
                        "text": header,
                    }
                )

            for row_index, row in enumerate(rows, start=1):
                for column_index, value in enumerate(row):
                    cells.append(
                        {
                            "row_index": row_index,
                            "column_index": column_index,
                            "text": value,
                        }
                    )

            tables.append(
                {
                    "table_id": clause,
                    "caption": section.get("title"),
                    "page": section.get("page"),
                    "cells": cells,
                    "raw": section,
                }
            )
            continue

        if section_type == "formula":
            formulas.append(
                {
                    "formula_id": clause,
                    "expression": content.get("text"),
                    "latex": content.get("latex"),
                    "page": section.get("page"),
                    "parameters": content.get("parameters") or [],
                    "raw": section,
                }
            )
            continue

        if clause == "note":
            notes.append(
                {
                    "note_id": clause,
                    "section_id": section_id,
                    "text": content.get("text"),
                    "page": section.get("page"),
                    "raw": section,
                }
            )
            continue

        rich_sections.append(
            {
                "section_id": section_id,
                "parent_id": (
                    str(section["parent_id"])
                    if section.get("parent_id") is not None
                    else None
                ),
                "clause": clause,
                "title": section.get("title"),
                "level": section.get("level"),
                "page_start": section.get("page"),
                "page_end": section.get("page"),
                "content": content.get("text"),
                "raw": section,
            }
        )

        for index, reference in enumerate(section.get("references") or [], start=1):
            target_document_code = reference.get("target_doc_code")
            references.append(
                {
                    "reference_id": f"{section_id}-ref-{index}",
                    "section_id": section_id,
                    "reference_text": target_document_code,
                    "target_document_code": target_document_code,
                    "reference_type": reference.get("type"),
                    "page": section.get("page"),
                    "raw": reference,
                }
            )

    return {
        "sections": _extract_result({"sections": rich_sections}),
        "images": _extract_result({"images": images}),
        "tables": _extract_result({"tables": tables}),
        "notes": _extract_result({"notes": notes}),
        "references": _extract_result({"references": references}),
        "formulas": _extract_result({"formulas": formulas}),
    }


def _extract_result(result: dict[str, object]) -> ExtractJobResult:
    return ExtractJobResult.model_construct(
        job_id="extract-job-1",
        status="COMPLETED",
        result=result,
        raw_response=result,
    )
