from fastapi.testclient import TestClient

from rag_search.api.app import app


def test_health() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "rag_search_service_spd"
