from __future__ import annotations

import json
from textwrap import dedent
from typing import Any

from convertor_validator_service_lama.models.document_structure_extraction import (
    DocumentStructureExtraction,
)


SYSTEM_PROMPT = dedent(
    """
    You are a document structure extraction agent for technical and normative
    documents.

    Your task is to classify parse items and extract the logical document
    structure. Return JSON only. The JSON must match the provided schema.

    Do not invent pages, clauses, captions, or namespaces. If something is
    uncertain, mark it as unknown and add an issue with evidence.

    Distinguish carefully between:
    - normative clauses;
    - clause continuations;
    - designation examples;
    - table rows;
    - page headers and footers;
    - table and figure captions;
    - notes and examples;
    - table of contents entries.

    A numbering scope is a region where local numbering is valid. Simple
    standards usually have one main_document scope. Compound rule books may
    have several scopes with restarted numbering.
    """
).strip()


USER_PROMPT_TEMPLATE = dedent(
    """
    Extract DocumentStructureExtraction from the following parse result.

    Document hint:
    {document_hint}

    Page count:
    {page_count}

    Output JSON schema:
    {json_schema}

    Parse items preview:
    {parse_items_preview}

    Markdown excerpt:
    {document_markdown}

    Return JSON only.
    """
).strip()


def document_structure_extraction_json_schema() -> dict[str, Any]:
    return DocumentStructureExtraction.model_json_schema()


def build_document_structure_extraction_prompt(
    *,
    document_markdown: str,
    parse_items_preview: list[dict[str, Any]],
    page_count: int | None = None,
    document_hint: str | None = None,
) -> str:
    json_schema = json.dumps(
        document_structure_extraction_json_schema(),
        ensure_ascii=False,
        indent=2,
    )
    items_json = json.dumps(
        parse_items_preview,
        ensure_ascii=False,
        indent=2,
    )

    return USER_PROMPT_TEMPLATE.format(
        document_hint=document_hint or "unknown",
        page_count=page_count if page_count is not None else "unknown",
        json_schema=json_schema,
        parse_items_preview=items_json,
        document_markdown=document_markdown,
    )
