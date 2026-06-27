from fastapi.testclient import TestClient

import rag_search.api.app as app_module
from rag_search.api.app import app


class ReadyRepository:
    def assert_read_model_ready(self) -> None:
        return None


class NotReadyRepository:
    def assert_read_model_ready(self) -> None:
        raise RuntimeError("read model is not ready")


def test_api_v1_health() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "rag_search_service_spd"


def test_legacy_health_removed() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 404


def test_ready_paths_return_200_when_read_model_is_ready(monkeypatch) -> None:
    monkeypatch.setattr(
        app_module,
        "PostgresSearchRepository",
        ReadyRepository,
    )

    client = TestClient(app)

    for path in ("/ready", "/api/v1/ready"):
        response = client.get(path)

        assert response.status_code == 200
        assert response.json()["status"] == "ready"
        assert response.json()["service"] == "rag_search_service_spd"


def test_ready_returns_503_when_read_model_is_not_ready(monkeypatch) -> None:
    monkeypatch.setattr(
        app_module,
        "PostgresSearchRepository",
        NotReadyRepository,
    )

    client = TestClient(app)

    response = client.get("/api/v1/ready")

    assert response.status_code == 503
    assert response.json()["detail"] == "read model is not ready"
