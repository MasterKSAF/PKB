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
    
    # Group by classifier system
    classifier_system_counts = db.query(
        ClassifierRegistryPurgatory.classifier_system, 
        func.count(ClassifierRegistryPurgatory.code)
    ).group_by(ClassifierRegistryPurgatory.classifier_system).all()
    classifiers_by_system = {system: count for system, count in classifier_system_counts}
    
    # Group by document status
    status_counts = db.query(DocumentsPurgatory.status, func.count(DocumentsPurgatory.id)).group_by(DocumentsPurgatory.status).all()
    documents_by_status = {status.value if status else "unknown": count for status, count in status_counts}
    
    # Group by source_type
    source_type_counts = db.query(DocumentsPurgatory.source_type, func.count(DocumentsPurgatory.id)).group_by(DocumentsPurgatory.source_type).all()
    documents_by_source_type = {source_type or "unknown": count for source_type, count in source_type_counts}
    
    # Group by era
    era_counts = db.query(DocumentsPurgatory.era, func.count(DocumentsPurgatory.id)).group_by(DocumentsPurgatory.era).all()
    documents_by_era = {era or "unknown": count for era, count in era_counts}
    
    # Group by term type
    term_type_counts = db.query(TerminologyRegistryPurgatory.term_type, func.count(TerminologyRegistryPurgatory.id)).group_by(TerminologyRegistryPurgatory.term_type).all()
    terminology_by_type = {term_type or "unknown": count for term_type, count in term_type_counts}
    
    return success_response(
        data={
            "classifiers_total": classifiers_total,
            "classifiers_by_system": classifiers_by_system,
            "terminology_total": terminology_total,
            "terminology_by_type": terminology_by_type,
            "documents_total": documents_total,
            "documents_by_status": documents_by_status,
            "documents_by_source_type": documents_by_source_type,
            "documents_by_era": documents_by_era
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
