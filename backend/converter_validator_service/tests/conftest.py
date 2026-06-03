import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from app.main import app  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def raw_gost_sample() -> dict:
    path = FIXTURES / "raw_gost_sample.json"
    return json.loads(path.read_text(encoding="utf-8"))
