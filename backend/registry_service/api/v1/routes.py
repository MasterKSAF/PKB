from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from starlette.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.v1.dependencies.database import get_db
from api.v1.crud import document as document_crud, classifier as classifier_crud, terminology as terminology_crud
from api.v1.models import Classifier, ClassifierPending, Document, Terminology
from api.v1.models.registry_service_enums import RegistryServiceEnums
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

    Docs: docs/api/registry_service_api.md §3.1 - Список
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

    Docs: docs/api/registry_service_api.md §3.10 - Экспорт
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

    Docs: docs/api/registry_service_api.md §3.11 - Массовый импорт
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


@routes.post('/registry/documents/check-uniqueness')
def check_documents_uniqueness(
    payload: dict,
    db: Session = Depends(get_db),
):
    """POST /registry/documents/check-uniqueness — duplicate check by metadata.

    Docs: docs/api/registry_service_api.md §3.2.5 - Проверить уникальность документа
    """
    log_event('INFO', '/registry/documents/check-uniqueness', None, log_payload(payload))
    try:
        title = payload.get('title')
        if not title:
            raise HTTPException(
                status_code=422,
                detail={'error': {'code': 'VALIDATION_ERROR', 'message': 'title is required'}},
            )

        result = document_crud.check_document_uniqueness(
            db,
            title=title,
            doc_code=payload.get('doc_code'),
            era=payload.get('era'),
            source_type=payload.get('source_type'),
            file_size_bytes=payload.get('file_size_bytes'),
        )
        return {'data': result}
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', '/registry/documents/check-uniqueness', None, log_payload(payload), str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/documents/{document_id}')
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
):
    """
    GET /registry/documents/{document_id}
    Retrieve a single document by ID.

    Docs: docs/api/registry_service_api.md §3.2 - Один документ (описание)
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


@routes.get('/registry/documents/{document_id}/sections')
def document_sections(
    document_id: str,
    db: Session = Depends(get_db),
):
    """GET /registry/documents/{document_id}/sections — full document for RAG Builder.

    Docs: docs/api/registry_service_api.md §3.2.1 - Секции документа (полный объект для RAG Builder)
    """
    log_event('INFO', f'/registry/documents/{document_id}/sections', None, None)
    try:
        document = document_crud.get_document_by_id(db, document_id)
        if not document:
            raise HTTPException(
                status_code=404,
                detail={'error': {'code': 'DOCUMENT_NOT_FOUND', 'message': 'Document not found'}},
            )
        return document_crud.get_document_sections_bundle(db, document)
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/documents/{document_id}/sections', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.post('/registry/documents/')
def create_document(
    payload: dict,
    db: Session = Depends(get_db),
):
    """
    POST /registry/documents/
    Create a new document.

    Docs: docs/api/registry_service_api.md §3.3 - Создать (основной / из Пайплайна 1)
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

    Docs: docs/api/registry_service_api.md §3.4 - Обновить
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

    Docs: docs/api/registry_service_api.md §3.6 - Обновить статус
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

    Docs: docs/api/registry_service_api.md §3.5 - Частичное обновление
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

    Docs: docs/api/registry_service_api.md §3.9 - Удалить
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

    Docs: docs/api/registry_service_api.md §3.7 - История статусов
    """
    log_event('INFO', f'/registry/documents/{document_id}/history', None, None)
    try:
        document = document_crud.get_document_by_id(db, document_id)
        if not document:
            raise HTTPException(
                status_code=404,
                detail={'error': {'code': 'DOCUMENT_NOT_FOUND', 'message': 'Document not found'}},
            )

        history_rows = document_crud.get_document_history(db, document_id)
        data = [
            {
                'history_id': str(row.id),
                'old_status': row.old_status,
                'new_status': row.new_status,
                'comment': document_crud.parse_history_comment(row.comment),
                'changed_by': row.changed_by,
                'changed_at': row.event_at.isoformat() if row.event_at else None,
            }
            for row in history_rows
        ]
        return {'data': data, 'meta': {'total': len(data)}}
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

    Docs: docs/api/registry_service_api.md §3.8 - Цепочка преемственности
    """
    log_event('INFO', f'/registry/documents/{document_id}/succession', None, None)
    try:
        document = document_crud.get_document_by_id(db, document_id)
        if not document:
            raise HTTPException(
                status_code=404,
                detail={'error': {'code': 'DOCUMENT_NOT_FOUND', 'message': 'Document not found'}},
            )

        return {'data': document_crud.get_document_succession(db, document)}
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
        classifier_system = payload.get('classifier_system')  # Classifier system
        code = payload.get('code')  # Classifier code
        full_name = payload.get('full_name')  # Full name of the classifier
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
    """
    Docs: docs/api/registry_service_api.md §1.4 - Список (плоский)
    """
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
    """
    Docs: docs/api/registry_service_api.md §1.2 - Дерево (иерархическое)
    """
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
    """
    Docs: docs/api/registry_service_api.md §1.8 - Импорт
    """
    try:
        if not file:
            raise HTTPException(
                status_code=400,
                detail={'error': {'code': 'INVALID_FILE', 'message': 'No file uploaded'}},
            )

        return {
            'data': {'message': 'File for Import accepted - not implemented yet'},
        }
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', '/registry/classifiers/import', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/classifiers/pending')
def list_classifier_pending(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    system: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    log_event('INFO', '/registry/classifiers/pending', None, None)
    """
    Docs: docs/api/registry_service_api.md §1.9 - Список карантина
    """
    try:
        items, total = classifier_crud.get_classifier_pending(
            db, page=page, page_size=page_size, system=system, status=status,
        )
        data = []
        for item in items:
            doc_title = None
            if item.found_in_document_id:
                doc = document_crud.get_document_by_id(db, str(item.found_in_document_id))
                doc_title = doc.title if doc else None
            data.append({
                'id': str(item.id),
                'system': item.system,
                'code': item.code,
                'found_in_document_id': str(item.found_in_document_id) if item.found_in_document_id else None,
                'found_in_document_title': doc_title,
                'status': item.status,
                'suggested_parent_code': None,
                'suggested_parent_name': None,
                'admin_comment': item.admin_comment,
                'created_at': item.created_at.isoformat() if item.created_at else None,
            })
        return {'data': data, 'meta': {'total': total, 'page': page, 'page_size': page_size}}
    except Exception as e:
        log_event('ERROR', '/registry/classifiers/pending', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.post('/registry/classifiers/pending/{pending_id}/accept')
def accept_classifier_pending(
    pending_id: str,
    payload: dict,
    db: Session = Depends(get_db),
):
    log_event('INFO', f'/registry/classifiers/pending/{pending_id}/accept', None, log_payload(payload))
    """
    Docs: docs/api/registry_service_api.md §1.10 - Принять код из карантина
    """
    try:
        pending = classifier_crud.get_classifier_pending_by_id(db, pending_id)
        if not pending:
            raise HTTPException(
                status_code=404,
                detail={'error': {'code': 'NOT_FOUND', 'message': 'Pending classifier not found'}},
            )

        full_name = payload.get('full_name')
        if not full_name:
            raise HTTPException(
                status_code=422,
                detail={'error': {'code': 'VALIDATION_ERROR', 'message': 'full_name is required'}},
            )

        classifier, pending = classifier_crud.accept_classifier_pending(
            db,
            pending,
            full_name=full_name,
            parent_code=payload.get('parent_code'),
            admin_comment=payload.get('admin_comment'),
        )
        return {
            'data': {
                'pending_id': str(pending.id),
                'classifier_system': pending.system,
                'code': pending.code,
                'status': pending.status,
                'registry_created': classifier is not None,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/classifiers/pending/{pending_id}/accept', None, log_payload(payload), str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.post('/registry/classifiers/pending/{pending_id}/reject')
def reject_classifier_pending(
    pending_id: str,
    payload: dict,
    db: Session = Depends(get_db),
):
    log_event('INFO', f'/registry/classifiers/pending/{pending_id}/reject', None, log_payload(payload))
    """
    Docs: docs/api/registry_service_api.md §1.11 - Отклонить код из карантина
    """
    try:
        pending = classifier_crud.get_classifier_pending_by_id(db, pending_id)
        if not pending:
            raise HTTPException(
                status_code=404,
                detail={'error': {'code': 'NOT_FOUND', 'message': 'Pending classifier not found'}},
            )

        pending = classifier_crud.reject_classifier_pending(
            db, pending, admin_comment=payload.get('admin_comment'),
        )
        return {'data': {'pending_id': str(pending.id), 'status': pending.status}}
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/classifiers/pending/{pending_id}/reject', None, log_payload(payload), str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.post('/registry/classifiers/validate')
def validate_classifiers(
    payload: dict,
    db: Session = Depends(get_db),
):
    log_event('INFO', '/registry/classifiers/validate', None, log_payload(payload))
    """
    Docs: docs/api/registry_service_api.md §1.12 - Валидация классификации
    """
    try:
        classification = payload.get('classification')
        if not isinstance(classification, dict):
            raise HTTPException(
                status_code=422,
                detail={'error': {'code': 'VALIDATION_ERROR', 'message': 'classification object is required'}},
            )
        return {'data': classifier_crud.validate_classification(db, classification)}
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', '/registry/classifiers/validate', None, log_payload(payload), str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/classifiers/{code}')
def get_classifier(
    code: str,
    classifier_system: str = Query(...),
    db: Session = Depends(get_db),
):
    log_event('INFO', f'/registry/classifiers/{code}', None, None)
    """
    Docs: docs/api/registry_service_api.md §1.3 - Один узел
    """
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
    """
    Docs: docs/api/registry_service_api.md §1.5 - Обновить
    """
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
    """
    Docs: docs/api/registry_service_api.md §1.6 - Частичное обновление
    """
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
    """
    Docs: docs/api/registry_service_api.md §1.7 - Удалить
    """
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
    """
    Docs: docs/api/registry_service_api.md §2.3 - Создать
    """
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
    """
    Docs: docs/api/registry_service_api.md §2.1 - Список
    """
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
    """
    Docs: docs/api/registry_service_api.md §2.6 - Поиск нормализованной формы
    """
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
    """
    Docs: docs/api/registry_service_api.md §2.7 - Импорт
    """
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
    """
    Docs: docs/api/registry_service_api.md §2.2 - Один термин
    """
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
    """
    Docs: docs/api/registry_service_api.md §2.4 - Обновить
    """
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
    """
    Docs: docs/api/registry_service_api.md §2.4 - Обновить
    """
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
    """
    Docs: docs/api/registry_service_api.md §2.5 - Удалить
    """
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
def get_enums(db: Session = Depends(get_db)):
    """
    Docs: docs/api/registry_service_api.md — GET /registry/enums (Enums / reference values)
    """
    log_event('INFO', '/registry/enums', None, None)
    try:
        data = RegistryServiceEnums.get_all_grouped(db)
    except Exception as e:
        log_event('ERROR', '/registry/enums', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})

    return {'data': data}


@routes.get('/registry/stats')
def get_stats(db: Session = Depends(get_db)):
    """
    Docs: docs/api/registry_service_api.md — GET /registry/stats (Statistics)
    """
    log_event('INFO', '/registry/stats', None, None)
    try:
        classifiers_by_system = dict(
            db.query(Classifier.classifier_system, func.count())
            .group_by(Classifier.classifier_system)
            .all()
        )
    except Exception:
        classifiers_by_system = {}

    try:
        classifiers_pending = db.query(ClassifierPending).filter(ClassifierPending.status == 'new').count()
    except Exception:
        classifiers_pending = 0

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

    try:
        source_types = db.query(Document.source_type, func.count()).group_by(Document.source_type).all()
        documents_by_source_type = {value or 'unknown': count for value, count in source_types}
    except Exception:
        documents_by_source_type = {}

    try:
        eras = db.query(Document.era, func.count()).group_by(Document.era).all()
        documents_by_era = {value or 'unknown': count for value, count in eras}
    except Exception:
        documents_by_era = {}

    return {
        'data': {
            'classifiers_total': classifiers_by_system,
            'classifiers_pending': classifiers_pending,
            'terminology_total': terminologies_total,
            'documents_total': documents_total,
            'documents_by_status': documents_by_status,
            'documents_by_source_type': documents_by_source_type,
            'documents_by_era': documents_by_era,
        }
    }


@routes.get('/health')
def health_check():
    """Health check endpoint.

    Docs: docs/api/registry_service_api.md — GET /health (Health check)
    """
    log_event('INFO', '/health', None, None)
    return {'status': 'ok'}
