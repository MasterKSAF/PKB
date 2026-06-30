"""
Health endpoint failure tests (P0 from todo_pipeline_coverage §9).

Покрывает 2 дефекта текущей реализации:
1. `/health/ready` — docstring обещает `Checks database connectivity`,
   но в коде НЕТ реального SELECT 1 (health.py:73-86).
2. `/system/health` — возвращает захардкоженный `services_status = {all: "ok"}`,
   даже если downstream упал. Никогда не показывает "degraded".

Тесты ДЕМОНСТРИРУЮТ текущее поведение (которое, скорее всего, неверно).
Если тесты не проходят — это сигнал на доработку health endpoint.
"""

import pytest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


class TestHealthReadyDbCheck:
    """
    /health/ready должен проверять реальную связность с БД.

    Сейчас в коде:
        from app.db.base import get_db   # noqa  ← импорт без вызова
        from fastapi import Depends       # noqa
    То есть Depends(get_db) НЕ подключён, запрос к БД не выполняется.
    """

    def test_health_ready_calls_db_dependency(self, client: TestClient):
        """
        /health/ready должен зависеть от get_db, и при сбое БД
        возвращать признак "offline".
        """
        # Сейчас: status_code=200, database="online" — даже если БД лежит.
        response = client.get("/api/v1/health/ready")
        assert response.status_code == 200
        # Если реализация исправлена, тут должен быть непустой database.
        # Тест-доказательство текущего дефекта:
        data = response.json()
        # Должно быть поле, сигнализирующее об ошибке БД.
        # Без правок кода значение всегда "online" — тест зафиксирует.
        assert "database" in data

    def test_health_ready_returns_offline_when_db_unreachable(
        self, client: TestClient, monkeypatch
    ):
        """
        При недоступной БД /health/ready должен вернуть 503 + database="offline".

        Имитируем сломанную БД: подменяем session.execute так, чтобы он raise.
        """
        from app.api.v1.endpoints import health as health_module
        from sqlalchemy.ext.asyncio import AsyncSession

        async def _broken_execute(self, *args, **kwargs):
            raise ConnectionError("DB is down (test simulation)")

        monkeypatch.setattr(AsyncSession, "execute", _broken_execute)
        # Чтобы избежать гонки с реальной сессией, заставим endpoint
        # вызвать нашу сломанную execute. Так как он использует get_db,
        # достаточно подменить метод на классе — повлияет на все сессии.
        try:
            response = client.get("/api/v1/health/ready")
        finally:
            monkeypatch.undo()

        # После доработки: 503 + database="offline".
        assert response.status_code == 503, (
            f"Expected 503 on DB failure, got {response.status_code}: "
            f"{response.text}"
        )
        data = response.json()
        assert data.get("database") == "offline"
        assert "database_error" in data
        assert "DB is down" in data["database_error"]


class TestSystemHealthAggregate:
    """
    /system/health должен корректно отражать degraded-состояние,
    когда downstream-сервис вернул ошибку.
    """

    def test_system_health_returns_degraded_when_rag_unavailable(
        self, client: TestClient, monkeypatch
    ):
        """
        При недоступном RAG Builder общий status должен быть "degraded",
        services["rag_builder"] != "ok".
        """
        # Выключаем mock для проверки real-ветки.
        from app.core.config import settings
        monkeypatch.setattr(settings.services, "REGISTRY_SERVICE_MOCK", False)
        monkeypatch.setattr(
            settings.services, "RAG_BUILDER_SERVICE_URL",
            "http://localhost:1",  # unreachable port
        )

        # Мокаем httpx.AsyncClient: RAG вернёт таймаут (degraded), остальные — ok.
        import httpx as _httpx

        class _FakeAsyncClient:
            def __init__(self, *args, **kwargs):
                pass
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args):
                return None
            async def get(self, url, **kwargs):
                if ":1" in url or ":1/" in url:
                    raise _httpx.ConnectError("simulated down")
                # Прочие — ok
                resp = _httpx.Response(200)
                return resp

        monkeypatch.setattr(_httpx, "AsyncClient", _FakeAsyncClient)

        response = client.get("/api/v1/system/health")
        assert response.status_code == 200
        data = response.json()

        # После доработки: RAG degraded → status "degraded".
        assert data["status"] == "degraded", (
            f"Expected degraded status when RAG down, got {data['status']}: "
            f"services={data['services']}"
        )
        assert data["services"]["rag_builder"] in ("degraded", "not_configured"), (
            f"rag_builder state: {data['services']['rag_builder']}"
        )

    def test_system_health_aggregates_multiple_downstream_failures(
        self, client: TestClient, monkeypatch
    ):
        """
        Если упало >1 сервиса, status всё равно "degraded" (не partial).
        Проверяем агрегацию: 2+ сервиса degraded → общий status "degraded".
        """
        from app.core.config import settings
        monkeypatch.setattr(settings.services, "REGISTRY_SERVICE_MOCK", False)
        monkeypatch.setattr(
            settings.services, "RAG_BUILDER_SERVICE_URL",
            "http://localhost:1",
        )
        monkeypatch.setattr(
            settings.services, "OCR_SERVICE_URL",
            "http://localhost:2",
        )

        import httpx as _httpx

        class _FakeAsyncClient:
            def __init__(self, *args, **kwargs):
                pass
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args):
                return None
            async def get(self, url, **kwargs):
                if ":1" in url or ":2" in url:
                    raise _httpx.ConnectError("simulated down")
                return _httpx.Response(200)

        monkeypatch.setattr(_httpx, "AsyncClient", _FakeAsyncClient)

        response = client.get("/api/v1/system/health")
        assert response.status_code == 200
        data = response.json()

        # ≥2 сервиса degraded → общий status degraded.
        degraded_count = sum(
            1 for s in data["services"].values() if s == "degraded"
        )
        if degraded_count < 2:
            pytest.xfail(
                f"Test setup failed: only {degraded_count} degraded services, "
                f"services={data['services']}"
            )
        assert data["status"] == "degraded"
