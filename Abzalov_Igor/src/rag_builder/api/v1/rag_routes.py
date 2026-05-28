from fastapi import APIRouter, Depends, Query
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from rag_builder.core.config import settings
from rag_builder.db.session import get_session
from rag_builder.models.contracts import BuildRequest, BuildResponse, DeleteResponse, StatusResponse
from rag_builder.services.indexing_service import indexing_service

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/build", response_model=BuildResponse, status_code=201)
async def build(req: BuildRequest, session: AsyncSession = Depends(get_session)) -> BuildResponse:
    logger.info("POST /rag/build document_id={} sections={}", req.document_id, len(req.sections))
    try:
        return await indexing_service.build(req, session)
    except Exception:
        logger.exception("POST /rag/build failed document_id={}", req.document_id)
        raise


@router.delete("/build/{doc_id}", response_model=DeleteResponse)
async def delete(doc_id: str, session: AsyncSession = Depends(get_session)) -> DeleteResponse:
    from uuid import UUID

    logger.info("DELETE /rag/build/{}", doc_id)
    try:
        return await indexing_service.delete(UUID(doc_id), session)
    except Exception:
        logger.exception("DELETE /rag/build failed document_id={}", doc_id)
        raise


@router.get("/build/{doc_id}/status", response_model=StatusResponse)
async def status(
    doc_id: str,
    longpoll: int = Query(default=settings.default_longpoll_seconds, ge=0, le=120),
    session: AsyncSession = Depends(get_session),
) -> StatusResponse:
    from uuid import UUID

    logger.info("GET /rag/build/{}/status longpoll={}", doc_id, longpoll)
    try:
        return await indexing_service.status(UUID(doc_id), session, longpoll)
    except Exception:
        logger.exception("GET /rag/build/{}/status failed", doc_id)
        raise
