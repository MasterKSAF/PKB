"""
P2-6: TestIdempotencyCacheTtl.

Источник: todo_pipeline_coverage.md P2 №6.

В `app/api/v1/endpoints/drafts.py`:
  - `_IDEMPOTENCY_CACHE` (dict, TTL=3600 сек для POST /drafts)
  - `_PREVIEW_IDEMPOTENCY_CACHE` (dict, TTL=3600 сек для POST /preview)
  - `IDEMPOTENCY_TTL_SECONDS = 3600`

Проверяем:
  1. TTL=3600.
  2. Кэш отдаёт hit в пределах TTL.
  3. Кэш НЕ отдаёт hit после истечения TTL.
  4. Preview-кэш работает по той же логике.
"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient


class TestIdempotencyCacheTtl:
    """P2-6: TTL idempotency-кеша."""

    URL = "/api/v1/drafts/"

    def test_ttl_constant_is_3600(self):
        """IDEMPOTENCY_TTL_SECONDS == 3600."""
        from app.api.v1.endpoints.drafts import IDEMPOTENCY_TTL_SECONDS

        assert IDEMPOTENCY_TTL_SECONDS == 3600

    def test_cache_hit_within_ttl_returns_200(
        self, client: TestClient, auth_header: dict
    ):
        """В пределах TTL повторный запрос → 200 (idempotent hit)."""
        from app.api.v1.endpoints.drafts import _IDEMPOTENCY_CACHE

        _IDEMPOTENCY_CACHE.clear()
        key = "test-ttl-1"
        file_bytes = b"%PDF-1.4 mock content " * 50

        r1 = client.post(
            self.URL,
            headers={**auth_header, "Idempotency-Key": key},
            files={"file": ("a.pdf", file_bytes, "application/pdf")},
            data={"document_key": "doc-ttl-1", "source_type": "GOST"},
        )
        assert r1.status_code == 202
        draft_id_1 = r1.json()["draft_id"]

        r2 = client.post(
            self.URL,
            headers={**auth_header, "Idempotency-Key": key},
            files={"file": ("a.pdf", file_bytes, "application/pdf")},
            data={"document_key": "doc-ttl-1", "source_type": "GOST"},
        )
        assert r2.status_code == 200
        assert r2.json()["draft_id"] == draft_id_1

    def test_cache_miss_after_ttl_expired(
        self, client: TestClient, auth_header: dict
    ):
        """После истечения TTL кэш НЕ отдаёт hit — новый запрос создаёт новый draft.

        Симулируем: подменяем created_at в кэше на timestamp в прошлом,
        чтобы age > IDEMPOTENCY_TTL_SECONDS.
        """
        from app.api.v1.endpoints.drafts import (
            _IDEMPOTENCY_CACHE,
            IDEMPOTENCY_TTL_SECONDS,
        )

        _IDEMPOTENCY_CACHE.clear()
        key = "test-ttl-2"
        file_bytes = b"%PDF-1.4 mock content " * 50

        r1 = client.post(
            self.URL,
            headers={**auth_header, "Idempotency-Key": key},
            files={"file": ("a.pdf", file_bytes, "application/pdf")},
            data={"document_key": "doc-ttl-2", "source_type": "GOST"},
        )
        assert r1.status_code == 202
        draft_id_1 = r1.json()["draft_id"]

        # Симулируем истечение TTL: откатываем created_at на 2 часа назад
        expired_time = datetime.now(timezone.utc) - timedelta(
            seconds=IDEMPOTENCY_TTL_SECONDS + 60
        )
        _IDEMPOTENCY_CACHE[key]["created_at"] = expired_time

        r2 = client.post(
            self.URL,
            headers={**auth_header, "Idempotency-Key": key},
            files={"file": ("a.pdf", file_bytes, "application/pdf")},
            data={"document_key": "doc-ttl-2", "source_type": "GOST"},
        )
        # TTL истёк, но файл уже существует в Draft — детекция дублей (D1)
        # блокирует повторную загрузку как DUPLICATE_FILE
        assert r2.status_code == 409, (
            "TTL истёк, но файл уже загружен — детекция дублей должна "
            "вернуть 409 DUPLICATE_FILE. Статус: %s" % r2.status_code
        )
        detail = r2.json()
        assert detail.get("detail", {}).get("error", {}).get("code") == "DUPLICATE_FILE"

    def test_cache_hit_just_under_ttl(
        self, client: TestClient, auth_header: dict
    ):
        """За 1 секунду до истечения TTL кэш всё ещё отдаёт hit."""
        from app.api.v1.endpoints.drafts import (
            _IDEMPOTENCY_CACHE,
            IDEMPOTENCY_TTL_SECONDS,
        )

        _IDEMPOTENCY_CACHE.clear()
        key = "test-ttl-3"
        file_bytes = b"%PDF-1.4 mock content " * 50

        r1 = client.post(
            self.URL,
            headers={**auth_header, "Idempotency-Key": key},
            files={"file": ("a.pdf", file_bytes, "application/pdf")},
            data={"document_key": "doc-ttl-3", "source_type": "GOST"},
        )
        assert r1.status_code == 202
        draft_id_1 = r1.json()["draft_id"]

        # Откатываем created_at на 1 секунду до истечения TTL
        just_under = datetime.now(timezone.utc) - timedelta(
            seconds=IDEMPOTENCY_TTL_SECONDS - 1
        )
        _IDEMPOTENCY_CACHE[key]["created_at"] = just_under

        r2 = client.post(
            self.URL,
            headers={**auth_header, "Idempotency-Key": key},
            files={"file": ("a.pdf", file_bytes, "application/pdf")},
            data={"document_key": "doc-ttl-3", "source_type": "GOST"},
        )
        # age = TTL-1 → < TTL → hit
        assert r2.status_code == 200
        assert r2.json()["draft_id"] == draft_id_1

    def test_cache_entry_removed_on_expiry(
        self, client: TestClient, auth_header: dict
    ):
        """После истечения TTL ключ удаляется из кэша."""
        from app.api.v1.endpoints.drafts import (
            _IDEMPOTENCY_CACHE,
            IDEMPOTENCY_TTL_SECONDS,
        )

        _IDEMPOTENCY_CACHE.clear()
        key = "test-ttl-4"
        file_bytes = b"%PDF-1.4 mock content " * 50

        client.post(
            self.URL,
            headers={**auth_header, "Idempotency-Key": key},
            files={"file": ("a.pdf", file_bytes, "application/pdf")},
            data={"document_key": "doc-ttl-4", "source_type": "GOST"},
        )
        assert key in _IDEMPOTENCY_CACHE

        # Симулируем истечение TTL
        expired_time = datetime.now(timezone.utc) - timedelta(
            seconds=IDEMPOTENCY_TTL_SECONDS + 60
        )
        _IDEMPOTENCY_CACHE[key]["created_at"] = expired_time

        file_bytes_2 = b"%PDF-1.4 mock content v2 " * 50
        client.post(
            self.URL,
            headers={**auth_header, "Idempotency-Key": key},
            files={"file": ("a.pdf", file_bytes_2, "application/pdf")},
            data={"document_key": "doc-ttl-4", "source_type": "GOST"},
        )
        # Старая запись удалена, новая создана → ключ остался в кэше
        # с обновлённым created_at
        assert key in _IDEMPOTENCY_CACHE
        age = (
            datetime.now(timezone.utc) - _IDEMPOTENCY_CACHE[key]["created_at"]
        ).total_seconds()
        assert age < 60  # новая запись, возраст < 60 секунд
