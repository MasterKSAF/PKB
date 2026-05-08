#
# All routes
#

from fastapi import APIRouter
from .endpoints import classifiers, document, terminology

routes = APIRouter()

routes.include_router(classifiers.router, prefix="/registry/classifiers", tags=["classifiers"])
routes.include_router(document.router, prefix="/registry/documents", tags=["registry document"])
routes.include_router(terminology.router, prefix="/registry/terminology", tags=["terminology"])
