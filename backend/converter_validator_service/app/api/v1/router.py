from fastapi import APIRouter

from app.api.v1.endpoints import converter, validate

router = APIRouter()

router.include_router(converter.router, prefix="/converter", tags=["converter"])
router.include_router(validate.router, prefix="/validate", tags=["validate"])
