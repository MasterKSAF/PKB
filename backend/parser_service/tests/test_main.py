import pytest
from unittest.mock import patch, AsyncMock
from app.main import app, lifespan


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_routes_endpoint(client):
    response = client.get("/routes")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any("/health" in r["path"] for r in data)


@pytest.mark.asyncio
async def test_lifespan_creates_buckets():
    """Проверяет, что при старте приложения вызывается создание бакетов."""
    with patch("app.core.minio_client.minio_client._ensure_bucket", new_callable=AsyncMock) as mock_ensure:
        async with lifespan(app):
            pass
    assert mock_ensure.call_count == 2


def test_404_handler(client):
    response = client.get("/nonexistent")
    assert response.status_code == 404
    assert "detail" in response.json()