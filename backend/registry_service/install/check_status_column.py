"""Check registry.documents.status column (uses .env app user)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import env  # noqa: F401
import os

from sqlalchemy import create_engine, text

database_url = (
    f"postgresql://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_DATABASE')}"
)
engine = create_engine(database_url)
with engine.connect() as conn:
    row = conn.execute(
        text(
            """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'registry'
              AND table_name = 'documents'
              AND column_name = 'status'
            """
        )
    ).fetchone()
    owner = conn.execute(
        text(
            """
            SELECT tableowner
            FROM pg_tables
            WHERE schemaname = 'registry' AND tablename = 'documents'
            """
        )
    ).scalar()
print("table owner:", owner)
print("status column:", row if row else "NOT FOUND")
