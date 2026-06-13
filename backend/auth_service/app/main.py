from fastapi import FastAPI

from app.api.v1 import audit, auth, internal, roles, users
from app.core.config import settings
from app.db.init_db import init_db
from app.db.session import AsyncSessionLocal

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Сервис аутентификации, ролей, доступов и аудита.",
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(roles.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(internal.router)


@app.on_event("startup")
async def on_startup():
    async with AsyncSessionLocal() as db:
        await init_db(db)


@app.get("/health")
def health():
    return {"status": "ok"}
