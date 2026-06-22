import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.config import settings

_PASSWORD_PATTERN = re.compile(
    r"^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?`~]).{8,}$"
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def validate_password(password: str) -> None:
    """Raises ValueError if password doesn't meet the policy."""
    if len(password) < 8:
        raise ValueError("Пароль должен быть не менее 8 символов")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Пароль должен содержать хотя бы одну заглавную букву")
    if not re.search(r"\d", password):
        raise ValueError("Пароль должен содержать хотя бы одну цифру")
    if not re.search(r"[!@#$%^&*()\-_=+\[\]{};':\"\\|,.<>/?`~]", password):
        raise ValueError("Пароль должен содержать хотя бы один спецсимвол")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(subject: str, roles: list[str], permissions: list[str]) -> str:
    now = utcnow()
    exp = now + timedelta(seconds=settings.access_token_expire_seconds)
    payload: dict[str, Any] = {
        "sub": subject,
        "roles": roles,
        "permissions": permissions,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
