import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_authenticate_logs_warning_on_failure(caplog):
    import logging
    from app.services.auth_service import authenticate

    mock_db = AsyncMock()
    with patch("app.services.auth_service.get_user_by_email", return_value=None):
        with caplog.at_level(logging.WARNING, logger="app.services.auth_service"):
            with pytest.raises(HTTPException):
                await authenticate(mock_db, "bad@example.com", "wrong")
    assert "bad@example.com" in caplog.text


@pytest.mark.asyncio
async def test_authenticate_logs_info_on_success(caplog):
    import logging
    from app.services.auth_service import authenticate

    mock_db = AsyncMock()
    mock_user = MagicMock()
    mock_user.is_active = True
    with patch("app.services.auth_service.get_user_by_email", return_value=mock_user), \
         patch("app.services.auth_service.verify_password", return_value=True):
        with caplog.at_level(logging.INFO, logger="app.services.auth_service"):
            await authenticate(mock_db, "good@example.com", "right")
    assert "good@example.com" in caplog.text
