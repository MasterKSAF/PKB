from fastapi import APIRouter, Depends, Query, UploadFile, File
from fastapi.encoders import jsonable_encoder
from fastapi.responses import Response
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
from datetime import date
from ..dependencies.database import get_db
from ..crud import document as crud
from ..schemas.document import DocumentsResponse, DocumentsCreate, DocumentsUpdate, DocumentsStatusUpdate

router = APIRouter()

@router.get("/")
async def list_documents(
    title: Optional[str] = None,
    doc_number: Optional[str] = None,
    classifier_code: Optional[str] = None,
    status: Optional[str] = None,
    source: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    page: int = Query(1, ge=1), 
    page_size: int = Query(50, ge=1, le=100), 
    db: Session = Depends(get_db)
):
    skip = (page - 1) * page_size
    items, total = crud.get_documents(
        db, title=title, doc_number=doc_number, classifier_code=classifier_code,
        status=status, source=source, date_from=date_from, date_to=date_to,
        skip=skip, limit=page_size
    )
    validated = [DocumentsResponse.model_validate(item) for item in items]
    return success_response(
        data=jsonable_encoder(validated),
        meta={"total": total, "page": page, "page_size": page_size}
    )

@router.get("/export")
async def export_documents(
    title: Optional[str] = None,
    doc_number: Optional[str] = None,
    classifier_code: Optional[str] = None,
    status: Optional[str] = None,
    source: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    items, _ = crud.get_documents(
        db, title=title, doc_number=doc_number, classifier_code=classifier_code,
        status=status, source=source, date_from=date_from, date_to=date_to,
        skip=0, limit=10000
    )
    csv_content = "doc_id,title,doc_number,classifier_code,status\n"
    for item in items:
        csv_content += f"{item.id},{item.title},{item.doc_code},{item.classifier_code},{item.status}\n"
        
    return Response(content=csv_content, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=documents.csv"})

@router.get("/{doc_id}")
async def get_document(doc_id: UUID, db: Session = Depends(get_db)):
    db_doc = crud.get_document(db, doc_id=doc_id)
    if not db_doc:
        raise DomainException(404, "DOCUMENT_NOT_FOUND", "Документ реестра не найден")
    resp = DocumentsResponse.model_validate(db_doc)
    if db_doc.classifier_registry_purgatory:
        resp.classifier_name = db_doc.classifier_registry_purgatory.full_name
    return success_response(data=jsonable_encoder(resp))

@router.post("/")
async def create_document(document: DocumentsCreate, db: Session = Depends(get_db)):
    new_doc = crud.create_document(db, document=document)
    return success_response(
        data=jsonable_encoder(DocumentsResponse.model_validate(new_doc)),
        status_code=201
    )

@router.put("/{doc_id}")
async def update_document(doc_id: UUID, document_update: DocumentsUpdate, db: Session = Depends(get_db)):
    db_doc = crud.get_document(db, doc_id=doc_id)
    if not db_doc:
        raise DomainException(404, "DOCUMENT_NOT_FOUND", "Документ реестра не найден")
    updated = crud.update_document(db, db_document=db_doc, document_update=document_update)
    return success_response(data=jsonable_encoder(DocumentsResponse.model_validate(updated)))

@router.patch("/{doc_id}/status")
async def patch_document_status(doc_id: UUID, status_update: DocumentsStatusUpdate, db: Session = Depends(get_db)):
    db_doc = crud.get_document(db, doc_id=doc_id)
    if not db_doc:
        raise DomainException(404, "DOCUMENT_NOT_FOUND", "Документ реестра не найден")
    
    update_data = DocumentsUpdate(status=status_update.status)
    updated = crud.update_document(db, db_document=db_doc, document_update=update_data)
    return success_response(data=jsonable_encoder(DocumentsResponse.model_validate(updated)))

@router.delete("/{doc_id}")
async def delete_document(doc_id: UUID, db: Session = Depends(get_db)):
    db_doc = crud.get_document(db, doc_id=doc_id)
    if not db_doc:
        raise DomainException(404, "DOCUMENT_NOT_FOUND", "Документ реестра не найден")
    crud.delete_document(db, doc_id)
    return success_response(data={"deleted_id": str(doc_id)})

@router.post("/import")
async def import_documents(mapping: str, file: UploadFile = File(...)):
    # Stub for import
    return success_response(
        data={"inserted": 0, "updated": 0, "errors": []}
    )
