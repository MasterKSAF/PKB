from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.v1.dependencies.database import get_db
from api.v1.crud import document as document_crud
from api.v1.schemas import DocumentSchema
from api.v1.schemas.response import SingleResponse, ListResponse, PaginationMeta, ErrorResponse
from services.logger import log_event

routes = APIRouter()


# ============================================================================
# Documents - Group 3
# ============================================================================

@routes.get('/registry/documents')
def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    doc_code: str = Query(None),
    processing_status: str = Query(None),
    db: Session = Depends(get_db),
):
    """
    GET /registry/documents
    List all documents with pagination and optional filters.
    """
    try:
        documents, total = document_crud.get_documents(
            db,
            page=page,
            page_size=page_size,
            doc_code=doc_code,
            processing_status=processing_status,
        )
        
        data = [DocumentSchema.from_orm(doc) for doc in documents]
        
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


@routes.get('/registry/documents/{document_id}')
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
):
    """
    GET /registry/documents/{document_id}
    Retrieve a single document by ID.
    """
    try:
        document = document_crud.get_document_by_id(db, document_id)
        
        if not document:
            log_event('WARNING', f'/registry/documents/{document_id}', None, None, 'Document not found')
            raise HTTPException(
                status_code=404,
                detail={'error': {'code': 'DOCUMENT_NOT_FOUND', 'message': 'Document not found'}},
            )
        
        return {
            'data': DocumentSchema.from_orm(document),
        }
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/documents/{document_id}', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.post('/registry/documents')
def create_document(
    payload: dict,
    db: Session = Depends(get_db),
):
    """
    POST /registry/documents
    Create a new document.
    """
    try:
        doc_code = payload.get('doc_code')
        title = payload.get('title')
        
        if not doc_code or not title:
            log_event('WARNING', '/registry/documents', None, payload, 'Missing required fields')
            raise HTTPException(
                status_code=400,
                detail={'error': {'code': 'VALIDATION_ERROR', 'message': 'Missing doc_code or title'}},
            )
        
        document = document_crud.create_document(db, doc_code=doc_code, title=title, **payload)
        
        log_event('INFO', '/registry/documents', None, {'doc_code': doc_code}, 'Document created')
        
        return {
            'data': DocumentSchema.from_orm(document),
        }
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
            'data': DocumentSchema.from_orm(document),
        }
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/documents/{document_id}', None, payload, str(e))
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
            'data': DocumentSchema.from_orm(document),
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


@routes.get('/health')
def health_check():
    """Health check endpoint."""
    return {'status': 'ok'}
