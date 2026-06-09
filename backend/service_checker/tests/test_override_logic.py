"""
Тесты для api_coverage_test.py — логика all_404 оверрайда и ping_ok.

Проверяют:
- Если ≥2 не-health эндпоинтов вернули 404 (с JSON) — success откатывается, ping_ok=False
- Если ≥2 не-health эндпоинтов вернули 404 (без JSON) — ping_ok=False
- Если среди ответов есть не-404 — ping_ok остаётся True
"""
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest


@pytest.mark.asyncio
async def test_all_404_with_json_still_overrides_ping(tester, make_endpoint):
    """
    Все не-health эндпоинты вернули 404 с валидным JSON.
    Каждый эндпоинт сначала получает success=True (404 + JSON валиден),
    но оверрайд откатывает success на False, ping_ok → False.
    """
    eps = [
        make_endpoint("/api/v1/ocr/process", "ocr", method="POST"),
        make_endpoint("/api/v1/ocr/preview", "ocr", method="POST"),
    ]
    mock_404 = MagicMock(spec=httpx.Response)
    mock_404.status_code = 404
    mock_404.text = '{"error": {"code": "NOT_FOUND", "message": "Not found"}}'
    mock_404.content = b'{"error": {"code": "NOT_FOUND", "message": "Not found"}}'
    mock_404.json.return_value = {"error": {"code": "NOT_FOUND", "message": "Not found"}}

    with patch.object(tester, 'ping_service', new=AsyncMock(return_value=True)):
        with patch.object(tester.client, 'post', new=AsyncMock(return_value=mock_404)):
            tester.endpoints = {"test": eps}
            tester.context = {}
            tester.base_host = "localhost"

            result = await tester.test_service("test")

    # Все OCR-эндпоинты: success откачен на False
    for r in result.results:
        if r.endpoint.group == "ocr":
            assert r.success is False, (
                f"При всех 404 success эндпоинта должен быть False, "
                f"но success={r.success}"
            )
    # ping_ok False
    assert result.ping_ok is False
    # Passed = только health (если есть), Failed = ocr
    health_count = sum(1 for r in result.results if r.endpoint.group == "health")
    assert result.endpoints_passed == health_count
    assert result.endpoints_failed == len(result.results) - health_count


@pytest.mark.asyncio
async def test_all_404_overrides_ping(tester, make_endpoint):
    """
    Все не-health эндпоинты вернули 404 (без JSON) — ping_ok → False.
    """
    eps = [
        make_endpoint("/api/v1/ocr/process", "ocr", method="POST"),
        make_endpoint("/api/v1/ocr/preview", "ocr", method="POST"),
    ]
    mock_404 = MagicMock(spec=httpx.Response)
    mock_404.status_code = 404
    mock_404.text = ""
    mock_404.content = None
    mock_404.json.side_effect = ValueError("Not JSON")

    with patch.object(tester, 'ping_service', new=AsyncMock(return_value=True)):
        with patch.object(tester.client, 'post', new=AsyncMock(return_value=mock_404)):
            tester.endpoints = {"test": eps}
            tester.context = {}
            tester.base_host = "localhost"

            result = await tester.test_service("test")

    assert result.ping_ok is False


@pytest.mark.asyncio
async def test_mixed_responses_keeps_ping(tester, make_endpoint):
    """
    Если среди ответов есть не-404 — ping_ok остаётся True.
    """
    eps = [
        make_endpoint("/api/v1/ocr/process", "ocr", method="POST"),
        make_endpoint("/api/v1/parser/preview", "parser", method="POST"),
    ]
    mock_404 = MagicMock(spec=httpx.Response)
    mock_404.status_code = 404
    mock_404.text = ""
    mock_404.content = None
    mock_404.json.side_effect = ValueError("Not JSON")

    mock_422 = MagicMock(spec=httpx.Response)
    mock_422.status_code = 422
    mock_422.text = '{"detail": "validation error"}'
    mock_422.content = b'{"detail": "validation error"}'

    mock_post = AsyncMock()
    mock_post.side_effect = [mock_404, mock_422]

    with patch.object(tester, 'ping_service', new=AsyncMock(return_value=True)):
        with patch.object(tester.client, 'post', new=mock_post):
            tester.endpoints = {"test": eps}
            tester.context = {}
            tester.base_host = "localhost"

            result = await tester.test_service("test")

    assert result.ping_ok is True
