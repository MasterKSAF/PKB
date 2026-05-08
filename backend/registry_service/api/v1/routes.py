#
# All routes
#

from fastapi import APIRouter
from .endpoints import classifiers, document, terminology, common

routes = APIRouter()

routes.include_router(classifiers.router, prefix="/registry/classifiers", tags=["classifiers"])
routes.include_router(document.router, prefix="/registry/documents", tags=["documents"])
routes.include_router(terminology.router, prefix="/registry/terminology", tags=["terminology"])
routes.include_router(common.router, prefix="/registry", tags=["common"])

