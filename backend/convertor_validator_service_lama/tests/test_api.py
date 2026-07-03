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
