#
# All V1 routes
#

from fastapi import APIRouter
from .routers import documents


routes = APIRouter()

routes.include_router(documents.router, prefix="/documents", tags=["document"])
