"""
P1-7: TestIdempotencyCachePersistence.

Источник: todo_pipeline_coverage.md P1 №7, docstring in `app/api/v1/endpoints/drafts.py`:
  _IDEMPOTENCY_CACHE = {}  # in-memory dict, не переживает рестарт
  IDEMPOTENCY_TTL_SECONDS = 3600

Тесты проверяют дефект, документированный в
`todo_pipeline_coverage.md` §26: idempotency-cache — in-memory dict,
а не Redis. Ключ не переживает рестарт процесса.
"""

import pytest
from fastapi.testclient import TestClient


class TestIdempotencyCachePersistence:
    """P1-7: кэш идемпотентности не переживает рестарт процесса.

    Поведение: `_IDEMPOTENCY_CACHE` — module-level dict в
    `app/api/v1/endpoints/drafts.py`. При рестарте процесса Python
    теряет все in-memory state, и тот же Idempotency-Key
    не сработает как hit.
    """

    URL = "/api/v1/drafts/"

    def test_cache_state_visible_in_module(
        self, client: TestClient, auth_header: dict
    ):
        """Sanity-check: после успешного POST ключ лежит в in-memory dict."""
        from app.api.v1.endpoints.drafts import _IDEMPOTENCY_CACHE

        _IDEMPOTENCY_CACHE.clear()
        file_bytes = b"%PDF-1.4 mock content " * 50

        response = client.post(
            self.URL,
            headers={**auth_header, "Idempotency-Key": "test-persist-1"},
            files={"file": ("a.pdf", file_bytes, "application/pdf")},
            data={"document_key": "doc-persist-1", "source_type": "GOST"},
        )
        assert response.status_code == 202
        draft_id_1 = response.json()["draft_id"]

        # Кэш содержит ключ
        assert "test-persist-1" in _IDEMPOTENCY_CACHE
        assert _IDEMPOTENCY_CACHE["test-persist-1"]["draft_id"] == draft_id_1

    def test_cache_lost_on_simulated_restart(
        self, client: TestClient, auth_header: dict
    ):
        """Симулируем рестарт: очищаем _IDEMPOTENCY_CACHE.
        Тот же ключ создаёт НОВЫЙ draft, а не возвращает кэшированный 200.
        """
        from app.api.v1.endpoints.drafts import _IDEMPOTENCY_CACHE

        _IDEMPOTENCY_CACHE.clear()
        key = "test-persist-2"
        file_bytes = b"%PDF-1.4 mock content " * 50

        # Первый запрос
        r1 = client.post(
            self.URL,
            headers={**auth_header, "Idempotency-Key": key},
            files={"file": ("a.pdf", file_bytes, "application/pdf")},
            data={"document_key": "doc-persist-2", "source_type": "GOST"},
        )
        assert r1.status_code == 202
        draft_id_1 = r1.json()["draft_id"]

        # Повторный запрос БЕЗ очистки — idempotent hit
        r2 = client.post(
            self.URL,
            headers={**auth_header, "Idempotency-Key": key},
            files={"file": ("a.pdf", file_bytes, "application/pdf")},
            data={"document_key": "doc-persist-2", "source_type": "GOST"},
        )
        assert r2.status_code == 200
        assert r2.json()["draft_id"] == draft_id_1

        # === Симулируем рестарт: очищаем кэш ===
        _IDEMPOTENCY_CACHE.clear()

        # Третий запрос — после «рестарта» кэш пуст
        # С включённой детекцией дублей (D1) тот же файл детектится как дубликат
        r3 = client.post(
            self.URL,
            headers={**auth_header, "Idempotency-Key": key},
            files={"file": ("a.pdf", file_bytes, "application/pdf")},
            data={"document_key": "doc-persist-2", "source_type": "GOST"},
        )
        # Тот же файл уже существует в Draft — метод детекции дублей (D1)
        # блокирует повторную загрузку как DUPLICATE_FILE
        assert r3.status_code == 409, (
            "После рестарта кэш пуст. Тот же файл детектится как дубликат. "
            "Статус: %s (ожидался 409)." % r3.status_code
        )
        detail = r3.json()
        assert detail.get("detail", {}).get("error", {}).get("code") == "DUPLICATE_FILE"

    def test_cache_is_module_level_dict(self):
        """_IDEMPOTENCY_CACHE — module-level dict (НЕ Redis)."""
        from app.api.v1.endpoints.drafts import _IDEMPOTENCY_CACHE

        assert isinstance(_IDEMPOTENCY_CACHE, dict)

    def test_cache_persists_across_requests_in_same_process(
        self, client: TestClient, auth_header: dict
    ):
        """Контр-тест: в одном процессе кэш работает (3 запроса с одним ключом
        → первый 202, остальные 200 с тем же draft_id).
        """
        from app.api.v1.endpoints.drafts import _IDEMPOTENCY_CACHE

        _IDEMPOTENCY_CACHE.clear()
        key = "test-persist-3"
        file_bytes = b"%PDF-1.4 mock content " * 50

        responses = []
        for _ in range(3):
            r = client.post(
                self.URL,
                headers={**auth_header, "Idempotency-Key": key},
                files={"file": ("a.pdf", file_bytes, "application/pdf")},
                data={"document_key": "doc-persist-3", "source_type": "GOST"},
            )
            responses.append(r)

        assert responses[0].status_code == 202
        for r in responses[1:]:
            assert r.status_code == 200
            assert r.json()["draft_id"] == responses[0].json()["draft_id"]

    def test_ttl_constant_defined(self):
        """TTL=3600 сек (1 час) зафиксирован в константе."""
        from app.api.v1.endpoints.drafts import IDEMPOTENCY_TTL_SECONDS

        assert IDEMPOTENCY_TTL_SECONDS == 3600
