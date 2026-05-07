#
# registry terminology router
#

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def terminology():
    return {"message": "all registry terminology is here"}