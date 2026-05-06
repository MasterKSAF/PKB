#
# documents router
#

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def documents():
    return {"message": "all documents here"}