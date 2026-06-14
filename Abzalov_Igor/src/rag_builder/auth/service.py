from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import HTTPException, status
from loguru import logger

from rag_builder.core.config import settings

UTC = timezone.utc


class AuthService:
    def login(self, username: str, password: str) -> dict[str, str]:
        if username != settings.auth_username or password != settings.auth_password:
            logger.warning("Auth failed username={}", username)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
        access = self._create_token(username, "access", settings.jwt_access_expire_minutes)
        refresh = self._create_token(username, "refresh", settings.jwt_refresh_expire_minutes)
        logger.info("Auth success username={}", username)
        return {"access_token": access, "refresh_token": refresh}

    def refresh(self, refresh_token: str) -> dict[str, str]:
        payload = self._decode_token(refresh_token, expected_type="refresh")
        sub = str(payload["sub"])
        access = self._create_token(sub, "access", settings.jwt_access_expire_minutes)
        logger.info("Auth refresh success username={}", sub)
        return {"access_token": access}

    def validate(self, token: str) -> dict[str, Any]:
        payload = self._decode_token(token, expected_type="access")
        logger.info("Auth validate success username={}", payload["sub"])
        return {"active": True, "sub": payload["sub"], "exp": payload["exp"], "type": payload["type"]}

    def _create_token(self, sub: str, token_type: str, ttl_minutes: int) -> str:
        now = datetime.now(UTC)
        exp = now + timedelta(minutes=ttl_minutes)
        payload = {"sub": sub, "type": token_type, "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
        return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    def _decode_token(self, token: str, expected_type: str) -> dict[str, Any]:
        try:
            payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        except jwt.ExpiredSignatureError:
            logger.warning("Auth token expired")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token expired")
        except jwt.InvalidTokenError:
            logger.warning("Auth token invalid")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")
        token_type = payload.get("type")
        if token_type != expected_type:
            logger.warning("Auth token type mismatch expected={} got={}", expected_type, token_type)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token type")
        return payload


auth_service = AuthService()
