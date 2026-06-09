import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from api.v1.dependencies.database import get_db
from api.v1.models.base import Base
# Import all models to ensure they are registered with Base
from api.v1.models import *

# SQLITE database URL for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    execution_options={"schema_translate_map": {"purgatory": None}}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from sqlalchemy import event
from sqlalchemy.schema import Table, ColumnDefault
from sqlalchemy.sql.elements import TextClause
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapper
import uuid

from sqlalchemy import BigInteger

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

@compiles(BigInteger, "sqlite")
def compile_bigint_sqlite(type_, compiler, **kw):
    return "INTEGER"


@event.listens_for(Table, "before_create")
def sqlite_postgres_fix(target, connection, **kw):
    target.schema = None
    for fk in target.foreign_keys:
        if isinstance(fk._colspec, str) and fk._colspec.startswith('purgatory.'):
            fk._colspec = fk._colspec.replace('purgatory.', '')
    for column in target.columns:
        if column.server_default is not None:
            if isinstance(column.server_default.arg, TextClause):
                column.server_default = None

@pytest.fixture(scope="function")
def db_session():
    # Create fresh tables for each test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Seed rs_enums via ORM to support UUID generation
    from api.v1.models.registry_service_enums import RegistryServiceEnums
    default_enums = [
        ('classifier_system', 'MKS'),
        ('classifier_system', 'OKSTU'),
        ('classifier_system', 'UDC'),
        ('classifier_system', 'EXTERNAL'),
        ('classifier_status', 'active'),
        ('classifier_status', 'deprecated'),
        ('classifier_status', 'archived'),
        ('source_type', 'GOST'),
        ('source_type', 'GOST_R'),
        ('source_type', 'OST'),
        ('source_type', 'RD'),
        ('source_type', 'TU'),
        ('source_type', 'ISO'),
        ('source_type', 'DNV'),
        ('source_type', 'ASTM'),
        ('source_type', 'OTHER'),
        ('document_status', 'draft'),
        ('document_status', 'uploaded'),
        ('document_status', 'validating'),
        ('document_status', 'processing'),
        ('document_status', 'review_required'),
        ('document_status', 'ready_for_promotion'),
        ('document_status', 'approved'),
        ('document_status', 'failed'),
        ('document_status', 'archived'),
        ('era', 'USSR'),
        ('era', 'CIS'),
        ('era', 'RF'),
        ('era', 'CURRENT'),
        ('validity_status', 'active'),
        ('validity_status', 'superseded'),
        ('validity_status', 'cancelled'),
        ('validity_status', 'historical'),
        ('validity_status', 'draft'),
        ('jurisdiction', 'RU'),
        ('jurisdiction', 'EU'),
        ('jurisdiction', 'US'),
        ('jurisdiction', 'NO'),
        ('jurisdiction', 'INTL'),
        ('term_type', 'acronym'),
        ('term_type', 'foreign_term'),
        ('term_type', 'standard_code'),
        ('term_type', 'avatar'),
        ('term_type', 'symbol'),
        ('classification_status_code', 'CONFIRMED'),
        ('classification_status_code', 'PENDING_REVIEW'),
        ('classification_status_code', 'NOT_FOUND'),
        ('classification_status_code', 'NOT_USED'),
        ('classification_status_code', 'UNASSIGNED'),
        ('pending_status', 'new'),
        ('pending_status', 'mapped'),
        ('pending_status', 'rejected'),
        ('validation_status', 'pending'),
        ('validation_status', 'valid'),
        ('validation_status', 'invalid'),
        ('chunk_type', 'text'),
        ('chunk_type', 'table'),
        ('chunk_type', 'image'),
        ('chunk_type', 'formula')
    ]
    try:
        for key, value in default_enums:
            db.add(RegistryServiceEnums(enum_key=key, enum_value=value))
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Warning: Failed to seed rs_enums database table: {e}")
            
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
