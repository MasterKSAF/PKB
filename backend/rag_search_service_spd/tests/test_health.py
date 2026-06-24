from fastapi.testclient import TestClient

from rag_search.api.app import app


def test_api_v1_health() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "rag_search_service_spd"


def test_api_v1_health() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "rag_search_service_spd"

def test_legacy_health_removed() -> None:
    client = TestClient(app)

    legacy_path = "/" + "health"
    response = client.get(legacy_path)

    assert response.status_code == 404
