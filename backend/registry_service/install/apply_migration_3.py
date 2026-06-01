"""Apply install/3. add_documents_status.sql using credentials from .env."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import env  # noqa: F401  # loads .env
from sqlalchemy import create_engine, text

sql_path = Path(__file__).parent / "3. add_documents_status.sql"
sql = sql_path.read_text(encoding="utf-8")

database_url = (
    f"postgresql://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_DATABASE')}"
)

def _statements(script: str) -> list[str]:
    parts = []
    for block in script.split(";"):
        lines = [
            line for line in block.splitlines()
            if line.strip() and not line.strip().startswith("--")
        ]
        if lines:
            parts.append("\n".join(lines))
    return parts


statements = _statements(sql)

engine = create_engine(database_url)
with engine.begin() as conn:
    for stmt in statements:
        conn.execute(text(stmt))
        first_line = stmt.splitlines()[0]
        print(f"OK: {first_line}")

print("Migration applied successfully.")
