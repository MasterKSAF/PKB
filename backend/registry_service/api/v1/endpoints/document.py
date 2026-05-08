from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from ..dependencies.database import get_db
from ..crud import document as crud
from ..schemas.document import DocumentsResponse, DocumentsCreate
# We can use success_response if desired since it's in builtins!

router = APIRouter()

@router.get("/", response_model=list[DocumentsResponse])
async def list_documents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    docs = crud.get_documents(db, skip=skip, limit=limit)
    return docs

@router.post("/", response_model=DocumentsResponse)
async def create_document(doc: DocumentsCreate, db: Session = Depends(get_db)):
    return crud.create_document(db, document=doc)

@router.get("/{doc_id}", response_model=DocumentsResponse)
async def get_document(doc_id: UUID, db: Session = Depends(get_db)):
    db_doc = crud.get_document(db, doc_id=doc_id)
    if db_doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return db_doc
