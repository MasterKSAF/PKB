from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..dependencies.database import get_db
from ..models.classifier import ClassifierRegistryPurgatory
from ..models.terminology import TerminologyRegistryPurgatory
from ..models.document import DocumentsPurgatory

router = APIRouter()

@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    classifiers_total = db.query(ClassifierRegistryPurgatory).count()
    terminology_total = db.query(TerminologyRegistryPurgatory).count()
    documents_total = db.query(DocumentsPurgatory).count()
    
    # Group by status
    status_counts = db.query(DocumentsPurgatory.status, func.count(DocumentsPurgatory.id)).group_by(DocumentsPurgatory.status).all()
    documents_by_status = {status.value if status else "unknown": count for status, count in status_counts}
    
    return success_response(
        data={
            "classifiers_total": classifiers_total,
            "terminology_total": terminology_total,
            "documents_total": documents_total,
            "documents_by_status": documents_by_status
        }
    )

@router.get("/enums")
async def get_enums():
    return success_response(
        data={
            "doc_type": ["OKS", "GOST", "GOST_R", "OST", "TU", "ISO", "FSN"],
            "jurisdiction": ["RF", "EAES", "INTL", "US", "EU", "DE"],
            "language": ["ru", "en", "de"],
            "document_status": ["draft", "active", "obsolete", "need_to_buy", "searching"],
            "context": ["Общий", "Судостроение", "Электроника", "Металлургия", "Строительство"],
            "file_document_type": ["normative", "archival_scan", "drawing", "specification"],
            "file_document_status": ["queued", "processing", "processed", "error"],
            "check_result_status": ["OK", "WARNING", "ERROR"],
            "match_status": ["match", "possible_discrepancy", "not_found_in_project", "not_found_in_norm", "insufficient_data"],
            "ocr_engine": ["paddleocr", "tesseract"],
            "chat_status": ["answered", "needs_clarification", "source_conflict"]
        }
    )
