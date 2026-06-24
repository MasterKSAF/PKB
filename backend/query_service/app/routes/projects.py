from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..models import ChatProject
from ..schemas import (
    CreateProjectRequest, UpdateProjectRequest,
    ProjectResponse, ProjectListItem, ProjectListMeta, ProjectListResponse,
    DeleteProjectResponse,
)
from ..services.auth import get_current_user

router = APIRouter(prefix="/chat/projects", tags=["projects"])

_VALID_STATUSES = {"active", "archived", "draft"}


def _to_response(p: ChatProject, user_id: str) -> ProjectResponse:
    return ProjectResponse(
        project_id=p.project_id,
        user_id=user_id,
        code=p.code,
        name=p.name,
        description=p.description,
        status=p.status,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


@router.post("", status_code=201, response_model=ProjectResponse)
async def create_project(
    body: CreateProjectRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    if body.status not in _VALID_STATUSES:
        raise HTTPException(status_code=422, detail={"error": {"code": "INVALID_STATUS", "message": f"status должен быть одним из: {', '.join(_VALID_STATUSES)}", "details": {}}})
    try:
        async with db.begin():
            project = ChatProject(
                user_id=user_id,
                code=body.code,
                name=body.name,
                description=body.description,
                status=body.status,
            )
            db.add(project)
            await db.flush()
            await db.refresh(project)
            snap = project
    except IntegrityError:
        raise HTTPException(status_code=409, detail={"error": {"code": "DUPLICATE_PROJECT", "message": "Проект с таким code уже существует", "details": {}}})
    return _to_response(snap, user_id)


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    q = select(ChatProject).where(ChatProject.user_id == user_id, ChatProject.deleted_at.is_(None))
    if status:
        q = q.where(ChatProject.status == status)

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (await db.execute(
        q.order_by(ChatProject.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()

    return ProjectListResponse(
        items=[ProjectListItem(project_id=p.project_id, code=p.code, name=p.name, status=p.status, created_at=p.created_at) for p in rows],
        meta=ProjectListMeta(total=total, page=page, page_size=page_size),
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    p = await _get_or_404(db, project_id, user_id)
    return _to_response(p, user_id)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    body: UpdateProjectRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    if body.status is not None and body.status not in _VALID_STATUSES:
        raise HTTPException(status_code=422, detail={"error": {"code": "INVALID_STATUS", "message": f"status должен быть одним из: {', '.join(_VALID_STATUSES)}", "details": {}}})
    async with db.begin():
        p = await _get_or_404(db, project_id, user_id)
        if body.code is not None:
            p.code = body.code
        if body.name is not None:
            p.name = body.name
        if body.description is not None:
            p.description = body.description
        if body.status is not None:
            p.status = body.status
        p.updated_at = datetime.now(timezone.utc)
        await db.flush()
        await db.refresh(p)
    return _to_response(p, user_id)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    async with db.begin():
        p = await _get_or_404(db, project_id, user_id)
        await db.delete(p)


async def _get_or_404(db: AsyncSession, project_id: int, user_id: str) -> ChatProject:
    p = (await db.execute(
        select(ChatProject).where(
            ChatProject.project_id == project_id,
            ChatProject.user_id == user_id,
            ChatProject.deleted_at.is_(None),
        )
    )).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail={"error": {"code": "PROJECT_NOT_FOUND", "message": "Проект не найден", "details": {}}})
    return p
