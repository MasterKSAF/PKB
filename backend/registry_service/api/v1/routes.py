#
# All routes
#

from fastapi import APIRouter
from endpoints import registry


routes = APIRouter()

routes.include_router(registry.router, prefix="/registry", tags=["document"])