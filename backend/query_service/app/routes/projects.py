from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..models import ChatProject
from ..schemas import CreateProjectRequest, UpdateProjectRequest, ProjectResponse, DeleteProjectResponse
from ..services.auth import get_current_user

router = APIRouter(prefix="/chat/projects", tags=["projects"])


@router.post("", status_code=201, response_model=ProjectResponse)
async def create_project(
    body: CreateProjectRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    async with db.begin():
        project = ChatProject(user_id=user_id, name=body.name, description=body.description)
        db.add(project)
        await db.flush()
        await db.refresh(project)
        snap = (project.project_id, project.name, project.description, project.created_at, project.updated_at)

    pid, name, desc, cat, uat = snap
    return ProjectResponse(project_id=pid, user_id=user_id, name=name, description=desc, created_at=cat, updated_at=uat)


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    rows = (await db.execute(
        select(ChatProject).where(ChatProject.user_id == user_id).order_by(ChatProject.created_at.desc())
    )).scalars().all()
    return [ProjectResponse(project_id=p.project_id, user_id=p.user_id, name=p.name,
                            description=p.description, created_at=p.created_at, updated_at=p.updated_at)
            for p in rows]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    p = await _get_or_404(db, project_id, user_id)
    return ProjectResponse(project_id=p.project_id, user_id=p.user_id, name=p.name,
                           description=p.description, created_at=p.created_at, updated_at=p.updated_at)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    body: UpdateProjectRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    async with db.begin():
        p = await _get_or_404(db, project_id, user_id)
        if body.name is not None:
            p.name = body.name
        if body.description is not None:
            p.description = body.description
        p.updated_at = datetime.now(timezone.utc)
        await db.flush()
        await db.refresh(p)
    return ProjectResponse(project_id=p.project_id, user_id=p.user_id, name=p.name,
                           description=p.description, created_at=p.created_at, updated_at=p.updated_at)


@router.delete("/{project_id}", response_model=DeleteProjectResponse)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    async with db.begin():
        p = await _get_or_404(db, project_id, user_id)
        await db.delete(p)
    return DeleteProjectResponse(project_id=project_id, deleted_at=datetime.now(timezone.utc))


async def _get_or_404(db: AsyncSession, project_id: int, user_id: str) -> ChatProject:
    p = (await db.execute(
        select(ChatProject).where(ChatProject.project_id == project_id, ChatProject.user_id == user_id)
    )).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail={"error": {"code": "PROJECT_NOT_FOUND", "message": "Проект не найден", "details": {}}})
    return p
