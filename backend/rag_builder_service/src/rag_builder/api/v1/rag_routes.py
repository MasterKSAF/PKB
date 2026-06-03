from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from rag_builder.core.config import settings
from rag_builder.db.session import get_session
from rag_builder.models.contracts import BuildRequest, BuildResponse, DeleteResponse, StatusResponse
from rag_builder.services.indexing_service import indexing_service

router = APIRouter(prefix="/rag", tags=["rag"])


@router.get(
    "/health/live",
    summary="Проверка жизни сервиса (liveness)",
    description="Быстрая проверка, что процесс API запущен и отвечает.",
    responses={200: {"description": "Сервис жив."}},
)
async def health_live() -> dict[str, str]:
    logger.debug("GET /rag/health/live")
    return {"status": "ok"}


@router.get(
    "/health/ready",
    summary="Готовность сервиса (readiness)",
    description="Проверяет доступность базы данных через SQL-запрос `SELECT 1`.",
    responses={
        200: {"description": "Сервис готов, БД доступна."},
        503: {"description": "Сервис не готов: БД недоступна (`database unavailable`)."},
    },
)
async def health_ready(session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    logger.debug("GET /rag/health/ready")
    try:
        await session.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception:
        logger.exception("Health readiness failed")
        raise HTTPException(status_code=503, detail="database unavailable")


@router.post(
    "/build",
    response_model=BuildResponse,
    status_code=201,
    summary="Построить индекс документа",
    description=(
        "Запускает пайплайн индексации: валидация входа, chunking, embeddings и сохранение "
        "вектора в PostgreSQL/pgvector."
    ),
    responses={
        201: {"description": "Индексация успешно завершена."},
        500: {"description": "Внутренняя ошибка при построении индекса."},
    },
)
async def build(
    req: BuildRequest = Body(
        ...,
        openapi_examples={
            "document3_full": {
                "summary": "Полный вход по document3_for_rag.json",
                "description": "Пример полного payload со структурой metadata/document/sections/terminology.",
                "value": {
                    "metadata": {
                        "schema": "for_rag_v1",
                        "document_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                        "created_at": "2026-05-28T12:00:00Z",
                    },
                    "document": {
                        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                        "doc_code": "GOST-TEST-001",
                        "title": "Тестовый нормативный документ",
                    },
                    "sections": [
                        {
                            "section_id": 1,
                            "document_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                            "parent_id": None,
                            "clause": "1",
                            "title": None,
                            "level": 1,
                            "path": "1",
                            "page": 1,
                            "bbox": [10, 20, 200, 40],
                            "type": "section",
                            "content": {"text": "Тестовый текст раздела для индексации."},
                            "created_at": "2026-05-28T12:00:00Z",
                        }
                    ],
                    "terminology": [
                        {
                            "term": "допуск",
                            "definition": "Предельно допустимое отклонение параметра",
                            "source_clause": "1",
                            "normalized_term": "допуск",
                        }
                    ],
                    "protected_spans": [],
                    "options": {"strategy": "semantic_512"},
                },
            }
        },
    ),
    session: AsyncSession = Depends(get_session),
) -> BuildResponse:
    logger.info("POST /rag/build document_id={} sections={}", req.document_id, len(req.sections))
    try:
        return await indexing_service.build(req, session)
    except Exception:
        logger.exception("POST /rag/build failed document_id={}", req.document_id)
        raise


@router.delete(
    "/build/{doc_id}",
    response_model=DeleteResponse,
    summary="Удалить индекс документа",
    description="Удаляет все чанки и векторные данные документа из `rag.document_chunks`.",
    responses={
        200: {"description": "Индекс документа удален."},
        500: {"description": "Внутренняя ошибка при удалении индекса."},
    },
)
async def delete(doc_id: UUID, session: AsyncSession = Depends(get_session)) -> DeleteResponse:
    logger.info("DELETE /rag/build/{}", doc_id)
    try:
        return await indexing_service.delete(doc_id, session)
    except Exception:
        logger.exception("DELETE /rag/build failed document_id={}", doc_id)
        raise


@router.get(
    "/build/{doc_id}/status",
    response_model=StatusResponse,
    summary="Статус индексации документа",
    description=(
        "Возвращает текущий статус индексации (`pending/indexing/indexed/failed`). "
        "Поддерживает longpoll: ожидает обновление статуса до указанного таймаута."
    ),
    responses={
        200: {"description": "Текущий или финальный статус индексации."},
        500: {"description": "Внутренняя ошибка при чтении статуса."},
    },
)
async def status(
    doc_id: UUID,
    longpoll: int = Query(
        default=settings.default_longpoll_seconds,
        ge=0,
        le=120,
        description="Время longpoll-ожидания в секундах (0..120).",
    ),
    session: AsyncSession = Depends(get_session),
) -> StatusResponse:
    logger.info("GET /rag/build/{}/status longpoll={}", doc_id, longpoll)
    try:
        return await indexing_service.status(doc_id, session, longpoll)
    except Exception:
        logger.exception("GET /rag/build/{}/status failed", doc_id)
        raise
