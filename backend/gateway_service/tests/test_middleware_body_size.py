"""
Тесты MaxBodySizeMiddleware — ограничение размера тела запроса (GW-13).

Проверяются два уровня лимитов:
  - query-пути (/chat/, /text/) — строгий ~66 KB
  - остальные — 100 MB

Unit-тесты, не требуют Docker.
"""

from __future__ import annotations

import os
import sys
from unittest.mock import patch

_GATEWAY_DIR = os.path.join(os.path.dirname(__file__), "..")
if _GATEWAY_DIR not in sys.path:
    sys.path.insert(0, _GATEWAY_DIR)

import gateway.main

QUERY_PATH = "/api/v1/chat/sessions/1/messages"
DOC_PATH = "/api/v1/documents/upload"


class TestMaxBodySize:
    """Лимит тела запроса — Content-Length > limit → 413."""

    # Маленькие лимиты для тестов (не ждём 66 KB / 100 MB)
    TEST_QUERY_LIMIT = 100   # bytes — имитация строгого лимита
    TEST_GENERAL_LIMIT = 500  # bytes — имитация общего лимита

    # ------------------------------------------------------------------
    # Query-пути (/chat/, /text/)
    # ------------------------------------------------------------------

    def test_query_body_exceeds_query_limit(self, client):
        """Query-путь, тело > query-лимита → 413."""
        with patch.multiple(
            gateway.main,
            MAX_BODY_SIZE_QUERY=self.TEST_QUERY_LIMIT,
            MAX_BODY_SIZE=self.TEST_GENERAL_LIMIT,
        ):
            resp = client.post(
                QUERY_PATH,
                json={"content": "x" * (self.TEST_QUERY_LIMIT + 1)},
            )
        assert resp.status_code == 413
        assert resp.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"

    def test_query_body_within_query_limit(self, client):
        """Query-путь, тело в пределах query-лимита → не 413."""
        with patch.multiple(
            gateway.main,
            MAX_BODY_SIZE_QUERY=self.TEST_QUERY_LIMIT,
            MAX_BODY_SIZE=self.TEST_GENERAL_LIMIT,
        ):
            resp = client.post(
                QUERY_PATH,
                json={"content": "x" * (self.TEST_QUERY_LIMIT // 2)},
            )
        assert resp.status_code != 413

    def test_query_body_between_limits(self, client):
        """Query-путь, тело между query-лимитом и общим → 413 (сработал строгий)."""
        with patch.multiple(
            gateway.main,
            MAX_BODY_SIZE_QUERY=self.TEST_QUERY_LIMIT,
            MAX_BODY_SIZE=self.TEST_GENERAL_LIMIT,
        ):
            # тело > query-лимита, но < общего — должно быть 413
            body_size = self.TEST_QUERY_LIMIT + 20
            resp = client.post(
                QUERY_PATH,
                json={"content": "x" * body_size},
            )
        assert resp.status_code == 413, (
            f"Expected 413 (query limit), got {resp.status_code}"
        )

    # ------------------------------------------------------------------
    # Документные пути (не /chat/, не /text/)
    # ------------------------------------------------------------------

    def test_doc_body_exceeds_general_limit(self, client):
        """Документный путь, тело > общего лимита → 413."""
        with patch.multiple(
            gateway.main,
            MAX_BODY_SIZE_QUERY=self.TEST_QUERY_LIMIT,
            MAX_BODY_SIZE=self.TEST_GENERAL_LIMIT,
        ):
            resp = client.post(
                DOC_PATH,
                json={"content": "x" * (self.TEST_GENERAL_LIMIT + 1)},
            )
        assert resp.status_code == 413

    def test_doc_body_within_general_limit(self, client):
        """Документный путь, тело в пределах общего лимита → не 413."""
        with patch.multiple(
            gateway.main,
            MAX_BODY_SIZE_QUERY=self.TEST_QUERY_LIMIT,
            MAX_BODY_SIZE=self.TEST_GENERAL_LIMIT,
        ):
            resp = client.post(
                DOC_PATH,
                json={"content": "x" * (self.TEST_GENERAL_LIMIT // 2)},
            )
        assert resp.status_code != 413

    def test_doc_body_between_limits(self, client):
        """Документный путь, тело между лимитами → не 413 (общий лимит НЕ превышен)."""
        with patch.multiple(
            gateway.main,
            MAX_BODY_SIZE_QUERY=self.TEST_QUERY_LIMIT,
            MAX_BODY_SIZE=self.TEST_GENERAL_LIMIT,
        ):
            # тело > query-лимита, но < общего — документный путь, должно пропустить
            body_size = self.TEST_QUERY_LIMIT + 20
            resp = client.post(
                DOC_PATH,
                json={"content": "x" * body_size},
            )
        assert resp.status_code != 413, (
            f"Expected not 413 (general path, body within general limit), "
            f"got {resp.status_code}"
        )

    # ------------------------------------------------------------------
    # Крайние случаи
    # ------------------------------------------------------------------

    def test_no_body_get_request(self, client):
        """GET-запрос без тела не блокируется."""
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200

    def test_no_content_length_header(self, client):
        """Запрос без Content-Length не блокируется."""
        with patch.multiple(
            gateway.main,
            MAX_BODY_SIZE_QUERY=self.TEST_QUERY_LIMIT,
            MAX_BODY_SIZE=self.TEST_GENERAL_LIMIT,
        ):
            resp = client.post(
                QUERY_PATH,
                content=b"small body",
                headers={"Content-Type": "application/json"},
            )
        assert resp.status_code != 413
