from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


_SLUG_SEPARATOR_RE = re.compile(r"[^\w.-]+", re.UNICODE)
_REPEATED_DASH_RE = re.compile(r"-+")


def write_document_conversion_audit_bundle(
    bundle: dict[str, Any],
    *,
    output_root: str | Path,
    document_slug: str | None = None,
) -> dict[str, Any]:
    slug = _build_document_slug(bundle, document_slug)
    bundle_dir = Path(output_root) / slug
    bundle_dir.mkdir(parents=True, exist_ok=True)

    written_files: list[str] = []

    _write_json(bundle_dir / "bundle.json", bundle)
    written_files.append("bundle.json")

    input_block = _as_dict(bundle.get("input"))
    service_1 = _as_dict(bundle.get("service_1_rich"))
    service_2 = _as_dict(bundle.get("service_2_rag_builder"))
    llm_audit = _as_dict(bundle.get("llm_audit"))

    _write_json(bundle_dir / "input" / "input.json", input_block)
    written_files.append("input/input.json")

    _write_json(
        bundle_dir / "input" / "source_path.json",
        {
            "source_pdf_path": input_block.get("source_pdf_path"),
        },
    )
    written_files.append("input/source_path.json")

    _write_json(
        bundle_dir / "service_1_rich" / "rich_document_package.json",
        service_1.get("rich_document_package"),
    )
    written_files.append("service_1_rich/rich_document_package.json")

    _write_json(
        bundle_dir / "service_1_rich" / "parse_result.json",
        service_1.get("parse_result"),
    )
    written_files.append("service_1_rich/parse_result.json")

    extract_artifacts = _as_dict(service_1.get("extract_artifacts"))
    for artifact_key in sorted(extract_artifacts):
        artifact_file = f"{_safe_file_stem(artifact_key)}.json"
        _write_json(
            bundle_dir / "service_1_rich" / "extract_artifacts" / artifact_file,
            extract_artifacts[artifact_key],
        )
        written_files.append(f"service_1_rich/extract_artifacts/{artifact_file}")

    _write_json(
        bundle_dir / "service_1_rich" / "asset_references.json",
        service_1.get("asset_references"),
    )
    written_files.append("service_1_rich/asset_references.json")

    _write_json(
        bundle_dir / "service_1_rich" / "quality_report.json",
        service_1.get("quality_report"),
    )
    written_files.append("service_1_rich/quality_report.json")

    _write_json(
        bundle_dir / "service_1_rich" / "correction_proposals.json",
        service_1.get("correction_proposals"),
    )
    written_files.append("service_1_rich/correction_proposals.json")

    _write_json(
        bundle_dir / "service_1_rich" / "diagnostics.json",
        service_1.get("diagnostics"),
    )
    written_files.append("service_1_rich/diagnostics.json")

    _write_json(
        bundle_dir / "service_2_rag_builder" / "rag_builder_buildrequest.json",
        service_2.get("rag_builder_buildrequest"),
    )
    written_files.append("service_2_rag_builder/rag_builder_buildrequest.json")

    _write_json(
        bundle_dir
        / "service_2_rag_builder"
        / "rag_builder_contract_gap_report.json",
        service_2.get("rag_builder_contract_gap_report"),
    )
    written_files.append(
        "service_2_rag_builder/rag_builder_contract_gap_report.json"
    )

    _write_json(
        bundle_dir / "service_2_rag_builder" / "warnings.json",
        service_2.get("warnings"),
    )
    written_files.append("service_2_rag_builder/warnings.json")

    _write_text(
        bundle_dir / "llm_audit" / "audit_prompt.md",
        _as_str(llm_audit.get("audit_prompt_md")),
    )
    written_files.append("llm_audit/audit_prompt.md")

    _write_text(
        bundle_dir / "llm_audit" / "audit_result.md",
        _as_str(llm_audit.get("audit_result_md")),
    )
    written_files.append("llm_audit/audit_result.md")

    manifest = {
        "bundle_schema": bundle.get("bundle_schema"),
        "document_slug": slug,
        "bundle_dir": str(bundle_dir),
        "files": sorted([*written_files, "manifest.json"]),
    }

    _write_json(bundle_dir / "manifest.json", manifest)

    return manifest


def _build_document_slug(
    bundle: dict[str, Any],
    document_slug: str | None,
) -> str:
    if document_slug:
        return _safe_file_stem(document_slug)

    input_block = _as_dict(bundle.get("input"))

    for value in (
        input_block.get("document_code"),
        input_block.get("parse_job_id"),
        "document",
    ):
        if isinstance(value, str) and value.strip():
            return _safe_file_stem(value)

    return "document"


def _safe_file_stem(value: str) -> str:
    slug = _SLUG_SEPARATOR_RE.sub("-", value.strip().lower())
    slug = _REPEATED_DASH_RE.sub("-", slug).strip("-._")

    return slug or "document"


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_str(value: Any) -> str:
    return value if isinstance(value, str) else ""
