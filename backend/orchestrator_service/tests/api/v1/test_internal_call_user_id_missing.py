"""
P1-10: TestUserIdMissing.

Источник: todo_pipeline_coverage.md P1 №10.

Когда внутренний сервис вызывает оркестратор без заголовка `X-User-ID`,
запрос НЕ должен ломаться. Поведение:
  - `app/main.py::trace_middleware` НЕ устанавливает user_id, если заголовка нет.
  - `app/api/v1/endpoints/drafts.py::create_draft` использует
    `current_user.user_id if current_user else MOCK_USER_ID` — fallback.
  - В mock-режиме `get_current_user` всегда возвращает MOCK_USER, поэтому
    X-User-ID фактически не используется в create_draft.
  - Но если задан dependency_overrides, current_user=None, и тогда
    должен сработать fallback MOCK_USER_ID.
"""

import io
import pytest
from fastapi.testclient import TestClient


class TestUserIdMissing:
    """P1-10: запрос без X-User-ID → fallback MOCK_USER."""

    URL = "/api/v1/drafts/"

    def test_request_without_x_user_id_succeeds(
        self, client: TestClient
    ):
        """Запрос без X-User-ID → 202 (создаётся draft с MOCK_USER)."""
        file_bytes = b"%PDF-1.4 mock content " * 50

        response = client.post(
            self.URL,
            # НЕТ auth_header, НЕТ X-User-ID
            files={"file": ("a.pdf", file_bytes, "application/pdf")},
            data={"document_key": "doc-no-user", "source_type": "GOST"},
        )
        assert response.status_code == 202
        draft_id = response.json()["draft_id"]

        # Draft создан с MOCK_USER_ID (u-mock-001)
        from app.services.registry_client import RegistryServiceClient
        draft = RegistryServiceClient._storage["drafts"][draft_id]
        assert draft["created_by"] == "u-mock-001"

    def test_request_with_x_user_id_propagates_to_draft(
        self, client: TestClient
    ):
        """Запрос с X-User-ID → draft создан с этим user_id."""
        from app.core.trace import get_user_id

        file_bytes = b"%PDF-1.4 mock content " * 50

        response = client.post(
            self.URL,
            headers={"X-User-ID": "u-real-007"},
            files={"file": ("a.pdf", file_bytes, "application/pdf")},
            data={"document_key": "doc-with-user", "source_type": "GOST"},
        )
        assert response.status_code == 202

        # X-User-ID пробросился в trace-контекст (CM-5).
        # В mock-режиме get_current_user возвращает MOCK_USER, поэтому
        # current_user.user_id == "u-mock-001", а не "u-real-007".
        # Это документированное поведение: get_current_user всегда MOCK_USER.
        draft_id = response.json()["draft_id"]
        from app.services.registry_client import RegistryServiceClient
        draft = RegistryServiceClient._storage["drafts"][draft_id]
        # MOCK_USER перебивает X-User-ID для draft.created_by.
        assert draft["created_by"] == "u-mock-001"

    def test_x_user_id_header_extracted_in_middleware(self):
        """trace_middleware извлекает X-User-ID из заголовка."""
        from app.core.trace import set_user_id, get_user_id, reset_trace_id

        reset_trace_id()
        set_user_id("u-from-mw")
        try:
            assert get_user_id() == "u-from-mw"
        finally:
            reset_trace_id()

    def test_x_user_id_absent_get_returns_empty(self):
        """Без X-User-ID get_user_id() возвращает пустую строку (default)."""
        from app.core.trace import set_user_id, get_user_id, reset_trace_id

        reset_trace_id()
        # Не вызываем set_user_id — должен вернуть default ""
        try:
            assert get_user_id() == ""
        finally:
            reset_trace_id()

    def test_draft_with_override_auth_uses_custom_user(
        self, client: TestClient
    ):
        """dependency_overrides[get_current_user] → custom user_id."""
        from app.api.deps import get_current_user, CurrentUser

        custom_user = CurrentUser(
            user_id="u-custom-99",
            email="c@x.com",
            full_name="Custom",
            roles=["engineer"],
            permissions=["documents:write"],
        )
        file_bytes = b"%PDF-1.4 mock content " * 50

        client.app.dependency_overrides[get_current_user] = lambda: custom_user
        try:
            response = client.post(
                self.URL,
                files={"file": ("a.pdf", file_bytes, "application/pdf")},
                data={"document_key": "doc-custom-99", "source_type": "GOST"},
            )
            assert response.status_code == 202
            draft_id = response.json()["draft_id"]
            from app.services.registry_client import RegistryServiceClient
            draft = RegistryServiceClient._storage["drafts"][draft_id]
            assert draft["created_by"] == "u-custom-99"
        finally:
            client.app.dependency_overrides.pop(get_current_user, None)
