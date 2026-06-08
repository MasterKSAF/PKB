"""Logging middleware для всех HTTP запросов сервиса."""

from __future__ import annotations

import logging
import time

from fastapi import FastAPI, Request

logger = logging.getLogger(__name__)


def add_request_logging_middleware(app: FastAPI) -> None:
    """Добавляет middleware, логирующий каждый входящий HTTP запрос.

    Логирует:
      - вход: метод и путь
      - выход: статус-код и время обработки
      - ошибки: тип исключения и время до сбоя
    """

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        logger.info("--> %s %s", request.method, request.url.path)
        start = time.time()

        try:
            response = await call_next(request)
        except Exception as exc:
            elapsed = time.time() - start
            logger.exception(
                "<-- %s %s | ERROR | %.3fs | %s: %s",
                request.method,
                request.url.path,
                elapsed,
                type(exc).__name__,
                exc,
            )
            raise

        elapsed = time.time() - start
        logger.info(
            "<-- %s %s | %d | %.3fs",
            request.method,
            request.url.path,
            response.status_code,
            elapsed,
        )
        return response