#
# All routes
#

from fastapi import APIRouter
from endpoints import registry


routes = APIRouter()

routes.include_router(registry.router, prefix="/registry/classifiers", tags=["classifiers"])
routes.include_router(registry.router, prefix="/registry/documents", tags=["registry document"])
routes.include_router(registry.router, prefix="/registry/terminology", tags=["terminology"])
