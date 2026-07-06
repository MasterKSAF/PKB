from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol

from convertor_validator_service_lama.models.document_structure_extraction import (
    DocumentStructureExtraction,
)
from convertor_validator_service_lama.prompts.document_structure_extraction import (
    SYSTEM_PROMPT,
    build_document_structure_extraction_prompt,
    document_structure_extraction_json_schema,
)
from convertor_validator_service_lama.services.document_structure_extraction_workflow import (
    DocumentStructureExtractionAgent,
)


class StructuredJsonPromptBackend(Protocol):
    """Backend interface for structured JSON generation.

    Implementations may use LlamaExtract, an OpenAI-compatible chat endpoint,
    a local model, or a deterministic fake in tests.
    """

    def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        json_schema: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Return a JSON object matching the requested schema."""


@dataclass(frozen=True)
class DocumentStructurePromptAgentConfig:
    document_hint: str | None = None


class DocumentStructurePromptAgent(DocumentStructureExtractionAgent):
    """Prompt-based implementation of DocumentStructureExtractionAgent.

    This adapter does not own network transport or API keys. It only converts
    staged workflow inputs into prompt/backend calls and validates backend JSON
    against DocumentStructureExtraction.
    """

    def __init__(
        self,
        *,
        backend: StructuredJsonPromptBackend,
        config: DocumentStructurePromptAgentConfig | None = None,
    ) -> None:
        self._backend = backend
        self._config = config or DocumentStructurePromptAgentConfig()

    def extract_overview(
        self,
        overview_input: dict[str, Any],
    ) -> DocumentStructureExtraction:
        return self._extract_stage(
            stage_type="overview",
            stage_input=overview_input,
        )

    def extract_scope(
        self,
        scope_input: dict[str, Any],
    ) -> DocumentStructureExtraction:
        return self._extract_stage(
            stage_type="scope",
            stage_input=scope_input,
        )

    def _extract_stage(
        self,
        *,
        stage_type: str,
        stage_input: dict[str, Any],
    ) -> DocumentStructureExtraction:
        user_prompt = build_document_structure_extraction_prompt(
            document_markdown=_stage_markdown(stage_input),
            parse_items_preview=_stage_items_preview(stage_input),
            page_count=_stage_page_count(stage_input),
            document_hint=_stage_document_hint(
                stage_type=stage_type,
                stage_input=stage_input,
                default_hint=self._config.document_hint,
            ),
        )
        json_schema = document_structure_extraction_json_schema()

        raw_output = self._backend.generate_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            json_schema=json_schema,
            metadata=_stage_metadata(
                stage_type=stage_type,
                stage_input=stage_input,
            ),
        )

        return DocumentStructureExtraction.model_validate(raw_output)


def _stage_markdown(stage_input: dict[str, Any]) -> str:
    markdown = (
        stage_input.get("markdown_excerpt")
        or stage_input.get("document_markdown")
        or ""
    )

    if isinstance(markdown, str):
        return markdown

    return str(markdown)


def _stage_items_preview(stage_input: dict[str, Any]) -> list[dict[str, Any]]:
    preview = stage_input.get("parse_items_preview")

    if not isinstance(preview, list):
        return []

    return [
        item
        for item in preview
        if isinstance(item, dict)
    ]


def _stage_page_count(stage_input: dict[str, Any]) -> int | None:
    page_count = stage_input.get("page_count")
    if isinstance(page_count, int):
        return page_count

    if isinstance(page_count, float) and page_count.is_integer():
        return int(page_count)

    return None


def _stage_document_hint(
    *,
    stage_type: str,
    stage_input: dict[str, Any],
    default_hint: str | None,
) -> str:
    parts: list[str] = []

    if default_hint:
        parts.append(default_hint)

    parts.append(f"stage_type={stage_type}")

    stage_id = stage_input.get("stage_id")
    if isinstance(stage_id, str) and stage_id:
        parts.append(f"stage_id={stage_id}")

    namespace_id = stage_input.get("namespace_id")
    if isinstance(namespace_id, str) and namespace_id:
        parts.append(f"namespace_id={namespace_id}")

    scope_title = stage_input.get("scope_title")
    if isinstance(scope_title, str) and scope_title:
        parts.append(f"scope_title={scope_title}")

    goal = stage_input.get("goal")
    if isinstance(goal, str) and goal:
        parts.append(f"goal={goal}")

    return " | ".join(parts)


def _stage_metadata(
    *,
    stage_type: str,
    stage_input: dict[str, Any],
) -> dict[str, Any]:
    metadata_keys = [
        "job_id",
        "stage_id",
        "stage_type",
        "namespace_id",
        "scope_title",
        "scope_type",
        "page_start",
        "page_end",
        "window_index",
        "windows_count",
        "items_count",
        "items_preview_count",
    ]

    metadata = {
        "agent_stage_type": stage_type,
    }

    for key in metadata_keys:
        value = stage_input.get(key)
        if value is not None:
            metadata[key] = value

    return metadata


def parse_json_object_response(value: str | bytes | dict[str, Any]) -> dict[str, Any]:
    """Parse backend response into a JSON object.

    This helper is intentionally small and deterministic. Real backends can use
    it after receiving a text response from an LLM.
    """

    if isinstance(value, dict):
        return value

    if isinstance(value, bytes):
        value = value.decode("utf-8")

    if not isinstance(value, str):
        raise TypeError(f"unsupported JSON response type: {type(value)!r}")

    parsed = json.loads(value)

    if not isinstance(parsed, dict):
        raise ValueError("structured backend response must be a JSON object")

    return parsed
