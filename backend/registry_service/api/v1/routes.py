from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, Header, Body
from starlette.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.v1.dependencies.database import get_db
from api.v1.crud import document as document_crud, classifier as classifier_crud, terminology as terminology_crud
from api.v1.models import Classifier, ClassifierPending, Document, Terminology
from api.v1.models.registry_service_enums import RegistryServiceEnums
from api.v1.schemas import DocumentSchema, ClassifierSchema, TerminologySchema, ClassifierValidateRequest
from api.v1.schemas.response import SingleResponse, ListResponse, PaginationMeta, ErrorResponse
from services.logger import log_event, log_payload

routes = APIRouter()


@routes.get('/registry/search')
def search_registry(
    q: str = Query(..., min_length=3),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """
    GET /registry/search
    BM25 Registry search
    """
    log_event('INFO', '/registry/search', None, {'q': q})
    try:
        from sqlalchemy import text
        skip = (page - 1) * page_size
        
        query = text("""
            SELECT id::text, 'document' as type, title as match_text, 
                   ts_rank(to_tsvector('russian', title), plainto_tsquery('russian', :q)) as rank
            FROM registry.documents
            WHERE to_tsvector('russian', title) @@ plainto_tsquery('russian', :q)
            UNION ALL
            SELECT code as id, 'classifier' as type, full_name as match_text, 
                   ts_rank(to_tsvector('russian', full_name), plainto_tsquery('russian', :q)) as rank
            FROM registry.classifiers
            WHERE to_tsvector('russian', full_name) @@ plainto_tsquery('russian', :q)
            ORDER BY rank DESC
            OFFSET :skip LIMIT :limit
        """)
        
        result = db.execute(query, {'q': q, 'skip': skip, 'limit': page_size})
        data = [
            {'id': row[0], 'type': row[1], 'match_text': row[2], 'rank': row[3]}
            for row in result
        ]
        
        return {'data': data, 'meta': {'page': page, 'page_size': page_size}}
    except Exception as e:
        log_event('ERROR', '/registry/search', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})

# ============================================================================
# Documents - Group 3
# ============================================================================

@routes.get('/registry/documents')
def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    doc_code: Optional[str] = Query(None),
    title: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    mks_oks_code: Optional[str] = Query(None),
    source_type: Optional[str] = Query(None),
    okstu_code: Optional[str] = Query(None),
    era: Optional[str] = Query(None),
    validity_status: Optional[str] = Query(None),
    jurisdiction: Optional[str] = Query(None),
    issuing_body: Optional[str] = Query(None),
    title_hash_sha256: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    valid_at: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    GET /registry/documents/
    List all documents with pagination and optional filters.

    Docs: docs/api/registry_service_api.md §3.1 - Список
    """
    log_event('INFO', '/registry/documents/', None, None)
    try:
        dt_from = None
        if date_from:
            try:
                from datetime import datetime
                dt_from = datetime.fromisoformat(date_from)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail={'error': {'code': 'INVALID_DATE_RANGE', 'message': 'Некорректный формат даты date_from'}}
                )
        dt_to = None
        if date_to:
            try:
                from datetime import datetime
                dt_to = datetime.fromisoformat(date_to)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail={'error': {'code': 'INVALID_DATE_RANGE', 'message': 'Некорректный формат даты date_to'}}
                )

        if dt_from and dt_to:
            if dt_from > dt_to:
                raise HTTPException(
                    status_code=400,
                    detail={'error': {'code': 'INVALID_DATE_RANGE', 'message': 'date_from позже date_to'}}
                )
            
            from settings import MAX_DATE_RANGE_YEARS
            days_diff = (dt_to - dt_from).days
            if days_diff > MAX_DATE_RANGE_YEARS * 365.25:
                raise HTTPException(
                    status_code=400,
                    detail={'error': {'code': 'INVALID_DATE_RANGE', 'message': f'Превышен максимальный диапазон дат ({MAX_DATE_RANGE_YEARS} лет)'}}
                )


        dt_valid_at = None
        if valid_at:
            try:
                from datetime import datetime
                dt_valid_at = datetime.fromisoformat(valid_at)
            except ValueError:
                pass

        documents, total = document_crud.get_documents(
            db,
            page=page,
            page_size=page_size,
            doc_code=doc_code,
            title=title,
            status=status,
            mks_oks_code=mks_oks_code,
            source_type=source_type,
            okstu_code=okstu_code,
            era=era,
            validity_status=validity_status,
            jurisdiction=jurisdiction,
            issuing_body=issuing_body,
            title_hash_sha256=title_hash_sha256,
            date_from=dt_from,
            date_to=dt_to,
            valid_at=dt_valid_at,
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
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', '/registry/documents/', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/documents/export')
def export_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(1000, ge=1, le=10000),
    db: Session = Depends(get_db),
):
    """
    GET /registry/documents/export/
    Export documents as CSV.

    Docs: docs/api/registry_service_api.md §3.10 - Экспорт
    """
    log_event('INFO', '/registry/documents/export/', None, None)
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
        log_event('ERROR', '/registry/documents/export/', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.post('/registry/documents/import')
async def import_documents(
    mapping: str = Query(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    POST /registry/documents/import/
    Import documents from a file.

    Docs: docs/api/registry_service_api.md §3.11 - Массовый импорт
    """
    log_event('INFO', '/registry/documents/import/', None, None)
    try:
        if not file:
            raise HTTPException(
                status_code=400,
                detail={'error': {'code': 'INVALID_FILE', 'message': 'No file uploaded'}},
            )

        import csv
        import json
        import io

        try:
            col_map = json.loads(mapping)
        except Exception:
            col_map = {}

        contents = await file.read()
        text_data = contents.decode('utf-8')
        f = io.StringIO(text_data)
        reader = csv.DictReader(f)
        
        inserted = 0
        updated = 0
        errors = []
        
        for idx, row in enumerate(reader, start=2):
            title_col = col_map.get('title')
            code_col = col_map.get('doc_code')
            era_col = col_map.get('era')
            
            title_val = row.get(title_col) if title_col else None
            code_val = row.get(code_col) if code_col else None
            era_val = row.get(era_col) if era_col else None
            
            if not title_val or not code_val:
                errors.append({"row": idx, "code": code_val or "", "message": "Missing title or doc_code"})
                continue
                
            kwargs = {}
            for schema_key, csv_col in col_map.items():
                if schema_key not in ('title', 'doc_code') and csv_col in row:
                    kwargs[schema_key] = row.get(csv_col)
                    
            try:
                from api.v1.crud.document import compute_title_hash_sha256
                title_hash = compute_title_hash_sha256(
                    era_val,
                    kwargs.get('source_type'),
                    kwargs.get('mks_oks_code'),
                    kwargs.get('okstu_code'),
                    code_val,
                    title_val.strip().lower()
                )
                
                existing = db.query(Document).filter(Document.title_hash_sha256 == title_hash).first()
                if existing:
                    document_crud.update_document(db, str(existing.id), title=title_val, **kwargs)
                    updated += 1
                else:
                    document_crud.create_document(db, doc_code=code_val, title=title_val, **kwargs)
                    inserted += 1
            except Exception as e:
                errors.append({"row": idx, "code": code_val, "message": str(e)})

        return {
            'data': {
                'inserted': inserted,
                'updated': updated,
                'errors': errors
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', '/registry/documents/import/', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.post('/registry/documents/check-uniqueness')
def check_documents_uniqueness(
    payload: dict,
    db: Session = Depends(get_db),
):
    """POST /registry/documents/check-uniqueness/ — duplicate check by metadata.

    Docs: docs/api/registry_service_api.md §3.2.5 - Проверить уникальность документа
    """
    log_event('INFO', '/registry/documents/check-uniqueness/', None, log_payload(payload))
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
        log_event('ERROR', '/registry/documents/check-uniqueness/', None, log_payload(payload), str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/documents/{document_id}')
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
):
    """
    GET /registry/documents/{document_id}/
    Retrieve a single document by ID.

    Docs: docs/api/registry_service_api.md §3.2 - Один документ (описание)
    """
    log_event('INFO', f'/registry/documents/{document_id}/', None, None)
    try:
        document = document_crud.get_document_by_id(db, document_id)
        
        if not document:
            log_event('WARNING', f'/registry/documents/{document_id}/', None, None, 'Document not found')
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
        log_event('ERROR', f'/registry/documents/{document_id}/', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/documents/{document_id}/sections')
def document_sections(
    document_id: str,
    db: Session = Depends(get_db),
):
    """GET /registry/documents/{document_id}/sections/ — full document for RAG Builder.

    Docs: docs/api/registry_service_api.md §3.2.1 - Секции документа (полный объект для RAG Builder)
    """
    log_event('INFO', f'/registry/documents/{document_id}/sections/', None, None)
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
        log_event('ERROR', f'/registry/documents/{document_id}/sections/', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/documents/{document_id}/parameters')
def get_document_parameters_endpoint(
    document_id: str,
    db: Session = Depends(get_db),
):
    """GET /registry/documents/{document_id}/parameters - Извлечённые параметры (формулы)"""
    log_event('INFO', f'/registry/documents/{document_id}/parameters', None, None)
    try:
        document = document_crud.get_document_by_id(db, document_id)
        if not document:
            raise HTTPException(
                status_code=404,
                detail={'error': {'code': 'DOCUMENT_NOT_FOUND', 'message': 'Document not found'}},
            )
        params = document_crud.get_document_parameters(db, document.id)
        return {'data': {'document_id': document.id, 'parameters': params}}
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/documents/{document_id}/parameters', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/documents/{document_id}/pages')
def get_document_pages_endpoint(
    document_id: str,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
):
    """GET /registry/documents/{document_id}/pages - Список страниц документа"""
    log_event('INFO', f'/registry/documents/{document_id}/pages', None, None)
    try:
        document = document_crud.get_document_by_id(db, document_id)
        if not document:
            raise HTTPException(
                status_code=404,
                detail={'error': {'code': 'DOCUMENT_NOT_FOUND', 'message': 'Document not found'}},
            )
        pages_total = document_crud.get_document_pages_count(db, document.id)
        
        pages_list = []
        for i in range(1, pages_total + 1):
            pages_list.append({
                "page": i,
                "width": 595.0,
                "height": 842.0,
                "ocr_status": "completed",
                "confidence": 0.95,
                "has_text_layer": True
            })
            
        start = (page - 1) * page_size
        end = start + page_size
        paged_items = pages_list[start:end]
        
        return {
            'data': {
                'document_id': document.id,
                'pages_total': pages_total,
                'pages': paged_items
            },
            'meta': {
                'total': pages_total,
                'page': page,
                'page_size': page_size
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/documents/{document_id}/pages', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/documents/{document_id}/pages/{page_num}')
def get_document_page_endpoint(
    document_id: str,
    page_num: int,
    db: Session = Depends(get_db),
):
    """GET /registry/documents/{document_id}/pages/{page_num} - Метаданные конкретной страницы"""
    log_event('INFO', f'/registry/documents/{document_id}/pages/{page_num}', None, None)
    try:
        document = document_crud.get_document_by_id(db, document_id)
        if not document:
            raise HTTPException(
                status_code=404,
                detail={'error': {'code': 'DOCUMENT_NOT_FOUND', 'message': 'Document not found'}},
            )
        pages_total = document_crud.get_document_pages_count(db, document.id)
        if page_num < 1 or page_num > pages_total:
            raise HTTPException(
                status_code=404,
                detail={'error': {'code': 'PAGE_NOT_FOUND', 'message': f'Page {page_num} not found. Total pages: {pages_total}'}},
            )
        blocks = document_crud.get_page_blocks(db, document.id, page_num)
        return {
            'data': {
                'document_id': document.id,
                'page': page_num,
                'width': 595.0,
                'height': 842.0,
                'blocks': blocks
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/documents/{document_id}/pages/{page_num}', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/documents/{document_id}/pages/{page_num}/text')
def get_document_page_text_endpoint(
    document_id: str,
    page_num: int,
    db: Session = Depends(get_db),
):
    """GET /registry/documents/{document_id}/pages/{page_num}/text - Текстовый слой страницы"""
    log_event('INFO', f'/registry/documents/{document_id}/pages/{page_num}/text', None, None)
    try:
        document = document_crud.get_document_by_id(db, document_id)
        if not document:
            raise HTTPException(
                status_code=404,
                detail={'error': {'code': 'DOCUMENT_NOT_FOUND', 'message': 'Document not found'}},
            )
        pages_total = document_crud.get_document_pages_count(db, document.id)
        if page_num < 1 or page_num > pages_total:
            raise HTTPException(
                status_code=404,
                detail={'error': {'code': 'PAGE_NOT_FOUND', 'message': f'Page {page_num} not found. Total pages: {pages_total}'}},
            )
        blocks = document_crud.get_page_blocks(db, document.id, page_num)
        return {
            'data': {
                'document_id': document.id,
                'page': page_num,
                'width': 595.0,
                'height': 842.0,
                'blocks': blocks
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/documents/{document_id}/pages/{page_num}/text', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/documents/{document_id}/pages/{page_num}/preview')
def get_document_page_preview_endpoint(
    document_id: str,
    page_num: int,
    db: Session = Depends(get_db),
):
    """GET /registry/documents/{document_id}/pages/{page_num}/preview - Превью страницы"""
    log_event('INFO', f'/registry/documents/{document_id}/pages/{page_num}/preview', None, None)
    try:
        document = document_crud.get_document_by_id(db, document_id)
        if not document:
            raise HTTPException(
                status_code=404,
                detail={'error': {'code': 'DOCUMENT_NOT_FOUND', 'message': 'Document not found'}},
            )
        pages_total = document_crud.get_document_pages_count(db, document.id)
        if page_num < 1 or page_num > pages_total:
            raise HTTPException(
                status_code=404,
                detail={'error': {'code': 'PAGE_NOT_FOUND', 'message': f'Page {page_num} not found. Total pages: {pages_total}'}},
            )
        blocks = document_crud.get_page_blocks(db, document.id, page_num)
        text_layer = "\n".join([b["content"] for b in blocks if b["content"]])
        return {
            'data': {
                'document_id': document.id,
                'page': page_num,
                'key': f"previews/{document.id}/p{page_num}.png",
                'blocks': blocks,
                'text_layer': text_layer
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/documents/{document_id}/pages/{page_num}/preview', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.post('/registry/documents')

def create_document(
    payload: dict,
    db: Session = Depends(get_db),
):
    """
    POST /registry/documents/
    Create a new document.

    Docs: docs/api/registry_service_api.md §3.3 - Создать (основной / из Пайплайна 1)
    """
    log_event('INFO', '/registry/documents/', None, log_payload(payload))
    try:
        # Check if this is the pipeline payload format
        if 'document' in payload:
            try:
                res = document_crud.create_pipeline_document(db, payload)
                return JSONResponse(
                    status_code=201,
                    content=res
                )
            except ValueError as e:
                db.rollback()
                log_event('WARNING', '/registry/documents/', None, payload, f"Transaction rolled back. Reason: {str(e)}")
                err_msg = str(e)
                if err_msg == "DUPLICATE_DOCUMENT":
                    raise HTTPException(
                        status_code=409,
                        detail={'error': {'code': 'DUPLICATE_DOCUMENT', 'message': 'Document with this title hash already exists'}}
                    )
                raise HTTPException(
                    status_code=422,
                    detail={'error': {'code': 'VALIDATION_ERROR', 'message': err_msg}}
                )
            except Exception as e:
                db.rollback()
                log_event('ERROR', '/registry/documents/', None, payload, f"Transaction rolled back. Reason: {str(e)}")
                raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})

        title = payload.get('title')
        doc_code = payload.get('doc_code') or (title or '').strip().upper().replace(' ', '-').replace('/', '-')
        
        if not title:
            log_event('WARNING', '/registry/documents/', None, payload, 'Missing required fields')
            raise HTTPException(
                status_code=422,
                detail={'error': {'code': 'VALIDATION_ERROR', 'message': 'Missing title'}},
            )
        if not doc_code:
            log_event('WARNING', '/registry/documents/', None, payload, 'Missing document code')
            raise HTTPException(
                status_code=422,
                detail={'error': {'code': 'VALIDATION_ERROR', 'message': 'Missing doc_code'}},
            )

        clean_payload = {k: v for k, v in payload.items() if k in {
            'normalized_title', 'source_type', 'group', 'mks_oks_code', 'okstu_code',
            'udk_code', 'era', 'validity_status', 'status', 'jurisdiction', 'issuing_body',
            'adoption_date', 'effective_from', 'replaces', 'status_note', 'file_hash_sha256',
            'title_hash_sha256', 'file_size_bytes', 'processing_status', 'chunk_count',
            'successor_doc_id', 'predecessor_doc_id', 'created_by', 'updated_by',
            'classifier_code', 'industry_code', 'enterprise_id', 'draft_id', 'valid_from', 'valid_until',
            'current_version_id', 'preview_snapshot',
        }}
        
        if 'source_draft_id' in payload:
            clean_payload['draft_id'] = payload['source_draft_id']

        existing_hash = clean_payload.get('title_hash_sha256')
        if not existing_hash:
            existing_hash = document_crud.compute_title_hash_sha256(
                clean_payload.get('era'),
                clean_payload.get('source_type'),
                clean_payload.get('mks_oks_code'),
                clean_payload.get('okstu_code'),
                doc_code,
                clean_payload.get('normalized_title') or (title or '').strip().lower()
            )
        existing = db.query(Document).filter(Document.title_hash_sha256 == existing_hash).first()
        if existing:
            raise HTTPException(
                status_code=409,
                detail={'error': {'code': 'DUPLICATE_DOCUMENT', 'message': 'Document already exists'}},
            )

        document = document_crud.create_document(db, doc_code=doc_code, title=title, commit=False, **clean_payload)
        db.commit()
        
        log_event('INFO', '/registry/documents/', None, {'doc_code': doc_code}, 'Document created')
        
        response_data = DocumentSchema.model_validate(document).model_dump(mode='json', by_alias=True, exclude_none=True)
        response_data['version_id'] = f"v1-{document.id}"
        
        return JSONResponse(
            status_code=201,
            content={'data': response_data},
        )
    except HTTPException as e:
        db.rollback()
        log_event('WARNING', '/registry/documents/', None, payload, f"Transaction rolled back. Reason: HTTP {e.status_code} - {e.detail}")
        raise
    except Exception as e:
        db.rollback()
        log_event('ERROR', '/registry/documents/', None, payload, f"Transaction rolled back. Reason: {str(e)}")
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.put('/registry/documents/{document_id}')
def update_document(
    document_id: str,
    payload: dict,
    db: Session = Depends(get_db),
):
    """
    PUT /registry/documents/{document_id}/
    Update an entire document.

    Docs: docs/api/registry_service_api.md §3.4 - Обновить
    """
    log_event('INFO', f'/registry/documents/{document_id}/', None, log_payload(payload))
    try:
        document = document_crud.update_document(db, document_id, **payload)
        
        if not document:
            log_event('WARNING', f'/registry/documents/{document_id}/', None, None, 'Document not found')
            raise HTTPException(
                status_code=404,
                detail={'error': {'code': 'DOCUMENT_NOT_FOUND', 'message': 'Document not found'}},
            )
        
        log_event('INFO', f'/registry/documents/{document_id}/', None, payload, 'Document updated')
        
        return {
            'data': DocumentSchema.model_validate(document).model_dump(mode='json', by_alias=True, exclude_none=True),
        }
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/documents/{document_id}/', None, payload, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.patch('/registry/documents/{document_id}/status')
def patch_document_status(
    document_id: str,
    payload: dict,
    x_service_id: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    PATCH /registry/documents/{document_id}/status/
    Update the status of a document.

    Docs: docs/api/registry_service_api.md §3.6 - Обновить статус
    """
    log_event('INFO', f'/registry/documents/{document_id}/status/', None, log_payload(payload))
    try:
        if x_service_id != 'orchestrator':
            raise HTTPException(status_code=403, detail={'error': {'code': 'FORBIDDEN', 'message': 'Only Orchestrator can change document status directly'}})

        status = payload.get('status')
        comment = payload.get('comment')
        changed_by = payload.get('changed_by')

        if status is None:
            raise HTTPException(
                status_code=422,
                detail={'error': {'code': 'VALIDATION_ERROR', 'message': 'Missing status'}},
            )

        try:
            res = document_crud.update_document_status(
                db, document_id, status=status, comment=comment, changed_by=changed_by
            )
        except ValueError as e:
            err_msg = str(e)
            raise HTTPException(
                status_code=400,
                detail={'error': {'code': 'VALIDATION_ERROR', 'message': err_msg}}
            )

        if not res:
            raise HTTPException(
                status_code=404,
                detail={'error': {'code': 'DOCUMENT_NOT_FOUND', 'message': 'Document not found'}},
            )

        document, history, previous_status = res

        log_event('INFO', f'/registry/documents/{document_id}/status/', None, payload, 'Document status updated')
        return {
            'data': {
                'id': str(document.id),
                'status': document.status,
                'previous_status': previous_status,
                'history_id': str(history.id),
                'updated_at': document.updated_at.isoformat() if document.updated_at else None,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/documents/{document_id}/status/', None, payload, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})



@routes.patch('/registry/documents/{document_id}')
def patch_document(
    document_id: str,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
):
    """
    PATCH /registry/documents/{document_id}/
    Partially update a document.

    Docs: docs/api/registry_service_api.md §3.5 - Частичное обновление
    """
    log_event('INFO', f'/registry/documents/{document_id}/', None, log_payload(payload))
    try:
        editable_fields = {
            'title', 'metadata', 'validity_status', 'status_note', 'category_ids',
            'valid_from', 'valid_until', 'mks_oks_code', 'okstu_code', 'udk_code'
        }

        # Check for immutable fields
        for field in payload.keys():
            if field not in editable_fields:
                raise HTTPException(
                    status_code=400,
                    detail={'error': {'code': 'IMMUTABLE_FIELD', 'message': f'Field {field} is immutable'}}
                )

        # Build list of updated fields for the response
        updated_fields = list(payload.keys())

        # Extract category_ids if present
        category_ids = None
        if 'category_ids' in payload:
            category_ids = payload.pop('category_ids')
            # Validate categories exist
            from api.v1.models.category import Category
            if category_ids:
                existing_cats_count = db.query(Category).filter(Category.id.in_(category_ids)).count()
                if existing_cats_count != len(category_ids):
                    raise HTTPException(
                        status_code=404,
                        detail={'error': {'code': 'CATEGORY_NOT_FOUND', 'message': 'One or more categories not found'}}
                    )

        # Parse date fields
        from datetime import date
        for date_field in ('valid_from', 'valid_until'):
            if date_field in payload:
                val = payload[date_field]
                if val is None and date_field == 'valid_until':
                    payload[date_field] = date(9999, 12, 31)
                elif isinstance(val, str):
                    try:
                        payload[date_field] = date.fromisoformat(val.split('T')[0])
                    except ValueError:
                        raise HTTPException(
                            status_code=422,
                            detail={'error': {'code': 'VALIDATION_ERROR', 'message': f'Invalid date format for {date_field}'}}
                        )

        # Update the document attributes
        document = document_crud.update_document(db, document_id, **payload)
        if not document:
            log_event('WARNING', f'/registry/documents/{document_id}/', None, None, 'Document not found')
            raise HTTPException(
                status_code=404,
                detail={'error': {'code': 'DOCUMENT_NOT_FOUND', 'message': 'Document not found'}},
            )

        # Update categories if provided
        if category_ids is not None:
            from api.v1.models.category import DocumentCategory
            # Delete existing relations
            db.query(DocumentCategory).filter(DocumentCategory.document_id == document.id).delete(synchronize_session=False)
            # Insert new relations
            for cat_id in category_ids:
                db.add(DocumentCategory(document_id=document.id, category_id=cat_id))
            db.commit()

        log_event('INFO', f'/registry/documents/{document_id}/', None, payload, 'Document patched')

        return {
            'data': {
                'id': document.id,
                'updated_at': document.updated_at.isoformat() if document.updated_at else None,
                'updated_fields': updated_fields
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/documents/{document_id}/', None, payload, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.delete('/registry/documents/{document_id}')
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
):
    """
    DELETE /registry/documents/{document_id}/
    Delete a document.

    Docs: docs/api/registry_service_api.md §3.9 - Удалить
    """
    log_event('INFO', f'/registry/documents/{document_id}/', None, None)
    try:
        if not document_crud.delete_document(db, document_id):
            log_event('WARNING', f'/registry/documents/{document_id}/', None, None, 'Document not found')
            raise HTTPException(
                status_code=404,
                detail={'error': {'code': 'DOCUMENT_NOT_FOUND', 'message': 'Document not found'}},
            )
        
        log_event('INFO', f'/registry/documents/{document_id}/', None, None, 'Document deleted')
        
        return {
            'data': {'message': 'Document deleted'},
        }
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/documents/{document_id}/', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/documents/{document_id}/history')
def document_history(
    document_id: str,
    db: Session = Depends(get_db),
):
    """
    GET /registry/documents/{document_id}/history/
    Return document history.

    Docs: docs/api/registry_service_api.md §3.7 - История статусов
    """
    log_event('INFO', f'/registry/documents/{document_id}/history/', None, None)
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
        log_event('ERROR', f'/registry/documents/{document_id}/history/', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/documents/{document_id}/succession')
def document_succession(
    document_id: str,
    db: Session = Depends(get_db),
):
    """
    GET /registry/documents/{document_id}/succession/
    Return document succession.

    Docs: docs/api/registry_service_api.md §3.8 - Цепочка преемственности
    """
    log_event('INFO', f'/registry/documents/{document_id}/succession/', None, None)
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
        log_event('ERROR', f'/registry/documents/{document_id}/succession/', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.post('/registry/classifiers')
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
        effective_date = payload.get('effective_date')
        replaced_by = payload.get('replaced_by')

        if not classifier_system or not code or not full_name:
            raise HTTPException(
                status_code=422,
                detail={'error': {'code': 'VALIDATION_ERROR', 'message': 'classifier_system, code, and full_name are required'}},
            )

        if effective_date and isinstance(effective_date, str):
            from datetime import date
            try:
                effective_date = date.fromisoformat(effective_date.split('T')[0])
            except ValueError:
                effective_date = None

        existing = classifier_crud.get_classifier(db, classifier_system, code)
        if existing:
            raise HTTPException(
                status_code=409,
                detail={'error': {'code': 'DUPLICATE_CODE', 'message': 'Classifier already exists'}},
            )

        if parent_code:
            parent = classifier_crud.get_classifier(db, classifier_system, parent_code)
            if not parent:
                parent_in_any = db.query(Classifier).filter(Classifier.code == parent_code).first()
                if parent_in_any:
                    raise HTTPException(
                        status_code=409,
                        detail={'error': {'code': 'CROSS_SYSTEM_PARENT', 'message': f'Parent classifier exists in another system: {parent_in_any.classifier_system}'}},
                    )
                raise HTTPException(
                    status_code=404,
                    detail={'error': {'code': 'PARENT_NOT_FOUND', 'message': 'Parent classifier not found'}},
                )

        classifier = classifier_crud.create_classifier(
            db,
            classifier_system=classifier_system,
            code=code,
            full_name=full_name,
            parent_code=parent_code,
            status=status,
            description=description,
            effective_date=effective_date,
            replaced_by=replaced_by,
        )

        return JSONResponse(
            status_code=201,
            content={'data': ClassifierSchema.model_validate(classifier).model_dump(mode='json', by_alias=True, exclude_none=True)},
        )
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', '/registry/classifiers/', None, payload, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/classifiers')
def list_classifiers(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    classifier_system: Optional[str] = None,
    status: Optional[str] = None,
    full_name: Optional[str] = None,
    parent_code: Optional[str] = None,
    code: Optional[str] = None,
    db: Session = Depends(get_db),
):
    log_event('INFO', '/registry/classifiers/', None, None)
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
            code=code,
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
        log_event('ERROR', '/registry/classifiers/', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/classifiers/tree')
def classifier_tree(
    classifier_system: str = Query(...),
    root_code: Optional[str] = None,
    max_depth: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    log_event('INFO', '/registry/classifiers/tree/', None, None)
    """
    Docs: docs/api/registry_service_api.md §1.2 - Дерево (иерархическое)
    """
    try:
        classifiers, max_depth_reached = classifier_crud.get_classifier_tree(
            db, classifier_system, root_code=root_code, search=search, max_depth=max_depth, status=status
        )
        data = [ClassifierSchema.model_validate(item).model_dump(mode='json', by_alias=True, exclude_none=True) for item in classifiers]
        return {
            'data': data,
            'meta': {
                'total': len(data),
                'max_depth_reached': max_depth_reached,
            }
        }
    except Exception as e:
        log_event('ERROR', '/registry/classifiers/tree/', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.post('/registry/classifiers/import')
async def import_classifiers(
    classifier_system: str = Query(...),
    mapping: str = Query(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    log_event('INFO', '/registry/classifiers/import/', None, None)
    """
    Docs: docs/api/registry_service_api.md §1.8 - Импорт
    """
    try:
        if not file:
            raise HTTPException(
                status_code=400,
                detail={'error': {'code': 'INVALID_FILE', 'message': 'No file uploaded'}},
            )

        import csv
        import json
        import io

        try:
            col_map = json.loads(mapping)
        except Exception:
            col_map = {}

        contents = await file.read()
        text_data = contents.decode('utf-8')
        f = io.StringIO(text_data)
        reader = csv.DictReader(f)
        
        inserted = 0
        updated = 0
        errors = []
        
        for idx, row in enumerate(reader, start=2):
            code_col = col_map.get('code')
            name_col = col_map.get('full_name')
            parent_col = col_map.get('parent_code')
            
            code_val = row.get(code_col) if code_col else None
            name_val = row.get(name_col) if name_col else None
            parent_val = row.get(parent_col) if parent_col else None
            
            if not code_val or not name_val:
                errors.append({"row": idx, "code": code_val or "", "message": "Missing code or full_name"})
                continue
                
            existing = classifier_crud.get_classifier(db, classifier_system, code_val)
            if existing:
                classifier_crud.update_classifier(db, classifier_system, code_val, full_name=name_val, parent_code=parent_val)
                updated += 1
            else:
                try:
                    classifier_crud.create_classifier(db, classifier_system, code_val, full_name=name_val, parent_code=parent_val)
                    inserted += 1
                except Exception as e:
                    errors.append({"row": idx, "code": code_val, "message": str(e)})

        return {
            'data': {
                'classifier_system': classifier_system,
                'inserted': inserted,
                'updated': updated,
                'errors': errors
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', '/registry/classifiers/import/', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/classifiers/pending')
def list_classifier_pending(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    system: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    log_event('INFO', '/registry/classifiers/pending/', None, None)
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
            # Calculate suggested parent
            suggested_parent_code = None
            suggested_parent_name = None
            if item.code and '.' in item.code:
                parts = item.code.split('.')
                for i in range(len(parts) - 1, 0, -1):
                    parent_candidate = '.'.join(parts[:i])
                    parent_cls = classifier_crud.get_classifier(db, item.system, parent_candidate)
                    if parent_cls:
                        suggested_parent_code = parent_cls.code
                        suggested_parent_name = parent_cls.full_name
                        break

            data.append({
                'id': str(item.id),
                'system': item.system,
                'code': item.code,
                'found_in_document_id': str(item.found_in_document_id) if item.found_in_document_id else None,
                'found_in_document_title': doc_title,
                'status': item.status,
                'suggested_parent_code': suggested_parent_code,
                'suggested_parent_name': suggested_parent_name,
                'admin_comment': item.admin_comment,
                'created_at': item.created_at.isoformat() if item.created_at else None,
            })
        return {'data': data, 'meta': {'total': total, 'page': page, 'page_size': page_size}}
    except Exception as e:
        log_event('ERROR', '/registry/classifiers/pending/', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.post('/registry/classifiers/pending/{pending_id}/accept')
def accept_classifier_pending(
    pending_id: str,
    payload: dict,
    db: Session = Depends(get_db),
):
    log_event('INFO', f'/registry/classifiers/pending/{pending_id}/accept/', None, log_payload(payload))
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
        log_event('ERROR', f'/registry/classifiers/pending/{pending_id}/accept/', None, log_payload(payload), str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.post('/registry/classifiers/pending/{pending_id}/reject')
def reject_classifier_pending(
    pending_id: str,
    payload: dict,
    db: Session = Depends(get_db),
):
    log_event('INFO', f'/registry/classifiers/pending/{pending_id}/reject/', None, log_payload(payload))
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
        log_event('ERROR', f'/registry/classifiers/pending/{pending_id}/reject/', None, log_payload(payload), str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.post('/registry/classifiers/validate')
def validate_classifiers(
    payload: ClassifierValidateRequest,
    db: Session = Depends(get_db),
):
    log_event('INFO', '/registry/classifiers/validate/', None, log_payload(payload.model_dump()))
    """
    Docs: docs/api/registry_service_api.md §1.12 - Валидация классификации
    """
    try:
        classification = payload.classification.model_dump()
        return {'data': classifier_crud.validate_classification(db, classification)}
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', '/registry/classifiers/validate/', None, log_payload(payload.model_dump()), str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/classifiers/{code}')
def get_classifier(
    code: str,
    classifier_system: str = Query(...),
    db: Session = Depends(get_db),
):
    log_event('INFO', f'/registry/classifiers/{code}/', None, None)
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

        # Retrieve first-level children
        children = db.query(Classifier).filter(
            Classifier.classifier_system == classifier_system,
            Classifier.parent_code == code
        ).all()
        classifier.children = children

        return {
            'data': ClassifierSchema.model_validate(classifier).model_dump(mode='json', by_alias=True, exclude_none=True),
        }
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/classifiers/{code}/', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.put('/registry/classifiers/{code}')
def update_classifier(
    code: str,
    payload: dict,
    classifier_system: str = Query(...),
    db: Session = Depends(get_db),
):
    log_event('INFO', f'/registry/classifiers/{code}/', None, log_payload(payload))
    """
    Docs: docs/api/registry_service_api.md §1.5 - Обновить
    """
    try:
        parent_code = payload.get('parent_code')
        if parent_code:
            parent = classifier_crud.get_classifier(db, classifier_system, parent_code)
            if not parent:
                parent_in_any = db.query(Classifier).filter(Classifier.code == parent_code).first()
                if parent_in_any:
                    raise HTTPException(
                        status_code=409,
                        detail={'error': {'code': 'CROSS_SYSTEM_PARENT', 'message': f'Parent classifier exists in another system: {parent_in_any.classifier_system}'}},
                    )
                raise HTTPException(
                    status_code=404,
                    detail={'error': {'code': 'PARENT_NOT_FOUND', 'message': 'Parent classifier not found'}},
                )

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
        log_event('ERROR', f'/registry/classifiers/{code}/', None, payload, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.patch('/registry/classifiers/{code}')
def patch_classifier(
    code: str,
    payload: dict,
    classifier_system: str = Query(...),
    db: Session = Depends(get_db),
):
    log_event('INFO', f'/registry/classifiers/{code}/', None, log_payload(payload))
    """
    Docs: docs/api/registry_service_api.md §1.6 - Частичное обновление
    """
    try:
        parent_code = payload.get('parent_code')
        if parent_code:
            parent = classifier_crud.get_classifier(db, classifier_system, parent_code)
            if not parent:
                parent_in_any = db.query(Classifier).filter(Classifier.code == parent_code).first()
                if parent_in_any:
                    raise HTTPException(
                        status_code=409,
                        detail={'error': {'code': 'CROSS_SYSTEM_PARENT', 'message': f'Parent classifier exists in another system: {parent_in_any.classifier_system}'}},
                    )
                raise HTTPException(
                    status_code=404,
                    detail={'error': {'code': 'PARENT_NOT_FOUND', 'message': 'Parent classifier not found'}},
                )

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
        log_event('ERROR', f'/registry/classifiers/{code}/', None, payload, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.delete('/registry/classifiers/{code}')
def delete_classifier(
    code: str,
    classifier_system: str = Query(...),
    force: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    log_event('INFO', f'/registry/classifiers/{code}/', None, None)
    """
    Docs: docs/api/registry_service_api.md §1.7 - Удалить
    """
    try:
        force_flag = str(force).lower() == 'true'
        try:
            deleted = classifier_crud.delete_classifier(db, classifier_system, code, force=force_flag)
        except ValueError as e:
            err_code = str(e)
            if err_code not in ('HAS_CHILDREN', 'HAS_DOCUMENTS'):
                err_code = 'DELETE_CONFLICT'
            raise HTTPException(
                status_code=409,
                detail={'error': {'code': err_code, 'message': str(e)}},
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
        log_event('ERROR', f'/registry/classifiers/{code}/', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.post('/registry/terminology')
def create_terminology(
    payload: dict,
    db: Session = Depends(get_db),
):
    log_event('INFO', '/registry/terminology/', None, log_payload(payload))
    """
    Docs: docs/api/registry_service_api.md §2.3 - Создать
    """
    try:
        raw_term = payload.get('raw_term')
        standard_term = payload.get('standard_term')
        normalized_value = payload.get('normalized_value')
        term_type = payload.get('term_type')
        is_blocked = payload.get('is_blocked', False)
        is_case_sensitive = payload.get('is_case_sensitive', False)
        definition = payload.get('definition')
        synonyms = payload.get('synonyms', [])
        related_docs = payload.get('related_docs', [])
        scope = payload.get('scope', [])

        if not raw_term or not standard_term or not normalized_value or not term_type:
            raise HTTPException(
                status_code=422,
                detail={'error': {'code': 'VALIDATION_ERROR', 'message': 'raw_term, standard_term, normalized_value, and term_type are required'}},
            )

        existing = terminology_crud.get_terminology_by_raw_term(db, raw_term)
        if existing:
            raise HTTPException(
                status_code=409,
                detail={'error': {'code': 'DUPLICATE_TERM', 'message': 'Terminology already exists'}},
            )

        term = terminology_crud.create_terminology(
            db,
            raw_term=raw_term,
            standard_term=standard_term,
            normalized_value=normalized_value,
            term_type=term_type,
            is_blocked=is_blocked,
            is_case_sensitive=is_case_sensitive,
            definition=definition,
            synonyms=synonyms,
            related_docs=related_docs,
            scope=scope,
        )

        return JSONResponse(
            status_code=201,
            content={'data': TerminologySchema.model_validate(term).model_dump(mode='json', by_alias=True, exclude_none=True)},
        )
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', '/registry/terminology/', None, payload, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/terminology')
def list_terminology(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    raw_term: Optional[str] = Query(None),
    standard_term: Optional[str] = Query(None),
    term_type: Optional[str] = Query(None),
    is_blocked: Optional[str] = Query(None),
    scope: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    log_event('INFO', '/registry/terminology/', None, None)
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
            standard_term=standard_term,
            term_type=term_type,
            is_blocked=blocked,
            scope=scope,
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
        log_event('ERROR', '/registry/terminology/', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/terminology/normalize')
def normalize_terminology(
    term: str = Query(...),
    db: Session = Depends(get_db),
):
    log_event('INFO', '/registry/terminology/normalize/', None, None)
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
        log_event('ERROR', '/registry/terminology/normalize/', None, {'term': term}, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.post('/registry/terminology/import')
async def import_terminology(
    mapping: str = Query(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    log_event('INFO', '/registry/terminology/import/', None, None)
    """
    Docs: docs/api/registry_service_api.md §2.7 - Импорт
    """
    try:
        if not file:
            raise HTTPException(
                status_code=400,
                detail={'error': {'code': 'INVALID_FILE', 'message': 'No file uploaded'}},
            )

        import csv
        import json
        import io

        try:
            col_map = json.loads(mapping)
        except Exception:
            col_map = {}

        contents = await file.read()
        text_data = contents.decode('utf-8')
        f = io.StringIO(text_data)
        reader = csv.DictReader(f)
        
        inserted = 0
        updated = 0
        errors = []
        
        for idx, row in enumerate(reader, start=2):
            raw_col = col_map.get('raw_term')
            std_col = col_map.get('standard_term') or raw_col
            type_col = col_map.get('term_type')
            
            raw_val = row.get(raw_col) if raw_col else None
            std_val = row.get(std_col) if std_col else raw_val
            type_val = row.get(type_col) if type_col else 'term'
            
            if not raw_val:
                errors.append({"row": idx, "code": "", "message": "Missing raw_term"})
                continue
                
            existing = terminology_crud.get_terminology_by_raw_term(db, raw_val)
            if existing:
                terminology_crud.update_terminology(db, str(existing.id), standard_term=std_val, term_type=type_val)
                updated += 1
            else:
                try:
                    terminology_crud.create_terminology(
                        db,
                        raw_term=raw_val,
                        standard_term=std_val,
                        normalized_value=raw_val.lower(),
                        term_type=type_val
                    )
                    inserted += 1
                except Exception as e:
                    errors.append({"row": idx, "code": raw_val, "message": str(e)})

        return {
            'data': {
                'inserted': inserted,
                'updated': updated,
                'errors': errors
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', '/registry/terminology/import/', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/terminology/{term_id}')
def get_terminology(
    term_id: str,
    db: Session = Depends(get_db),
):
    log_event('INFO', f'/registry/terminology/{term_id}/', None, None)
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
        log_event('ERROR', f'/registry/terminology/{term_id}/', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.put('/registry/terminology/{term_id}')
def update_terminology(
    term_id: str,
    payload: dict,
    db: Session = Depends(get_db),
):
    log_event('INFO', f'/registry/terminology/{term_id}/', None, log_payload(payload))
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
        log_event('ERROR', f'/registry/terminology/{term_id}/', None, payload, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.patch('/registry/terminology/{term_id}')
def patch_terminology(
    term_id: str,
    payload: dict,
    db: Session = Depends(get_db),
):
    log_event('INFO', f'/registry/terminology/{term_id}/', None, log_payload(payload))
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
        log_event('ERROR', f'/registry/terminology/{term_id}/', None, payload, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.delete('/registry/terminology/{term_id}')
def delete_terminology(
    term_id: str,
    db: Session = Depends(get_db),
):
    log_event('INFO', f'/registry/terminology/{term_id}/', None, None)
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
        log_event('ERROR', f'/registry/terminology/{term_id}/', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/enums')
def get_enums(db: Session = Depends(get_db)):
    """
    Docs: docs/api/registry_service_api.md — GET /registry/enums/ (Enums / reference values)
    """
    log_event('INFO', '/registry/enums/', None, None)
    try:
        data = RegistryServiceEnums.get_all_grouped(db)
    except Exception as e:
        log_event('ERROR', '/registry/enums/', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})

    return {'data': data}


@routes.get('/registry/stats')
def get_stats(db: Session = Depends(get_db)):
    """
    Docs: docs/api/registry_service_api.md — GET /registry/stats/ (Statistics)
    """
    log_event('INFO', '/registry/stats/', None, None)
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
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint.

    Docs: docs/api/registry_service_api.md — GET /health/ (Health check)
    """
    from settings import SERVICE_NAME, SERVICE_VERSION
    from sqlalchemy import text
    
    status = 'ok'
    try:
        db.execute(text('SELECT 1'))
    except Exception as e:
        log_event('ERROR', '/health', None, None, f'Health check database connection failed: {str(e)}')
        status = 'error'
        return JSONResponse(
            status_code=500,
            content={
                'status': status,
                'service': SERVICE_NAME,
                'version': SERVICE_VERSION
            }
        )

    return {
        'status': status,
        'service': SERVICE_NAME,
        'version': SERVICE_VERSION
    }



# ============================================================================
# Drafts - Group 4
# ============================================================================

from api.v1.crud import draft as draft_crud
from api.v1.schemas.draft import DraftSchema, DraftCreate, DraftUpdateStatus, DraftUpdateMetadata, DraftSnapshotCreate

@routes.post('/registry/drafts')
def create_draft(
    payload: DraftCreate,
    db: Session = Depends(get_db),
):
    """POST /registry/drafts - Создать запись черновика"""
    log_event('INFO', '/registry/drafts', None, payload.model_dump())
    try:
        draft = draft_crud.create_draft(
            db,
            file_key=payload.file_key,
            document_key=payload.document_key,
            status=payload.status,
            raw_data=payload.raw_data,
            created_by=payload.created_by
        )
        return JSONResponse(status_code=201, content={'data': DraftSchema.model_validate(draft).model_dump(mode='json', by_alias=True, exclude_none=True)})
    except Exception as e:
        log_event('ERROR', '/registry/drafts', None, payload.model_dump(), str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/drafts')
def list_drafts(
    draft_id: Optional[int] = Query(None),
    document_key: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """GET /registry/drafts - Список черновиков"""
    log_event('INFO', '/registry/drafts', None, None)
    try:
        drafts, total = draft_crud.get_drafts(db, page=page, page_size=page_size, draft_id=draft_id, document_key=document_key, status=status)
        data = [DraftSchema.model_validate(d).model_dump(mode='json', by_alias=True, exclude_none=True) for d in drafts]
        return {'data': data, 'meta': {'total': total, 'page': page, 'page_size': page_size}}
    except Exception as e:
        log_event('ERROR', '/registry/drafts', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/drafts/{draft_id}')
def get_draft(draft_id: int, db: Session = Depends(get_db)):
    """GET /registry/drafts/{draft_id} - Полная информация"""
    log_event('INFO', f'/registry/drafts/{draft_id}', None, None)
    try:
        draft = draft_crud.get_draft_by_id(db, draft_id)
        if not draft:
            raise HTTPException(status_code=404, detail={'error': {'code': 'DRAFT_NOT_FOUND', 'message': 'Draft not found'}})
        return {'data': DraftSchema.model_validate(draft).model_dump(mode='json', by_alias=True, exclude_none=True)}
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/drafts/{draft_id}', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/drafts/{draft_id}/preview')
def get_draft_preview(draft_id: int, db: Session = Depends(get_db)):
    """GET /registry/drafts/{draft_id}/preview - Preview-метаданные"""
    log_event('INFO', f'/registry/drafts/{draft_id}/preview', None, None)
    try:
        draft = draft_crud.get_draft_by_id(db, draft_id)
        if not draft:
            raise HTTPException(status_code=404, detail={'error': {'code': 'DRAFT_NOT_FOUND', 'message': 'Draft not found'}})
        
        data = DraftSchema.model_validate(draft).model_dump(mode='json', by_alias=True, exclude_none=True)
        data.pop('raw_data', None)
        data.pop('document_key', None)
        data.pop('error_code', None)
        data.pop('error_message', None)
        data.pop('updated_by', None)
        data.pop('updated_at', None)
        data.pop('created_by', None)
        
        return {'data': data}
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/drafts/{draft_id}/preview', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.patch('/registry/drafts/{draft_id}/status')
def patch_draft_status(draft_id: int, payload: DraftUpdateStatus, db: Session = Depends(get_db)):
    """PATCH /registry/drafts/{draft_id}/status - Обновить статус"""
    log_event('INFO', f'/registry/drafts/{draft_id}/status', None, payload.model_dump())
    try:
        draft = draft_crud.get_draft_by_id(db, draft_id)
        if not draft:
            raise HTTPException(status_code=404, detail={'error': {'code': 'DRAFT_NOT_FOUND', 'message': 'Draft not found'}})
        if draft.status in ('approved', 'discarded'):
            raise HTTPException(status_code=409, detail={'error': {'code': 'DRAFT_ALREADY_DECIDED', 'message': 'Draft is already in a final state'}})

        updated_draft, previous_status = draft_crud.update_draft_status(
            db, draft_id, payload.status, payload.confidence, payload.preview_metadata, payload.error_code, payload.error_message, payload.updated_by
        )
        
        return {
            'data': {
                'id': updated_draft.draft_id,
                'status': updated_draft.status,
                'previous_status': previous_status,
                'updated_at': updated_draft.updated_at.isoformat() if updated_draft.updated_at else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/drafts/{draft_id}/status', None, payload.model_dump(), str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.patch('/registry/drafts/{draft_id}/metadata')
def patch_draft_metadata(draft_id: int, payload: DraftUpdateMetadata, db: Session = Depends(get_db)):
    """PATCH /registry/drafts/{draft_id}/metadata - Обновить метаданные черновика (internal)"""
    log_event('INFO', f'/registry/drafts/{draft_id}/metadata', None, payload.model_dump())
    try:
        draft = draft_crud.get_draft_by_id(db, draft_id)
        if not draft:
            raise HTTPException(status_code=404, detail={'error': {'code': 'DRAFT_NOT_FOUND', 'message': 'Draft not found'}})
        if draft.status in ('approved', 'discarded'):
            raise HTTPException(status_code=409, detail={'error': {'code': 'DRAFT_ALREADY_DECIDED', 'message': 'Draft is already in a final state'}})

        updated_draft = draft_crud.update_draft_metadata(db, draft_id, payload.preview_metadata, payload.metadata_overrides, payload.updated_by)
        
        return {
            'data': {
                'id': updated_draft.draft_id,
                'status': updated_draft.status,
                'preview_metadata': updated_draft.preview_metadata,
                'updated_at': updated_draft.updated_at.isoformat() if updated_draft.updated_at else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/drafts/{draft_id}/metadata', None, payload.model_dump(), str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.delete('/registry/drafts/{draft_id}')
def delete_draft_endpoint(draft_id: int, db: Session = Depends(get_db)):
    """DELETE /registry/drafts/{draft_id} - Удалить запись"""
    log_event('INFO', f'/registry/drafts/{draft_id}', None, None)
    try:
        if not draft_crud.delete_draft(db, draft_id):
            raise HTTPException(status_code=404, detail={'error': {'code': 'DRAFT_NOT_FOUND', 'message': 'Draft not found'}})
        from datetime import datetime, timezone
        return {'data': {'id': draft_id, 'deleted_at': datetime.now(timezone.utc).isoformat()}}
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/drafts/{draft_id}', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.post('/registry/drafts/{draft_id}/snapshot')
def save_draft_snapshot_endpoint(draft_id: int, payload: DraftSnapshotCreate, db: Session = Depends(get_db)):
    """POST /registry/drafts/{draft_id}/snapshot - Сохранить preview-слепок"""
    log_event('INFO', f'/registry/drafts/{draft_id}/snapshot', None, payload.model_dump())
    try:
        draft = draft_crud.save_draft_snapshot(db, draft_id, payload.preview_metadata)
        if not draft:
            raise HTTPException(status_code=404, detail={'error': {'code': 'DRAFT_NOT_FOUND', 'message': 'Draft not found'}})
        return {'data': {'draft_id': draft_id, 'snapshot_saved': True}}
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/drafts/{draft_id}/snapshot', None, payload.model_dump(), str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})




# ============================================================================
# Files and Versions API - Group 5
# ============================================================================

from api.v1.crud import file as file_crud
from api.v1.crud import document_version as version_crud
from api.v1.schemas.file import FileSchema
from api.v1.schemas.document_version import DocumentVersionSchema

@routes.get('/registry/files/{file_id}')
def get_file_metadata(file_id: str, db: Session = Depends(get_db)):
    """GET /registry/files/{file_id} — получить метаданные файла по ID"""
    log_event('INFO', f'/registry/files/{file_id}', None, None)
    try:
        file_rec = file_crud.get_file_by_id(db, file_id)
        if not file_rec:
            raise HTTPException(status_code=404, detail={'error': {'code': 'FILE_NOT_FOUND', 'message': 'File not found'}})
        return {'data': FileSchema.model_validate(file_rec).model_dump(mode='json')}
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/files/{file_id}', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/documents/{document_id}/file')
def get_document_file(
    document_id: int,
    version_id: Optional[int] = Query(None),
    format: str = Query("json"),
    db: Session = Depends(get_db)
):
    """GET /registry/documents/{document_id}/file — получить файл документа"""
    log_event('INFO', f'/registry/documents/{document_id}/file', None, None)
    try:
        from fastapi.responses import RedirectResponse
        from api.v1.models import DocumentVersion
        from datetime import datetime

        # 1. Fetch version
        if version_id:
            version = db.query(DocumentVersion).filter(
                DocumentVersion.document_id == document_id,
                DocumentVersion.id == version_id
            ).first()
        else:
            version = db.query(DocumentVersion).filter(
                DocumentVersion.document_id == document_id
            ).order_by(DocumentVersion.version_number.desc()).first()

        file_key = None
        file_size = 0
        filename = None
        content_type = "application/pdf"

        if version:
            file_key = version.file_key or version.file_path
            file_size = version.file_size_bytes or 0
            filename = version.source_filename

        # 2. Fall back to files table if no version found
        if not file_key:
            files = file_crud.get_files_by_document_id(db, document_id)
            if files:
                # Use the latest file
                files_sorted = sorted(files, key=lambda f: f.uploaded_at or datetime.min, reverse=True)
                file_rec = files_sorted[0]
                file_key = file_rec.storage_path or file_rec.file_id
                file_size = file_rec.size or 0
                filename = file_rec.filename
                content_type = file_rec.mime_type or "application/pdf"

        if not file_key:
            raise HTTPException(
                status_code=404,
                detail={'error': {'code': 'FILE_NOT_FOUND', 'message': 'File not found for the document'}}
            )

        # 3. Handle format
        if format == "binary":
            # Redirect to integration service file endpoint
            return RedirectResponse(url=f"/api/v1/files/{file_key}")
        else:
            # format == "json"
            # Return JSON metadata with pre-signed/direct MinIO download URL
            file_url = f"http://minio:9000/pkb/documents/{file_key}"
            return {
                "data": {
                    "file_url": file_url,
                    "file_size": file_size,
                    "content_type": content_type
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/documents/{document_id}/file', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/documents/{document_id}/files')
def list_document_files(document_id: int, db: Session = Depends(get_db)):
    """GET /registry/documents/{document_id}/files — список файлов, привязанных к документу"""
    log_event('INFO', f'/registry/documents/{document_id}/files', None, None)
    try:
        files = file_crud.get_files_by_document_id(db, document_id)
        data = [FileSchema.model_validate(f).model_dump(mode='json') for f in files]
        return {'data': data}
    except Exception as e:
        log_event('ERROR', f'/registry/documents/{document_id}/files', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/documents/{document_id}/versions')
def list_document_versions(document_id: int, db: Session = Depends(get_db)):
    """GET /registry/documents/{document_id}/versions — список версий документа"""
    log_event('INFO', f'/registry/documents/{document_id}/versions', None, None)
    try:
        versions = version_crud.get_versions_by_document_id(db, document_id)
        data = [DocumentVersionSchema.model_validate(v).model_dump(mode='json') for v in versions]
        return {'data': data}
    except Exception as e:
        log_event('ERROR', f'/registry/documents/{document_id}/versions', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/versions/{version_id}')
def get_document_version(version_id: int, db: Session = Depends(get_db)):
    """GET /registry/versions/{version_id} — получить конкретную версию"""
    log_event('INFO', f'/registry/versions/{version_id}', None, None)
    try:
        version = version_crud.get_version_by_id(db, version_id)
        if not version:
            raise HTTPException(status_code=404, detail={'error': {'code': 'VERSION_NOT_FOUND', 'message': 'Version not found'}})
        return {'data': DocumentVersionSchema.model_validate(version).model_dump(mode='json')}
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/versions/{version_id}', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})



# ============================================================================
# Categories API - Group 6
# ============================================================================

from api.v1.crud import category as category_crud
from api.v1.schemas.category import CategorySchema, CategoryCreateSchema, CategoryUpdateSchema

@routes.get('/registry/categories')
def list_categories(page: int = 1, page_size: int = 50, db: Session = Depends(get_db)):
    """GET /registry/categories — список категорий"""
    log_event('INFO', '/registry/categories', None, None)
    try:
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 50
        records, total = category_crud.get_categories(db, page, page_size)
        data = [CategorySchema.model_validate(r).model_dump(mode='json') for r in records]
        return {
            'data': data,
            'meta': {'total': total, 'page': page, 'page_size': page_size}
        }
    except Exception as e:
        log_event('ERROR', '/registry/categories', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.get('/registry/categories/{category_id}')
def get_category(category_id: int, db: Session = Depends(get_db)):
    """GET /registry/categories/{category_id} — получить одну категорию"""
    log_event('INFO', f'/registry/categories/{category_id}', None, None)
    try:
        category = category_crud.get_category_by_id(db, category_id)
        if not category:
            raise HTTPException(status_code=404, detail={'error': {'code': 'CATEGORY_NOT_FOUND', 'message': 'Category not found'}})
        return {'data': CategorySchema.model_validate(category).model_dump(mode='json')}
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/categories/{category_id}', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.post('/registry/categories', status_code=201)
def create_category_endpoint(schema: CategoryCreateSchema, db: Session = Depends(get_db)):
    """POST /registry/categories — создать категорию"""
    log_event('INFO', '/registry/categories', None, None)
    try:
        # Check duplicate name
        existing = category_crud.get_category_by_name(db, schema.name)
        if existing:
            raise HTTPException(status_code=409, detail={'error': {'code': 'DUPLICATE_CATEGORY_NAME', 'message': 'Category with this name already exists'}})
        category = category_crud.create_category(db, schema)
        return {'data': CategorySchema.model_validate(category).model_dump(mode='json')}
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', '/registry/categories', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.put('/registry/categories/{category_id}')
def update_category_endpoint(category_id: int, schema: CategoryUpdateSchema, db: Session = Depends(get_db)):
    """PUT /registry/categories/{category_id} — обновить категорию"""
    log_event('INFO', f'/registry/categories/{category_id}', None, None)
    try:
        category = category_crud.get_category_by_id(db, category_id)
        if not category:
            raise HTTPException(status_code=404, detail={'error': {'code': 'CATEGORY_NOT_FOUND', 'message': 'Category not found'}})
        
        # If name is provided and different, check for duplicate name
        if schema.name is not None and schema.name.strip() != category.name:
            existing = category_crud.get_category_by_name(db, schema.name)
            if existing and existing.id != category.id:
                raise HTTPException(status_code=409, detail={'error': {'code': 'DUPLICATE_CATEGORY_NAME', 'message': 'Category with this name already exists'}})
                
        updated = category_crud.update_category(db, category, schema)
        return {'data': CategorySchema.model_validate(updated).model_dump(mode='json')}
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/categories/{category_id}', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


@routes.delete('/registry/categories/{category_id}')
def delete_category_endpoint(category_id: int, db: Session = Depends(get_db)):
    """DELETE /registry/categories/{category_id} — удалить категорию"""
    log_event('INFO', f'/registry/categories/{category_id}', None, None)
    try:
        category = category_crud.get_category_by_id(db, category_id)
        if not category:
            raise HTTPException(status_code=404, detail={'error': {'code': 'CATEGORY_NOT_FOUND', 'message': 'Category not found'}})
            
        # Check if linked to documents
        if category_crud.is_category_linked_to_documents(db, category_id):
            raise HTTPException(status_code=409, detail={'error': {'code': 'CATEGORY_HAS_DOCUMENTS', 'message': 'Category is linked to documents and cannot be deleted'}})
            
        category_crud.delete_category(db, category)
        from datetime import datetime, timezone
        return {
            'data': {
                'id': category_id,
                'deleted_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                'message': 'Категория удалена'
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        log_event('ERROR', f'/registry/categories/{category_id}', None, None, str(e))
        raise HTTPException(status_code=500, detail={'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}})


