import pytest
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import os
import shutil
from pathlib import Path
import sys

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

# SQLAlchemy SQLite dialect schema ignore trick
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.schema import CreateTable, DropTable
from sqlalchemy.sql.ddl import CreateIndex

@compiles(CreateTable, "sqlite")
def _compile_create_table(element, compiler, **kw):
    element.element.schema = None
    return compiler.visit_create_table(element, **kw)

@compiles(DropTable, "sqlite")
def _compile_drop_table(element, compiler, **kw):
    element.element.schema = None
    return compiler.visit_drop_table(element, **kw)

@compiles(CreateIndex, "sqlite")
def _compile_create_index(element, compiler, **kw):
    element.element.schema = None
    return compiler.visit_create_index(element, **kw)

# Now import the app and models
from main import app
from api.v1.database import Base, get_db
from config import settings

# Setup in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(setup_database):
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def test_client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
        
    app.dependency_overrides.clear()

@pytest.fixture(scope="function", autouse=True)
def setup_test_directories(tmp_path):
    # Override settings for tests
    old_dirs = settings.STORAGE_DIRECTORIES
    
    test_dir_1 = tmp_path / "files1"
    test_dir_2 = tmp_path / "files2"
    
    test_dir_1.mkdir()
    test_dir_2.mkdir()
    
    settings.STORAGE_DIRECTORIES = [test_dir_1, test_dir_2]
    
    yield
    
    settings.STORAGE_DIRECTORIES = old_dirs
