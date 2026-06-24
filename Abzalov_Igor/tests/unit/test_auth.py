import pytest
from fastapi import HTTPException

from rag_builder.auth.service import AuthService


def test_auth_login_success() -> None:
    service = AuthService()
    tokens = service.login("admin", "admin")
    assert tokens["access_token"]
    assert tokens["refresh_token"]


def test_auth_login_invalid_credentials() -> None:
    service = AuthService()
    with pytest.raises(HTTPException) as exc:
        service.login("admin", "wrong")
    assert exc.value.status_code == 401


def test_auth_refresh_success() -> None:
    service = AuthService()
    tokens = service.login("admin", "admin")
    refreshed = service.refresh(tokens["refresh_token"])
    assert refreshed["access_token"]


def test_auth_validate_invalid_token() -> None:
    service = AuthService()
    with pytest.raises(HTTPException) as exc:
        service.validate("not-a-token")
    assert exc.value.status_code == 401
