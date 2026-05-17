from fastapi import APIRouter, Depends, Query, UploadFile, File
from fastapi.encoders import jsonable_encoder
from fastapi.responses import Response
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
from datetime import date
from ..dependencies.database import get_db
from ..crud import document as crud
from ..schemas.document import DocumentsPurgatoryResponse, DocumentsPurgatoryCreate, DocumentsPurgatoryUpdate, DocumentsPurgatoryStatusUpdate

router = APIRouter()

@router.get("/")
async def list_documents(
    title: Optional[str] = None,
    doc_code: Optional[str] = None,
    source_type: Optional[str] = None,
    mks_oks_code: Optional[str] = None,
    okstu_code: Optional[str] = None,
    status: Optional[str] = None,
    era: Optional[str] = None,
    validity_status: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    issuing_body: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    page: int = Query(1, ge=1), 
    page_size: int = Query(50, ge=1, le=100), 
    db: Session = Depends(get_db)
):
    skip = (page - 1) * page_size
    items, total = crud.get_documents(
        db, title=title, doc_code=doc_code, source_type=source_type,
        mks_oks_code=mks_oks_code, okstu_code=okstu_code, status=status,
        era=era, validity_status=validity_status, jurisdiction=jurisdiction,
        issuing_body=issuing_body, date_from=date_from, date_to=date_to,
        skip=skip, limit=page_size
    )
    validated = [DocumentsPurgatoryResponse.model_validate(item) for item in items]
    return success_response(
        data=jsonable_encoder(validated),
        meta={"total": total, "page": page, "page_size": page_size}
    )

@router.get("/export")
async def export_documents(
    title: Optional[str] = None,
    doc_code: Optional[str] = None,
    source_type: Optional[str] = None,
    mks_oks_code: Optional[str] = None,
    okstu_code: Optional[str] = None,
    status: Optional[str] = None,
    era: Optional[str] = None,
    validity_status: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    issuing_body: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    items, _ = crud.get_documents(
        db, title=title, doc_code=doc_code, source_type=source_type,
        mks_oks_code=mks_oks_code, okstu_code=okstu_code, status=status,
        era=era, validity_status=validity_status, jurisdiction=jurisdiction,
        issuing_body=issuing_body, date_from=date_from, date_to=date_to,
        skip=0, limit=10000
    )
    csv_content = "id,title,doc_code,source_type,era,validity_status,jurisdiction,issuing_body,mks_oks_code,okstu_code,status\n"
    for item in items:
        csv_content += f"{item.id},{item.title},{item.doc_code},{item.source_type},{item.era},{item.validity_status},{item.jurisdiction},{item.issuing_body},{item.mks_oks_code},{item.okstu_code},{item.status}\n"
        
    return Response(content=csv_content, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=documents.csv"})

@router.get("/{doc_id}")
async def get_document(doc_id: UUID, db: Session = Depends(get_db)):
    db_doc = crud.get_document(db, doc_id=doc_id)
    if not db_doc:
        raise DomainException(404, "DOCUMENT_NOT_FOUND", "Документ реестра не найден")
    resp = DocumentsPurgatoryResponse.model_validate(db_doc)
    if db_doc.mks_classifier_purgatory:
        resp.mks_name = db_doc.mks_classifier_purgatory.full_name
    if db_doc.okstu_classifier_purgatory:
        resp.okstu_name = db_doc.okstu_classifier_purgatory.full_name
    return success_response(data=jsonable_encoder(resp))

@router.post("/")
async def create_document(document: DocumentsPurgatoryCreate, db: Session = Depends(get_db)):
    new_doc = crud.create_document(db, document=document)
    return success_response(
        data=jsonable_encoder(DocumentsPurgatoryResponse.model_validate(new_doc)),
        status_code=201
    )

@router.put("/{doc_id}")
async def update_document(doc_id: UUID, document_update: DocumentsPurgatoryUpdate, db: Session = Depends(get_db)):
    db_doc = crud.get_document(db, doc_id=doc_id)
    if not db_doc:
        raise DomainException(404, "DOCUMENT_NOT_FOUND", "Документ реестра не найден")
    updated = crud.update_document(db, db_document=db_doc, document_update=document_update)
    return success_response(data=jsonable_encoder(DocumentsPurgatoryResponse.model_validate(updated)))

@router.patch("/{doc_id}/status")
async def patch_document_status(doc_id: UUID, status_update: DocumentsPurgatoryStatusUpdate, db: Session = Depends(get_db)):
    db_doc = crud.get_document(db, doc_id=doc_id)
    if not db_doc:
        raise DomainException(404, "DOCUMENT_NOT_FOUND", "Документ реестра не найден")
    
    update_data = DocumentsPurgatoryUpdate(status=status_update.status)
    updated = crud.update_document(db, db_document=db_doc, document_update=update_data)
    return success_response(
        data=jsonable_encoder({
            "id": updated.id,
            "status": updated.status,
            "previous_status": db_doc.status,
            "updated_at": updated.updated_at
        })
    )

@router.get("/{doc_id}/history")
async def get_document_history(doc_id: UUID, db: Session = Depends(get_db)):
    db_doc = crud.get_document(db, doc_id=doc_id)
    if not db_doc:
        raise DomainException(404, "DOCUMENT_NOT_FOUND", "Документ реестра не найден")
    
    history = db_doc.status_history_purgatory
    return success_response(
        data=jsonable_encoder(history),
        meta={"total": len(history)}
    )

@router.get("/{doc_id}/succession")
async def get_document_succession(doc_id: UUID, db: Session = Depends(get_db)):
    db_doc = crud.get_document(db, doc_id=doc_id)
    if not db_doc:
        raise DomainException(404, "DOCUMENT_NOT_FOUND", "Документ реестра не найден")
    
    chain = []
    current = db_doc
    depth = 0
    
    # Build predecessor chain
    while current.predecessor_doc_id:
        pred = crud.get_document(db, current.predecessor_doc_id)
        if pred:
            chain.insert(0, {
                "id": str(pred.id),
                "title": pred.title,
                "doc_code": pred.doc_code,
                "era": pred.era,
                "relation": "predecessor",
                "depth": depth - 1
            })
            current = pred
            depth -= 1
        else:
            break
    
    # Add self
    chain.append({
        "id": str(db_doc.id),
        "title": db_doc.title,
        "doc_code": db_doc.doc_code,
        "era": db_doc.era,
        "relation": "self",
        "depth": 0
    })
    
    # Build successor chain
    current = db_doc
    depth = 0
    while current.successor_doc_id:
        succ = crud.get_document(db, current.successor_doc_id)
        if succ:
            chain.append({
                "id": str(succ.id),
                "title": succ.title,
                "doc_code": succ.doc_code,
                "era": succ.era,
                "relation": "successor",
                "depth": depth + 1
            })
            current = succ
            depth += 1
        else:
            break
    
    return success_response(
        data={
            "document_id": str(db_doc.id),
            "title": db_doc.title,
            "chain": chain
        }
    )

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
