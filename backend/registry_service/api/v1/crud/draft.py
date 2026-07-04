from datetime import datetime, timezone
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from api.v1.models import Draft

def create_draft(
    db: Session,
    file_key: str,
    document_key: str,
    status: str,
    raw_data: Optional[dict],
    created_by: str,
    original_filename: Optional[str] = None,
    file_hash_sha256: Optional[str] = None,
    title_hash_sha256: Optional[str] = None,
    title_key: Optional[str] = None,
) -> Draft:
    draft = Draft(
        file_key=file_key,
        document_key=document_key,
        original_filename=original_filename,
        status=status,
        raw_data=raw_data,
        created_by=created_by,
        file_hash_sha256=file_hash_sha256,
        title_hash_sha256=title_hash_sha256,
        title_key=title_key,
        created_at=func.now(),
        updated_at=func.now()
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft

def get_drafts(db: Session, page: int = 1, page_size: int = 50, draft_id: Optional[int] = None, document_key: Optional[str] = None, status: Optional[str] = None) -> Tuple[List[Draft], int]:
    query = db.query(Draft)
    
    if draft_id is not None:
        query = query.filter(Draft.draft_id == draft_id)
    if document_key is not None:
        query = query.filter(Draft.document_key == document_key)
    if status is not None:
        query = query.filter(Draft.status == status)
        
    total = query.count()
    drafts = query.order_by(Draft.draft_id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return drafts, total

def get_draft_by_id(db: Session, draft_id: int) -> Optional[Draft]:
    return db.query(Draft).filter(Draft.draft_id == draft_id).first()

def update_draft_status(db: Session, draft_id: int, status: str, confidence: Optional[float] = None, preview_metadata: Optional[dict] = None, error_code: Optional[str] = None, error_message: Optional[str] = None, updated_by: Optional[str] = None) -> Tuple[Optional[Draft], Optional[str]]:
    draft = get_draft_by_id(db, draft_id)
    if not draft:
        return None, None
        
    previous_status = draft.status
    draft.status = status
    if confidence is not None:
        draft.confidence = confidence
    if preview_metadata is not None:
        draft.preview_metadata = preview_metadata
    if error_code is not None:
        draft.error_code = error_code
    if error_message is not None:
        draft.error_message = error_message
    if updated_by is not None:
        draft.updated_by = updated_by
        
    draft.updated_at = func.now()
    db.commit()
    db.refresh(draft)
    return draft, previous_status

def update_draft_metadata(db: Session, draft_id: int, preview_metadata: dict, metadata_overrides: Optional[dict], updated_by: str) -> Optional[Draft]:
    draft = get_draft_by_id(db, draft_id)
    if not draft:
        return None
        
    draft.preview_metadata = preview_metadata
    # Save metadata_overrides directly inside preview_metadata if present
    if metadata_overrides:
        if not isinstance(draft.preview_metadata, dict):
            draft.preview_metadata = {}
        draft.preview_metadata['metadata_overrides'] = metadata_overrides
        
    draft.updated_by = updated_by
    draft.updated_at = func.now()
    db.commit()
    db.refresh(draft)
    return draft

def save_draft_snapshot(db: Session, draft_id: int, preview_metadata: dict) -> Optional[Draft]:
    draft = get_draft_by_id(db, draft_id)
    if not draft:
        return None
    draft.preview_metadata = preview_metadata
    draft.updated_at = func.now()
    db.commit()
    db.refresh(draft)
    return draft

def get_draft_pages_from_raw(draft: Draft) -> list[dict]:
    """Извлечь список страниц из raw_data черновика."""
    raw = draft.raw_data or {}
    doc = raw.get("document", {})
    return doc.get("pages", [])


def get_draft_page_blocks(draft: Draft, page_num: int) -> list[dict]:
    """Извлечь блоки для указанной страницы из raw_data черновика."""
    raw = draft.raw_data or {}
    doc = raw.get("document", {})
    blocks = doc.get("block", [])
    return [b for b in blocks if b.get("page") == page_num]


def delete_draft(db: Session, draft_id: int) -> bool:
    draft = get_draft_by_id(db, draft_id)
    if not draft:
        return False
    db.delete(draft)
    db.commit()
    return True


def _extract_text(block: dict) -> str:
    """Извлечь текст из блока любой вложенности."""
    content = block.get('content') or ''
    if content:
        return str(content)
    # Вложенные block (list, text_block)
    children = block.get('block') or []
    parts = []
    for child in children:
        parts.append(_extract_text(child))
    return ' '.join(parts)


def draft_blocks_to_markdown(blocks: list[dict], files_base_url: str = '/files') -> str:
    """Конвертировать blocks из raw_data черновика в Markdown.

    Поддерживаемые типы: heading, paragraph, image, table, list,
    formula, caption, text_block.
    """
    md_parts = []
    for b in blocks:
        md = _block_to_md(b, files_base_url)
        if md:
            md_parts.append(md)
    return '\n\n'.join(md_parts)


def _block_to_md(b: dict, files_base_url: str) -> str:
    btype = b.get('type', '')

    if btype == 'heading':
        level = b.get('heading_level', 1)
        content = b.get('content') or ''
        return f"{'#' * level} {content}"

    if btype == 'paragraph':
        return b.get('content') or ''

    if btype == 'image':
        image_key = b.get('image_key') or ''
        if not image_key:
            return ''
        alt = b.get('content') or f"Страница {b.get('page', '')}"
        return f"![{alt}]({files_base_url}/{image_key})"

    if btype == 'table':
        return _table_to_md(b)

    if btype == 'list':
        return _list_to_md(b)

    if btype == 'formula':
        latex = b.get('latex') or ''
        if latex:
            return f"$$\n{latex}\n$$"
        image_key = b.get('image_key')
        if image_key:
            return f"![formula]({files_base_url}/{image_key})"
        return ''

    if btype == 'caption':
        return f"> {b.get('content') or ''}"

    if btype == 'text_block':
        children = b.get('block') or []
        return '\n'.join(_extract_text(c) for c in children if _extract_text(c))

    # fallback
    return b.get('content') or ''


def _table_to_md(b: dict) -> str:
    """Конвертировать table-блок в GFM pipe table."""
    rows_data = b.get('rows') or []
    if not rows_data:
        return ''

    # Собираем строки
    md_rows = []
    for row in rows_data:
        cells = row.get('cells') or []
        row_cells = []
        for cell in cells:
            cell_blocks = cell.get('block') or []
            cell_text = ' '.join(
                cb.get('content', '') for cb in cell_blocks if cb.get('content')
            )
            row_cells.append(cell_text)
        md_rows.append('| ' + ' | '.join(row_cells) + ' |')

    if not md_rows:
        return ''

    # Определяем количество колонок
    num_cols = len(rows_data[0].get('cells') or [])
    if num_cols == 0:
        return md_rows[0]

    # Разделитель
    separator = '| ' + ' | '.join(['---'] * num_cols) + ' |'

    result = [md_rows[0], separator]
    result.extend(md_rows[1:])
    return '\n'.join(result)


def _list_to_md(b: dict) -> str:
    """Конвертировать list-блок в маркированный/нумерованный список."""
    style = b.get('numbering_style', 'bullet')
    items = b.get('block') or []
    md_lines = []
    for i, item in enumerate(items, 1):
        text = _extract_text(item)
        if not text:
            continue
        if style == 'bullet':
            md_lines.append(f"- {text}")
        else:
            md_lines.append(f"{i}. {text}")
    return '\n'.join(md_lines)

