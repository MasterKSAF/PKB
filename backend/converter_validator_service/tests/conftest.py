import json
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("LLM_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("LLM_MODEL", "gpt-4o-mini")
os.environ.setdefault(
    "LLM_QUERY",
    "Уточни метаданные нормативного документа (код МКС, группа, эра) на основе JSON. Верни только JSON с ключами: mks_oks_code, group, era, validity_status.",
)

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


@pytest.fixture
def raw_circular_sample() -> dict:
    path = FIXTURES / "raw_circular_sample.json"
    return json.loads(path.read_text(encoding="utf-8"))
