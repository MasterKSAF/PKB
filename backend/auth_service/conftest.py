import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://unused:unused@localhost:5432/unused")
os.environ.setdefault("JWT_SECRET_KEY", "test_secret_key_for_pytest_only_32chars!!")
os.environ.setdefault("DEFAULT_ADMIN_EMAIL", "admin@test.com")
os.environ.setdefault("DEFAULT_ADMIN_PASSWORD", "Admin1234!")
os.environ.setdefault("ENV", "test")
