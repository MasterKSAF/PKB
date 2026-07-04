from fastapi.testclient import TestClient

from convertor_validator_service_lama.api import app as app_module
from convertor_validator_service_lama.models.parse_job import (
    ParseJobPollingConfig,
    ParseJobResult,
    ParseJobStatus,
)


def test_parse_job_endpoint_runs_service_orchestration(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run_parse_job_with_polling(
        source_pdf_path: str,
        expand: list[str],
        polling_config: ParseJobPollingConfig,
    ) -> ParseJobResult:
        captured["source_pdf_path"] = source_pdf_path
        captured["expand"] = expand
        captured["polling_config"] = polling_config

        return ParseJobResult(
            job_id="job-123",
            status=ParseJobStatus.completed,
            markdown="# Parsed document",
            raw_response={"job": {"id": "job-123", "status": "COMPLETED"}},
        )

    monkeypatch.setattr(
        app_module,
        "run_parse_job_with_polling",
        fake_run_parse_job_with_polling,
    )

    client = TestClient(app_module.app)

    response = client.post(
        "/parse-job",
        json={
            "source_pdf_path": "document.pdf",
            "expand": ["markdown"],
            "max_attempts": 3,
            "interval_seconds": 0.0,
        },
    )

    assert response.status_code == 200
    assert response.json()["job_id"] == "job-123"
    assert response.json()["status"] == "COMPLETED"
    assert response.json()["markdown"] == "# Parsed document"

    assert captured["source_pdf_path"] == "document.pdf"
    assert captured["expand"] == ["markdown"]
    assert captured["polling_config"] == ParseJobPollingConfig(
        max_attempts=3,
        interval_seconds=0.0,
    )