#
# All routes
#

from fastapi import APIRouter
from .endpoints import common, files, meridian, external

routes = APIRouter()

routes.include_router(files.router, prefix="/files", tags=["files"])
routes.include_router(meridian.router, prefix="/meridian", tags=["meridian"])
routes.include_router(external.router, prefix="/external", tags=["external"])
routes.include_router(common.router, prefix="/integration", tags=["integration"])

