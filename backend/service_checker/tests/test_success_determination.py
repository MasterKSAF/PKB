"""
Тесты для api_coverage_test.py — определение успеха/ошибки эндпоинта.

Проверяют:
- 404 с валидным JSON — успех (документ не найден, но эндпоинт существует)
- 404 с пустым/не-JSON телом — ошибка
- 5xx — ошибка сервера
- 2xx/3xx — успех
"""
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest


@pytest.mark.asyncio
async def test_health_404_empty_body_failed(tester, make_endpoint):
    """Health endpoint с 404 и пустым телом — ошибка."""
    ep = make_endpoint("/api/v1/health", "health")
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 404
    mock_response.text = ""
    mock_response.content = None
    mock_response.json.side_effect = ValueError("Not JSON")

    with patch.object(tester, 'ping_service', new=AsyncMock(return_value=True)):
        with patch.object(tester.client, 'get', new=AsyncMock(return_value=mock_response)):
            tester._test_endpoints = {"test": [ep]}
            tester.context = {}
            tester.base_host = "localhost"

            result = await tester.test_service("test")

    assert len(result.results) == 1
    assert result.results[0].success is False


@pytest.mark.asyncio
async def test_non_health_404_empty_body_failed(tester, make_endpoint):
    """Не-health endpoint с 404 и пустым телом — ошибка."""
    ep = make_endpoint("/api/v1/ocr/process", "ocr")
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 404
    mock_response.text = ""
    mock_response.content = None
    mock_response.json.side_effect = ValueError("Not JSON")

    with patch.object(tester, 'ping_service', new=AsyncMock(return_value=True)):
        with patch.object(tester.client, 'post', new=AsyncMock(return_value=mock_response)):
            tester._test_endpoints = {"test": [ep]}
            tester.context = {}
            tester.base_host = "localhost"

            result = await tester.test_service("test")

    assert len(result.results) == 1
    assert result.results[0].success is False


@pytest.mark.asyncio
async def test_200_is_success(tester, make_endpoint):
    """200 на любом endpoint — успех."""
    ep = make_endpoint("/api/v1/ocr/process", "ocr", method="POST")
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.text = '{"status": "ok"}'
    mock_response.content = b'{"status": "ok"}'

    with patch.object(tester, 'ping_service', new=AsyncMock(return_value=True)):
        with patch.object(tester.client, 'post', new=AsyncMock(return_value=mock_response)):
            tester._test_endpoints = {"test": [ep]}
            tester.context = {}
            tester.base_host = "localhost"

            result = await tester.test_service("test")

    assert len(result.results) == 1
    assert result.results[0].success is True


@pytest.mark.asyncio
async def test_500_is_failure(tester, make_endpoint):
    """500 на любом endpoint — ошибка (тело не JSON)."""
    ep = make_endpoint("/api/v1/ocr/process", "ocr")
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_response.content = b"Internal Server Error"
    mock_response.json.side_effect = ValueError("Not JSON")

    with patch.object(tester, 'ping_service', new=AsyncMock(return_value=True)):
        with patch.object(tester.client, 'post', new=AsyncMock(return_value=mock_response)):
            tester._test_endpoints = {"test": [ep]}
            tester.context = {}
            tester.base_host = "localhost"

            result = await tester.test_service("test")

    assert len(result.results) == 1
    assert result.results[0].success is False


@pytest.mark.asyncio
async def test_500_with_json_is_success(tester, make_endpoint):
    """500 с валидным JSON — метод существует, ошибка на стороне сервера."""
    ep = make_endpoint("/api/v1/ocr/process", "ocr", method="POST")
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 500
    mock_response.text = '{"error": {"code": "INTERNAL", "message": "error"}}'
    mock_response.content = b'{"error": {"code": "INTERNAL", "message": "error"}}'
    mock_response.json.return_value = {"error": {"code": "INTERNAL", "message": "error"}}

    with patch.object(tester, 'ping_service', new=AsyncMock(return_value=True)):
        with patch.object(tester.client, 'post', new=AsyncMock(return_value=mock_response)):
            tester._test_endpoints = {"test": [ep]}
            tester.context = {}
            tester.base_host = "localhost"

            result = await tester.test_service("test")

    assert len(result.results) == 1
    assert result.results[0].success is True


@pytest.mark.asyncio
async def test_404_with_json_is_success(tester, make_endpoint):
    """
    404 с валидным JSON — успех (документ не найден, но эндпоинт существует).
    Одиночный эндпоинт — оверрайд all_404 не срабатывает (< 2 результатов).
    """
    ep = make_endpoint("/api/v1/documents/123", "documents", method="GET")
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 404
    mock_response.text = '{"error": {"code": "NOT_FOUND", "message": "Document not found"}}'
    mock_response.content = b'{"error": {"code": "NOT_FOUND", "message": "Document not found"}}'
    mock_response.json.return_value = {"error": {"code": "NOT_FOUND", "message": "Document not found"}}

    with patch.object(tester, 'ping_service', new=AsyncMock(return_value=True)):
        with patch.object(tester.client, 'get', new=AsyncMock(return_value=mock_response)):
            tester._test_endpoints = {"test": [ep]}
            tester.context = {}
            tester.base_host = "localhost"

            result = await tester.test_service("test")

    assert len(result.results) == 1
    assert result.results[0].success is True
