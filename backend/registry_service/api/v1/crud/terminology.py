import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from api.v1.models import Terminology


def get_terminology(
    db: Session,
    page: int = 1,
    page_size: int = 50,
    raw_term: Optional[str] = None,
    standard_term: Optional[str] = None,
    term_type: Optional[str] = None,
    is_blocked: Optional[bool] = None,
    scope: Optional[str] = None,
) -> tuple[List[Terminology], int]:
    query = db.query(Terminology)

    if raw_term:
        query = query.filter(Terminology.raw_term.ilike(f'%{raw_term}%'))

    if standard_term:
        query = query.filter(Terminology.standard_term.ilike(f'%{standard_term}%'))

    if term_type:
        query = query.filter(Terminology.term_type == term_type)

    if is_blocked is not None:
        query = query.filter(Terminology.is_blocked == is_blocked)

    if scope:
        from sqlalchemy import cast, Text, or_
        import json
        conds = [cast(Terminology.scope, Text).ilike(f'%"{scope}"%')]
        try:
            escaped_val = json.dumps(scope)[1:-1]
            conds.append(cast(Terminology.scope, Text).ilike(f'%"{escaped_val}"%'))
            escaped_lower = json.dumps(scope.lower())[1:-1]
            conds.append(cast(Terminology.scope, Text).ilike(f'%"{escaped_lower}"%'))
            escaped_upper = json.dumps(scope.upper())[1:-1]
            conds.append(cast(Terminology.scope, Text).ilike(f'%"{escaped_upper}"%'))
        except Exception:
            pass
        if db.bind.dialect.name == "postgresql":
            conds.append(Terminology.scope.has_key(scope))
        query = query.filter(or_(*conds))

    total = query.count()
    skip = (page - 1) * page_size
    terms = query.order_by(desc(Terminology.created_at)).offset(skip).limit(page_size).all()
    return terms, total


def get_terminology_by_id(db: Session, term_id: str) -> Optional[Terminology]:
    try:
        term_int = int(str(term_id))
    except (ValueError, TypeError):
        return None
    return db.query(Terminology).filter(Terminology.id == term_int).first()


def get_terminology_by_raw_term(db: Session, raw_term: str) -> Optional[Terminology]:
    return db.query(Terminology).filter(Terminology.raw_term == raw_term).first()


def create_terminology(
    db: Session,
    raw_term: str,
    standard_term: str,
    normalized_value: str,
    term_type: str,
    is_blocked: Optional[bool] = False,
    definition: Optional[str] = None,
    **kwargs,
) -> Terminology:
    term = Terminology(
        raw_term=raw_term,
        standard_term=standard_term,
        normalized_value=normalized_value,
        term_type=term_type,
        is_blocked=is_blocked,
        definition=definition,
        **kwargs,
    )
    db.add(term)
    db.commit()
    db.refresh(term)
    return term


def update_terminology(db: Session, term_id: str, **kwargs) -> Optional[Terminology]:
    term = get_terminology_by_id(db, term_id)
    if not term:
        return None

    for key, value in kwargs.items():
        if hasattr(term, key):
            setattr(term, key, value)

    db.commit()
    db.refresh(term)
    return term


def delete_terminology(db: Session, term_id: str) -> bool:
    term = get_terminology_by_id(db, term_id)
    if not term:
        return False

    db.delete(term)
    db.commit()
    return True
