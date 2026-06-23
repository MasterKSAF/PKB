from typing import Optional, List, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from api.v1.models.category import Category, DocumentCategory
from api.v1.schemas.category import CategoryCreateSchema, CategoryUpdateSchema

def get_categories(db: Session, page: int = 1, page_size: int = 50) -> Tuple[List[Category], int]:
    query = db.query(Category)
    total = query.count()
    offset = (page - 1) * page_size
    records = query.order_by(Category.id.asc()).offset(offset).limit(page_size).all()
    return records, total

def get_category_by_id(db: Session, category_id: int) -> Optional[Category]:
    return db.query(Category).filter(Category.id == category_id).first()

def get_category_by_name(db: Session, name: str) -> Optional[Category]:
    return db.query(Category).filter(Category.name == name).first()

def create_category(db: Session, schema: CategoryCreateSchema) -> Category:
    now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
    # Generate code as a unique identifier slug from the name
    generated_code = schema.name.strip().lower().replace(" ", "_")
    
    # Check if generated code is unique, if not add simple suffix
    existing = db.query(Category).filter(Category.code == generated_code).first()
    if existing:
        import uuid
        generated_code = f"{generated_code}_{uuid.uuid4().hex[:8]}"

    category = Category(
        name=schema.name.strip(),
        code=generated_code,
        description=schema.description.strip() if schema.description else None,
        color=schema.color.strip() if schema.color else None,
        created_at=now_naive,
        updated_at=now_naive
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category

def update_category(db: Session, category: Category, schema: CategoryUpdateSchema) -> Category:
    now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
    
    if schema.name is not None:
        name_val = schema.name.strip()
        category.name = name_val
        # Update code slug too if name is changing
        generated_code = name_val.lower().replace(" ", "_")
        # Ensure new code uniqueness (excluding self)
        existing = db.query(Category).filter(Category.code == generated_code, Category.id != category.id).first()
        if existing:
            import uuid
            generated_code = f"{generated_code}_{uuid.uuid4().hex[:8]}"
        category.code = generated_code

    if schema.description is not None:
        category.description = schema.description.strip() if schema.description else None
        
    if schema.color is not None:
        category.color = schema.color.strip() if schema.color else None

    category.updated_at = now_naive
    db.commit()
    db.refresh(category)
    return category

def delete_category(db: Session, category: Category) -> None:
    db.delete(category)
    db.commit()

def is_category_linked_to_documents(db: Session, category_id: int) -> bool:
    count = db.query(DocumentCategory).filter(DocumentCategory.category_id == category_id).count()
    return count > 0
