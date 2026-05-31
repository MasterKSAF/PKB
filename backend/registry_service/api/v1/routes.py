from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from starlette.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.v1.dependencies.database import get_db
from api.v1.crud import document as document_crud, classifier as classifier_crud, terminology as terminology_crud
from api.v1.models import Classifier, Document, Terminology
from api.v1.schemas import DocumentSchema, ClassifierSchema, TerminologySchema
from api.v1.schemas.response import SingleResponse, ListResponse, PaginationMeta, ErrorResponse
from services.logger import log_event, log_payload

routes = APIRouter()


# ============================================================================
# Documents - Group 3
# ============================================================================

@routes.get('/registry/documents/')
def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    doc_code: Optional[str] = Query(None),
    title: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    mks_oks_code: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    GET /registry/documents/
    List all documents with pagination and optional filters.
    """
    log_event('INFO', '/registry/documents', None, None)
    try:
        documents, total = document_crud.get_documents(
            db,
            page=page,
            page_size=page_size,
            doc_code=doc_code,
            title=title,
            status=status,
            mks_oks_code=mks_oks_code,
        )
        
        data = [DocumentSchema.model_validate(doc).model_dump(mode='json', by_alias=True, exclude_none=True) for doc in documents]
        
        return {
            'data': data,
            'meta': {
                'total': total,
                'page': page,
                'page_size': page_size,
            }
        }
    except Exception as e:
        log_event('ERROR', '/registry/documents', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/documents/export')
def export_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(1000, ge=1, le=10000),
    db: Session = Depends(get_db),
):
    """
    GET /registry/documents/export
    Export documents as CSV.
    """
    log_event('INFO', '/registry/documents/export', None, None)
    try:
        documents, _ = document_crud.get_documents(db, page=page, page_size=page_size)
        rows = ['id,doc_code,title,status,mks_oks_code']
        for document in documents:
            rows.append(
                ','.join([
                    str(document.id),
                    document.doc_code or '',
                    (document.title or '').replace(',', ' '),
                    document.status or '',
                    document.mks_oks_code or '',
                ])
            )
        csv_data = '\n'.join(rows)
        return Response(content=csv_data, media_type='text/csv')
    except Exception as e:
        log_event('ERROR', '/registry/documents/export', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.post('/registry/documents/import')
def import_documents(
    mapping: str = Query(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    POST /registry/documents/import
    Import documents from a file.
    """
    log_event('INFO', '/registry/documents/import', None, None)
    try:
        if not file:
            raise HTTPException(
                status_code=400,
                detail={'error': {'code': 'INVALID_FILE', 'message': 'No file uploaded'}},
            )

        return {
            'data': {'message': 'Import accepted'},
        }
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', '/registry/documents/import', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/documents/{document_id}')
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
):
    """
    GET /registry/documents/{document_id}
    Retrieve a single document by ID.
    """
    log_event('INFO', f'/registry/documents/{document_id}', None, None)
    try:
        document = document_crud.get_document_by_id(db, document_id)
        
        if not document:
            log_event('WARNING', f'/registry/documents/{document_id}', None, None, 'Document not found')
            raise HTTPException(
                status_code=404,
                detail={'error': {'code': 'DOCUMENT_NOT_FOUND', 'message': 'Document not found'}},
            )
        
        return {
            'data': DocumentSchema.model_validate(document).model_dump(mode='json', by_alias=True, exclude_none=True),
        }
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/documents/{document_id}', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.post('/registry/documents/')
def create_document(
    payload: dict,
    db: Session = Depends(get_db),
):
    """
    POST /registry/documents/
    Create a new document.
    """
    log_event('INFO', '/registry/documents', None, log_payload(payload))
    try:
        title = payload.get('title')
        doc_code = payload.get('doc_code') or (title or '').strip().upper().replace(' ', '-').replace('/', '-')
        
        if not title:
            log_event('WARNING', '/registry/documents', None, payload, 'Missing required fields')
            raise HTTPException(
                status_code=422,
                detail={'error': {'code': 'VALIDATION_ERROR', 'message': 'Missing title'}},
            )
        if not doc_code:
            log_event('WARNING', '/registry/documents', None, payload, 'Missing document code')
            raise HTTPException(
                status_code=422,
                detail={'error': {'code': 'VALIDATION_ERROR', 'message': 'Missing doc_code'}},
            )

        clean_payload = {k: v for k, v in payload.items() if k in {
            'normalized_title', 'source_type', 'group', 'mks_oks_code', 'okstu_code',
            'udc', 'era', 'validity_status', 'status', 'jurisdiction', 'issuing_body',
            'adoption_date', 'effective_from', 'replaces', 'status_note', 'file_hash_sha256',
            'title_hash_sha256', 'file_size_bytes', 'processing_status', 'chunk_count',
            'successor_doc_id', 'predecessor_doc_id', 'created_by', 'updated_by',
        }}

        document = document_crud.create_document(db, doc_code=doc_code, title=title, **clean_payload)
        
        log_event('INFO', '/registry/documents', None, {'doc_code': doc_code}, 'Document created')
        
        return JSONResponse(
            status_code=201,
            content={'data': DocumentSchema.model_validate(document).model_dump(mode='json', by_alias=True, exclude_none=True)},
        )
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', '/registry/documents', None, payload, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.put('/registry/documents/{document_id}')
def update_document(
    document_id: str,
    payload: dict,
    db: Session = Depends(get_db),
):
    """
    PUT /registry/documents/{document_id}
    Update an entire document.
    """
    log_event('INFO', f'/registry/documents/{document_id}', None, log_payload(payload))
    try:
        document = document_crud.update_document(db, document_id, **payload)
        
        if not document:
            log_event('WARNING', f'/registry/documents/{document_id}', None, None, 'Document not found')
            raise HTTPException(
                status_code=404,
                detail={'error': {'code': 'DOCUMENT_NOT_FOUND', 'message': 'Document not found'}},
            )
        
        log_event('INFO', f'/registry/documents/{document_id}', None, payload, 'Document updated')
        
        return {
            'data': DocumentSchema.model_validate(document).model_dump(mode='json', by_alias=True, exclude_none=True),
        }
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/documents/{document_id}', None, payload, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.patch('/registry/documents/{document_id}/status')
def patch_document_status(
    document_id: str,
    payload: dict,
    db: Session = Depends(get_db),
):
    """
    PATCH /registry/documents/{document_id}/status
    Update the status of a document.
    """
    log_event('INFO', f'/registry/documents/{document_id}/status', None, log_payload(payload))
    try:
        status = payload.get('status')
        if status is None:
            raise HTTPException(
                status_code=422,
                detail={'error': {'code': 'VALIDATION_ERROR', 'message': 'Missing status'}},
            )

        document = document_crud.update_document(db, document_id, status=status)
        if not document:
            raise HTTPException(
                status_code=404,
                detail={'error': {'code': 'DOCUMENT_NOT_FOUND', 'message': 'Document not found'}},
            )

        log_event('INFO', f'/registry/documents/{document_id}/status', None, payload, 'Document status updated')
        return {
            'data': DocumentSchema.model_validate(document).model_dump(mode='json', by_alias=True, exclude_none=True),
        }
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/documents/{document_id}/status', None, payload, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.patch('/registry/documents/{document_id}')
def patch_document(
    document_id: str,
    payload: dict,
    db: Session = Depends(get_db),
):
    """
    PATCH /registry/documents/{document_id}
    Partially update a document.
    """
    log_event('INFO', f'/registry/documents/{document_id}', None, log_payload(payload))
    try:
        document = document_crud.update_document(db, document_id, **payload)
        
        if not document:
            log_event('WARNING', f'/registry/documents/{document_id}', None, None, 'Document not found')
            raise HTTPException(
                status_code=404,
                detail={'error': {'code': 'DOCUMENT_NOT_FOUND', 'message': 'Document not found'}},
            )
        
        log_event('INFO', f'/registry/documents/{document_id}', None, payload, 'Document patched')
        
        return {
            'data': DocumentSchema.model_validate(document).model_dump(mode='json', by_alias=True, exclude_none=True),
        }
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/documents/{document_id}', None, payload, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.delete('/registry/documents/{document_id}')
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
):
    """
    DELETE /registry/documents/{document_id}
    Delete a document.
    """
    log_event('INFO', f'/registry/documents/{document_id}', None, None)
    try:
        if not document_crud.delete_document(db, document_id):
            log_event('WARNING', f'/registry/documents/{document_id}', None, None, 'Document not found')
            raise HTTPException(
                status_code=404,
                detail={'error': {'code': 'DOCUMENT_NOT_FOUND', 'message': 'Document not found'}},
            )
        
        log_event('INFO', f'/registry/documents/{document_id}', None, None, 'Document deleted')
        
        return {
            'data': {'message': 'Document deleted'},
        }
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/documents/{document_id}', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/documents/{document_id}/history')
def document_history(
    document_id: str,
    db: Session = Depends(get_db),
):
    """
    GET /registry/documents/{document_id}/history
    Return document history.
    """
    log_event('INFO', f'/registry/documents/{document_id}/history', None, None)
    try:
        document = document_crud.get_document_by_id(db, document_id)
        if not document:
            raise HTTPException(
                status_code=404,
                detail={'error': {'code': 'DOCUMENT_NOT_FOUND', 'message': 'Document not found'}},
            )

        return {'data': []}
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/documents/{document_id}/history', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/documents/{document_id}/succession')
def document_succession(
    document_id: str,
    db: Session = Depends(get_db),
):
    """
    GET /registry/documents/{document_id}/succession
    Return document succession.
    """
    log_event('INFO', f'/registry/documents/{document_id}/succession', None, None)
    try:
        document = document_crud.get_document_by_id(db, document_id)
        if not document:
            raise HTTPException(
                status_code=404,
                detail={'error': {'code': 'DOCUMENT_NOT_FOUND', 'message': 'Document not found'}},
            )

        return {'data': []}
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/documents/{document_id}/succession', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.post('/registry/classifiers/')
def create_classifier(
    payload: dict,
    db: Session = Depends(get_db),
):
    log_event('INFO', '/registry/classifiers', None, log_payload(payload))
    try:
        classifier_system = payload.get('classifier_system')
        code = payload.get('code')
        full_name = payload.get('full_name')
        parent_code = payload.get('parent_code')
        status = payload.get('status')
        description = payload.get('description')

        if not classifier_system or not code or not full_name:
            raise HTTPException(
                status_code=422,
                detail={'error': {'code': 'VALIDATION_ERROR', 'message': 'classifier_system, code, and full_name are required'}},
            )

        existing = classifier_crud.get_classifier(db, classifier_system, code)
        if existing:
            raise HTTPException(
                status_code=409,
                detail={'error': {'code': 'DUPLICATE_CLASSIFIER', 'message': 'Classifier already exists'}},
            )

        classifier = classifier_crud.create_classifier(
            db,
            classifier_system=classifier_system,
            code=code,
            full_name=full_name,
            parent_code=parent_code,
            status=status,
            description=description,
        )

        return JSONResponse(
            status_code=201,
            content={'data': ClassifierSchema.model_validate(classifier).model_dump(mode='json', by_alias=True, exclude_none=True)},
        )
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', '/registry/classifiers', None, payload, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/classifiers/')
def list_classifiers(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    classifier_system: Optional[str] = None,
    status: Optional[str] = None,
    full_name: Optional[str] = None,
    parent_code: Optional[str] = None,
    db: Session = Depends(get_db),
):
    log_event('INFO', '/registry/classifiers', None, None)
    try:
        classifiers, total = classifier_crud.get_classifiers(
            db,
            page=page,
            page_size=page_size,
            classifier_system=classifier_system,
            status=status,
            full_name=full_name,
            parent_code=parent_code,
        )

        data = [ClassifierSchema.model_validate(item).model_dump(mode='json', by_alias=True, exclude_none=True) for item in classifiers]

        return {
            'data': data,
            'meta': {
                'total': total,
                'page': page,
                'page_size': page_size,
            },
        }
    except Exception as e:
        log_event('ERROR', '/registry/classifiers', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/classifiers/tree')
def classifier_tree(
    classifier_system: str = Query(...),
    root_code: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    log_event('INFO', '/registry/classifiers/tree', None, None)
    try:
        classifiers = classifier_crud.get_classifier_tree(db, classifier_system, root_code=root_code, search=search)
        data = [ClassifierSchema.model_validate(item).model_dump(mode='json', by_alias=True, exclude_none=True) for item in classifiers]
        return {
            'data': data,
        }
    except Exception as e:
        log_event('ERROR', '/registry/classifiers/tree', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.post('/registry/classifiers/import')
def import_classifiers(
    classifier_system: str = Query(...),
    mapping: str = Query(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    log_event('INFO', '/registry/classifiers/import', None, None)
    try:
        if not file:
            raise HTTPException(
                status_code=400,
                detail={'error': {'code': 'INVALID_FILE', 'message': 'No file uploaded'}},
            )

        return {
            'data': {'message': 'Import accepted'},
        }
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', '/registry/classifiers/import', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/classifiers/{code}')
def get_classifier(
    code: str,
    classifier_system: str = Query(...),
    db: Session = Depends(get_db),
):
    log_event('INFO', f'/registry/classifiers/{code}', None, None)
    try:
        classifier = classifier_crud.get_classifier(db, classifier_system, code)
        if not classifier:
            raise HTTPException(
                status_code=404,
                detail={'error': {'code': 'CLASSIFIER_NOT_FOUND', 'message': 'Classifier not found'}},
            )

        return {
            'data': ClassifierSchema.model_validate(classifier).model_dump(mode='json', by_alias=True, exclude_none=True),
        }
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/classifiers/{code}', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.put('/registry/classifiers/{code}')
def update_classifier(
    code: str,
    payload: dict,
    classifier_system: str = Query(...),
    db: Session = Depends(get_db),
):
    log_event('INFO', f'/registry/classifiers/{code}', None, log_payload(payload))
    try:
        classifier = classifier_crud.update_classifier(db, classifier_system, code, **payload)
        if not classifier:
            raise HTTPException(
                status_code=404,
                detail={'error': {'code': 'CLASSIFIER_NOT_FOUND', 'message': 'Classifier not found'}},
            )

        return {
            'data': ClassifierSchema.model_validate(classifier).model_dump(mode='json', by_alias=True, exclude_none=True),
        }
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/classifiers/{code}', None, payload, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.patch('/registry/classifiers/{code}')
def patch_classifier(
    code: str,
    payload: dict,
    classifier_system: str = Query(...),
    db: Session = Depends(get_db),
):
    log_event('INFO', f'/registry/classifiers/{code}', None, log_payload(payload))
    try:
        classifier = classifier_crud.update_classifier(db, classifier_system, code, **payload)
        if not classifier:
            raise HTTPException(
                status_code=404,
                detail={'error': {'code': 'CLASSIFIER_NOT_FOUND', 'message': 'Classifier not found'}},
            )

        return {
            'data': ClassifierSchema.model_validate(classifier).model_dump(mode='json', by_alias=True, exclude_none=True),
        }
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/classifiers/{code}', None, payload, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.delete('/registry/classifiers/{code}')
def delete_classifier(
    code: str,
    classifier_system: str = Query(...),
    force: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    log_event('INFO', f'/registry/classifiers/{code}', None, None)
    try:
        force_flag = str(force).lower() == 'true'
        try:
            deleted = classifier_crud.delete_classifier(db, classifier_system, code, force=force_flag)
        except ValueError as e:
            raise HTTPException(
                status_code=409,
                detail={'error': {'code': 'DELETE_CONFLICT', 'message': str(e)}},
            )

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail={'error': {'code': 'CLASSIFIER_NOT_FOUND', 'message': 'Classifier not found'}},
            )

        return {
            'data': {'message': 'Classifier deleted'},
        }
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/classifiers/{code}', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.post('/registry/terminology/')
def create_terminology(
    payload: dict,
    db: Session = Depends(get_db),
):
    log_event('INFO', '/registry/terminology', None, log_payload(payload))
    try:
        raw_term = payload.get('raw_term')
        standard_term = payload.get('standard_term')
        normalized_value = payload.get('normalized_value')
        term_type = payload.get('term_type')
        is_blocked = payload.get('is_blocked', False)
        definition = payload.get('definition')

        if not raw_term or not standard_term or not normalized_value or not term_type:
            raise HTTPException(
                status_code=422,
                detail={'error': {'code': 'VALIDATION_ERROR', 'message': 'raw_term, standard_term, normalized_value, and term_type are required'}},
            )

        existing = terminology_crud.get_terminology_by_raw_term(db, raw_term)
        if existing:
            raise HTTPException(
                status_code=409,
                detail={'error': {'code': 'DUPLICATE_TERMINOLOGY', 'message': 'Terminology already exists'}},
            )

        term = terminology_crud.create_terminology(
            db,
            raw_term=raw_term,
            standard_term=standard_term,
            normalized_value=normalized_value,
            term_type=term_type,
            is_blocked=is_blocked,
            definition=definition,
        )

        return JSONResponse(
            status_code=201,
            content={'data': TerminologySchema.model_validate(term).model_dump(mode='json', by_alias=True, exclude_none=True)},
        )
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', '/registry/terminology', None, payload, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/terminology/')
def list_terminology(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    raw_term: Optional[str] = Query(None),
    normalized_term: Optional[str] = Query(None),
    term_type: Optional[str] = Query(None),
    is_blocked: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    log_event('INFO', '/registry/terminology', None, None)
    try:
        blocked = None
        if is_blocked is not None:
            blocked = str(is_blocked).lower() == 'true'

        terms, total = terminology_crud.get_terminology(
            db,
            page=page,
            page_size=page_size,
            raw_term=raw_term,
            normalized_term=normalized_term,
            term_type=term_type,
            is_blocked=blocked,
        )

        data = [TerminologySchema.model_validate(item).model_dump(mode='json', by_alias=True, exclude_none=True) for item in terms]
        return {
            'data': data,
            'meta': {
                'total': total,
                'page': page,
                'page_size': page_size,
            },
        }
    except Exception as e:
        log_event('ERROR', '/registry/terminology', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/terminology/normalize')
def normalize_terminology(
    term: str = Query(...),
    db: Session = Depends(get_db),
):
    log_event('INFO', '/registry/terminology/normalize', None, None)
    try:
        result = terminology_crud.get_terminology_by_raw_term(db, term)
        if result:
            return {
                'data': TerminologySchema.model_validate(result).model_dump(mode='json', by_alias=True, exclude_none=True),
            }

        return {
            'data': {
                'raw_term': term,
                'standard_term': term,
                'normalized_value': term.lower(),
                'term_type': 'unknown',
            }
        }
    except Exception as e:
        log_event('ERROR', '/registry/terminology/normalize', None, {'term': term}, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.post('/registry/terminology/import')
def import_terminology(
    mapping: str = Query(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    log_event('INFO', '/registry/terminology/import', None, None)
    try:
        if not file:
            raise HTTPException(
                status_code=400,
                detail={'error': {'code': 'INVALID_FILE', 'message': 'No file uploaded'}},
            )

        return {
            'data': {'message': 'Import accepted'},
        }
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', '/registry/terminology/import', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/terminology/{term_id}')
def get_terminology(
    term_id: str,
    db: Session = Depends(get_db),
):
    log_event('INFO', f'/registry/terminology/{term_id}', None, None)
    try:
        term = terminology_crud.get_terminology_by_id(db, term_id)
        if not term:
            raise HTTPException(
                status_code=404,
                detail={'error': {'code': 'TERMINOLOGY_NOT_FOUND', 'message': 'Terminology not found'}},
            )

        return {
            'data': TerminologySchema.model_validate(term).model_dump(mode='json', by_alias=True, exclude_none=True),
        }
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/terminology/{term_id}', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.put('/registry/terminology/{term_id}')
def update_terminology(
    term_id: str,
    payload: dict,
    db: Session = Depends(get_db),
):
    log_event('INFO', f'/registry/terminology/{term_id}', None, log_payload(payload))
    try:
        term = terminology_crud.update_terminology(db, term_id, **payload)
        if not term:
            raise HTTPException(
                status_code=404,
                detail={'error': {'code': 'TERMINOLOGY_NOT_FOUND', 'message': 'Terminology not found'}},
            )

        return {
            'data': TerminologySchema.model_validate(term).model_dump(mode='json', by_alias=True, exclude_none=True),
        }
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/terminology/{term_id}', None, payload, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.patch('/registry/terminology/{term_id}')
def patch_terminology(
    term_id: str,
    payload: dict,
    db: Session = Depends(get_db),
):
    log_event('INFO', f'/registry/terminology/{term_id}', None, log_payload(payload))
    try:
        term = terminology_crud.update_terminology(db, term_id, **payload)
        if not term:
            raise HTTPException(
                status_code=404,
                detail={'error': {'code': 'TERMINOLOGY_NOT_FOUND', 'message': 'Terminology not found'}},
            )

        return {
            'data': TerminologySchema.model_validate(term).model_dump(mode='json', by_alias=True, exclude_none=True),
        }
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/terminology/{term_id}', None, payload, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.delete('/registry/terminology/{term_id}')
def delete_terminology(
    term_id: str,
    db: Session = Depends(get_db),
):
    log_event('INFO', f'/registry/terminology/{term_id}', None, None)
    try:
        if not terminology_crud.delete_terminology(db, term_id):
            raise HTTPException(
                status_code=404,
                detail={'error': {'code': 'TERMINOLOGY_NOT_FOUND', 'message': 'Terminology not found'}},
            )

        return {
            'data': {'message': 'Terminology deleted'},
        }
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/terminology/{term_id}', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/enums')
def get_enums():
    log_event('INFO', '/registry/enums', None, None)
    return {
        'data': {
            'doc_type': ['OKS', 'FAC', 'STD'],
            'jurisdiction': ['RF', 'EU', 'US'],
            'language': ['ru', 'en', 'fr'],
            'document_status': ['draft', 'approved', 'processing', 'archived'],
            'context': ['policy', 'law', 'norm'],
        }
    }


@routes.get('/registry/stats')
def get_stats(db: Session = Depends(get_db)):
    log_event('INFO', '/registry/stats', None, None)
    try:
        classifiers_total = db.query(Classifier).count()
    except Exception:
        classifiers_total = 0

    try:
        documents_total = db.query(Document).count()
    except Exception:
        documents_total = 0

    try:
        terminologies_total = db.query(Terminology).count()
    except Exception:
        terminologies_total = 0

    try:
        statuses = db.query(Document.status, func.count()).group_by(Document.status).all()
        documents_by_status = {status or 'unknown': count for status, count in statuses}
    except Exception:
        documents_by_status = {}

    return {
        'data': {
            'classifiers_total': classifiers_total,
            'terminology_total': terminologies_total,
            'documents_total': documents_total,
            'documents_by_status': documents_by_status,
        }
    }


@routes.get('/health')
def health_check():
    """Health check endpoint."""
    log_event('INFO', '/health', None, None)
    return {'status': 'ok'}
