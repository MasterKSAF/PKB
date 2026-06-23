import os
import sys
from pathlib import Path

# Add project dir to path
sys.path.insert(0, str(Path(__file__).parent))

import env
from sqlalchemy import text
from api.v1.dependencies.database import engine

def fix_infinity():
    with engine.begin() as conn:
        conn.execute(text("UPDATE registry.documents SET valid_until = '9999-12-31' WHERE valid_until = 'infinity'"))
        conn.execute(text("ALTER TABLE registry.documents ALTER COLUMN valid_until SET DEFAULT '9999-12-31'"))
    print("Fixed infinity problem!")

if __name__ == "__main__":
    fix_infinity()
