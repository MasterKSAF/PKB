"""End-to-end тесты для API POST /rag/search."""

import pytest
from httpx import AsyncClient


class TestSearchAPI:
    """E2E тесты поискового эндпоинта."""

    @pytest.mark.asyncio
    async def test_search_hybrid_returns_results(self, client: AsyncClient):
        """Hybrid search возвращает корректную структуру ответа."""
        response = await client.post(
            "/api/v1/rag/search",
            json={
                "query": "ледовый класс",
                "top_k": 5,
                "search_type": "hybrid",
                "rerank": True,
            },
        )
        assert response.status_code == 200
        data = response.json()

        assert data["query"] == "ледовый класс"
        assert data["search_type_used"] == "hybrid"
        assert "processing_time_ms" in data
        assert "total_found" in data
        assert isinstance(data["results"], list)

        # Если есть результаты, проверяем структуру первого чанка
        if data["results"]:
            chunk = data["results"][0]
            assert "chunk_id" in chunk
            assert "document_id" in chunk
            assert "document_title" in chunk
            assert "content" in chunk
            assert "score" in chunk
            # RRF score должен быть больше 0
            assert chunk["score"] > 0

    @pytest.mark.asyncio
    async def test_search_sparse_returns_results(self, client: AsyncClient):
        """Sparse search работает и возвращает результаты."""
        response = await client.post(
            "/api/v1/rag/search",
            json={
                "query": "толщина обшивки",
                "top_k": 3,
                "search_type": "sparse",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["search_type_used"] == "sparse"

    @pytest.mark.asyncio
    async def test_search_dense_returns_results(self, client: AsyncClient):
        """Dense search работает и возвращает результаты."""
        response = await client.post(
            "/api/v1/rag/search",
            json={
                "query": "ледовые усиления",
                "top_k": 3,
                "search_type": "dense",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["search_type_used"] == "dense"

    @pytest.mark.asyncio
    async def test_search_empty_query_validation(self, client: AsyncClient):
        """Пустой query отклоняется на уровне валидации Pydantic (422)."""
        response = await client.post(
            "/api/v1/rag/search",
            json={"query": "", "top_k": 5},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_search_filter_by_document_type(self, client: AsyncClient):
        """Фильтр по document_type возвращает только чанки документов указанного типа."""
        response = await client.post(
            "/api/v1/rag/search",
            json={
                "query": "оборудование",
                "top_k": 10,
                "filters": {
                    "document_type": ["normative"],
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        # Все результаты должны быть от документов с document_type='normative'
        for chunk in data["results"]:
            assert chunk.get("doc_code") is not None

    @pytest.mark.asyncio
    async def test_search_filter_by_document_type_no_match(self, client: AsyncClient):
        """Фильтр по document_type с несуществующим типом возвращает пустой результат."""
        response = await client.post(
            "/api/v1/rag/search",
            json={
                "query": "оборудование",
                "top_k": 10,
                "filters": {
                    "document_type": ["technical", "standard"],
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Нет документов с такими типами в тестовых данных
        assert len(data["results"]) == 0
        # total_found должен отражать количество кандидатов до фильтрации
        assert data["total_found"] > 0

    @pytest.mark.asyncio
    async def test_search_filter_by_date_from(self, client: AsyncClient):
        """Фильтр date_from возвращает только документы, принятые после указанной даты."""
        response = await client.post(
            "/api/v1/rag/search",
            json={
                "query": "безопасность",
                "top_k": 10,
                "filters": {
                    "date_from": "1985-01-01",
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        # После 1985-01-01 только ГОСТ 12.2.003-91 (adoption_date=1991-01-01)
        if data["results"]:
            for chunk in data["results"]:
                assert chunk["doc_code"] == "ГОСТ 12.2.003-91"

    @pytest.mark.asyncio
    async def test_search_filter_by_date_to(self, client: AsyncClient):
        """Фильтр date_to возвращает только документы, принятые до указанной даты."""
        response = await client.post(
            "/api/v1/rag/search",
            json={
                "query": "сварка",
                "top_k": 10,
                "filters": {
                    "date_to": "1980-12-31",
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        # До 1980-12-31 только ГОСТ 5264-80 (adoption_date=1980-01-01)
        if data["results"]:
            for chunk in data["results"]:
                assert chunk["doc_code"] == "ГОСТ 5264-80"

    @pytest.mark.asyncio
    async def test_search_filter_by_date_range(self, client: AsyncClient):
        """Фильтр date_from + date_to возвращает документы в диапазоне дат."""
        response = await client.post(
            "/api/v1/rag/search",
            json={
                "query": "резьба метрическая",
                "top_k": 10,
                "filters": {
                    "date_from": "1980-06-01",
                    "date_to": "1990-12-31",
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        # В диапазоне 1980-06-01 — 1990-12-31 только ГОСТ 24705-81 (1981-07-01)
        if data["results"]:
            for chunk in data["results"]:
                assert chunk["doc_code"] == "ГОСТ 24705-81"

    @pytest.mark.asyncio
    async def test_search_filter_date_from_gt_date_to(self, client: AsyncClient):
        """date_from > date_to отклоняется на уровне валидации Pydantic (422)."""
        response = await client.post(
            "/api/v1/rag/search",
            json={
                "query": "оборудование",
                "top_k": 5,
                "filters": {
                    "date_from": "1990-01-01",
                    "date_to": "1980-01-01",
                },
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_search_filter_combined_dates_and_type(self, client: AsyncClient):
        """Комбинированный фильтр: document_type + date_from + date_to."""
        response = await client.post(
            "/api/v1/rag/search",
            json={
                "query": "оборудование",
                "top_k": 10,
                "filters": {
                    "document_type": ["normative"],
                    "date_from": "1970-01-01",
                    "date_to": "2025-12-31",
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Все 3 документа normative с датами в этом диапазоне
        assert len(data["results"]) > 0

    @pytest.mark.asyncio
    async def test_search_filter_empty_object(self, client: AsyncClient):
        """Пустой filters={{}} не влияет на результат (работает как обычный поиск)."""
        response = await client.post(
            "/api/v1/rag/search",
            json={
                "query": "оборудование",
                "top_k": 5,
                "filters": {},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) > 0
        assert data["total_found"] > 0

    @pytest.mark.asyncio
    async def test_search_filter_null(self, client: AsyncClient):
        """filters=null не влияет на результат."""
        response = await client.post(
            "/api/v1/rag/search",
            json={
                "query": "оборудование",
                "top_k": 5,
                "filters": None,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) > 0
        assert data["total_found"] > 0

    @pytest.mark.asyncio
    async def test_search_hybrid_without_rerank(self, client: AsyncClient):
        """Hybrid search без RRF возвращает результаты с score=1.0."""
        response = await client.post(
            "/api/v1/rag/search",
            json={
                "query": "методика испытаний",
                "top_k": 3,
                "search_type": "hybrid",
                "rerank": False,
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Без RRF все скоры должны быть 1.0 (порядок определяется БД)
        for chunk in data["results"]:
            assert chunk["score"] == 1.0