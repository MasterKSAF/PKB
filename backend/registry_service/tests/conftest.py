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

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

@event.listens_for(Mapper, "before_insert")
def set_uuid_default(mapper, connection, target):
    if hasattr(target, 'id') and target.id is None:
        target.id = uuid.uuid4()

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
