from __future__ import annotations

from fastapi import APIRouter

from rag_builder.auth.service import auth_service
from rag_builder.models.contracts import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
    TokenValidationRequest,
    TokenValidationResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse, summary="Вход и получение access/refresh токенов")
async def login(req: LoginRequest) -> LoginResponse:
    tokens = auth_service.login(req.username, req.password)
    return LoginResponse(access_token=tokens["access_token"], refresh_token=tokens["refresh_token"])


@router.post("/refresh", response_model=RefreshResponse, summary="Обновление access токена")
async def refresh(req: RefreshRequest) -> RefreshResponse:
    token = auth_service.refresh(req.refresh_token)
    return RefreshResponse(access_token=token["access_token"])


@router.post("/validate", response_model=TokenValidationResponse, summary="Валидация access токена")
async def validate(req: TokenValidationRequest) -> TokenValidationResponse:
    result = auth_service.validate(req.access_token)
    return TokenValidationResponse(active=True, sub=str(result["sub"]), exp=int(result["exp"]), type="access")
