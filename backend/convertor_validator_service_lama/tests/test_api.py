from fastapi.testclient import TestClient

from convertor_validator_service_lama.api.app import app


def test_health_returns_ok() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "convertor_validator_service_lama",
    }


def test_dry_run_describes_lama_pipeline() -> None:
    client = TestClient(app)
    response = client.get("/dry-run")

    assert response.status_code == 200
    data = response.json()
    assert data["accepted_input"] == "source_pdf"
    assert data["output_package"] == "rich_document_package.json"
    assert data["planned_steps"][2]["uses_parse_job_id"] is True
    assert data["planned_steps"][3]["name"] == "python_validator_assembler"


def test_parse_job_dry_run_returns_parse_job_contract() -> None:
    client = TestClient(app)
    response = client.post(
        "/parse-job/dry-run",
        json={"source_pdf_path": "D:/tmp/source.pdf", "document_code": "GOST-TEST"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "parse_job_dry_run"
    assert data["source_pdf_path"] == "D:/tmp/source.pdf"
    assert data["expected_parser"] == "LlamaParse"
    assert data["expected_parse_job_id"] == "dry-run-parse-job-id"
    assert data["next_step"] == "run LlamaExtract passes by parse_job_id"
    assert data["parse_payload"] == {
        "source_pdf_path": "D:/tmp/source.pdf",
        "result_format": "markdown",
        "base_url": "https://api.cloud.llamaindex.ai",
    }


def test_extract_pass_dry_run_returns_extract_payload() -> None:
    client = TestClient(app)
    response = client.post(
        "/extract-pass/dry-run",
        json={"parse_job_id": "parse-job-123", "pass_name": "sections"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "extract_pass_dry_run"
    assert data["parse_job_id"] == "parse-job-123"
    assert data["pass_name"] == "sections"
    assert data["extract_payload"] == {
        "parse_job_id": "parse-job-123",
        "pass_name": "sections",
        "base_url": "https://api.cloud.llamaindex.ai",
    }


def test_extract_passes_plan_uses_parse_job_id() -> None:
    client = TestClient(app)
    response = client.get("/extract-passes/plan")

    assert response.status_code == 200
    data = response.json()
    names = [item["name"] for item in data["passes"]]
    assert data["source"] == "parse_job_id"
    assert names == [
        "document_boundaries",
        "title_metadata",
        "table_of_contents",
        "sections",
        "tables",
        "images",
        "formulas",
        "cross_references",
        "validation_critic",
    ]
    assert all(item["uses_parse_job_id"] is True for item in data["passes"])


def test_rich_document_package_plan_keeps_final_corrections_in_python() -> None:
    client = TestClient(app)
    response = client.get("/rich-document-package/plan")

    assert response.status_code == 200
    data = response.json()
    artifact_keys = [item["artifact_key"] for item in data["artifacts"]]

    assert data["package_name"] == "rich_document_package.json"
    assert data["final_correction_policy"] == "python_validator_assembler_applies_final_corrections"
    assert "quality_report" in artifact_keys
    assert "correction_proposals" in artifact_keys
    assert data["artifacts"][-2]["source"] == "python_validator"
    assert data["artifacts"][-1]["source"] == "python_validator"
