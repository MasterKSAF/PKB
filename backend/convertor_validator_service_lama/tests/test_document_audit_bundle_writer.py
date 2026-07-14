import json
from pathlib import Path

from convertor_validator_service_lama.services.document_audit_bundle_writer import (
    write_document_conversion_audit_bundle,
)


def _audit_bundle() -> dict:
    return {
        "bundle_schema": "document_conversion_audit_bundle_v1",
        "input": {
            "source_pdf_path": "source.pdf",
            "document_code": "GOST TEST/20868",
            "parse_job_id": "parse-job-1",
        },
        "service_1_rich": {
            "rich_document_package": {
                "document_code": "GOST TEST/20868",
            },
            "parse_result": {
                "job_id": "parse-job-1",
            },
            "extract_artifacts": {
                "metadata": {
                    "artifact_key": "metadata",
                },
                "sections": {
                    "artifact_key": "sections",
                },
            },
            "asset_references": {
                "images": [],
                "tables": [],
                "formulas": [],
            },
            "quality_report": {
                "status": "needs_review",
            },
            "correction_proposals": [],
            "diagnostics": {
                "source": "test",
            },
        },
        "service_2_rag_builder": {
            "rag_builder_buildrequest": {
                "metadata": {
                    "schema": "schema_registry_for_rag_v2",
                    "document_id": 420000,
                },
                "document": {
                    "id": 420000,
                    "pkb_code": "-1",
                    "doc_code": "GOST TEST/20868",
                    "title": "Test document",
                },
                "sections": [],
            },
            "rag_builder_contract_gap_report": [],
            "warnings": [],
        },
        "llm_audit": {
            "audit_prompt_md": "# Audit prompt\n",
            "audit_result_md": None,
        },
    }


def test_write_document_conversion_audit_bundle_writes_expected_files(
    tmp_path: Path,
) -> None:
    manifest = write_document_conversion_audit_bundle(
        _audit_bundle(),
        output_root=tmp_path,
    )

    assert manifest["document_slug"] == "gost-test-20868"
    assert manifest["bundle_schema"] == "document_conversion_audit_bundle_v1"

    bundle_dir = tmp_path / "gost-test-20868"

    expected_files = {
        "bundle.json",
        "input/input.json",
        "input/source_path.json",
        "service_1_rich/rich_document_package.json",
        "service_1_rich/parse_result.json",
        "service_1_rich/extract_artifacts/metadata.json",
        "service_1_rich/extract_artifacts/sections.json",
        "service_1_rich/asset_references.json",
        "service_1_rich/quality_report.json",
        "service_1_rich/correction_proposals.json",
        "service_1_rich/diagnostics.json",
        "service_2_rag_builder/rag_builder_buildrequest.json",
        "service_2_rag_builder/rag_builder_contract_gap_report.json",
        "service_2_rag_builder/warnings.json",
        "llm_audit/audit_prompt.md",
        "llm_audit/audit_result.md",
        "manifest.json",
    }

    assert set(manifest["files"]) == expected_files

    input_block = json.loads(
        (bundle_dir / "input" / "input.json").read_text(encoding="utf-8")
    )
    assert input_block["document_code"] == "GOST TEST/20868"

    buildrequest = json.loads(
        (
            bundle_dir
            / "service_2_rag_builder"
            / "rag_builder_buildrequest.json"
        ).read_text(encoding="utf-8")
    )
    assert buildrequest["metadata"]["document_id"] == 420000
    assert buildrequest["document"]["pkb_code"] == "-1"

    prompt = (bundle_dir / "llm_audit" / "audit_prompt.md").read_text(
        encoding="utf-8"
    )
    assert prompt == "# Audit prompt\n"

    audit_result = (bundle_dir / "llm_audit" / "audit_result.md").read_text(
        encoding="utf-8"
    )
    assert audit_result == ""


def test_write_document_conversion_audit_bundle_accepts_explicit_slug(
    tmp_path: Path,
) -> None:
    manifest = write_document_conversion_audit_bundle(
        _audit_bundle(),
        output_root=tmp_path,
        document_slug="Custom Slug",
    )

    assert manifest["document_slug"] == "custom-slug"
    assert (tmp_path / "custom-slug" / "manifest.json").is_file()
