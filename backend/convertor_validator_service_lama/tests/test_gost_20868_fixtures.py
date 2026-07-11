import json
from collections import Counter
from pathlib import Path


_FIXTURE_DIR = Path(__file__).parent / "fixtures" / "gost_20868_81"


def _load_fixture(name: str) -> dict:
    return json.loads((_FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_gost_20868_v2_chunk_container_fixture_has_expected_layers() -> None:
    data = _load_fixture("chunk_container_v2.json")

    assert data["document"]["doc_code"] == "\u0413\u041e\u0421\u0422 20868-81"
    assert (
        data["document"]["title"]
        == "\u0421\u0422\u041e\u0419\u041a\u0418 \u0423\u0421\u0422\u0410\u041d\u041e\u0412\u041e\u0427\u041d\u042b\u0415 \u041a\u0420\u0415\u041f\u0415\u0416\u041d\u042b\u0415. \u0422\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0438\u0435 \u0442\u0440\u0435\u0431\u043e\u0432\u0430\u043d\u0438\u044f"
    )

    sections = data["sections"]
    assert len(sections) == 18

    section_types = Counter(section["type"] for section in sections)
    assert section_types == {
        "text": 15,
        "image": 2,
        "table": 1,
    }

    clauses = {section["clause"] for section in sections}
    assert {"title", "figure-1", "figure-2", "table-1", "note"}.issubset(clauses)

    references_count = sum(len(section.get("references") or []) for section in sections)
    assert references_count == 6


def test_gost_20868_formula_chunk_container_fixture_adds_formula_layer() -> None:
    data = _load_fixture("chunk_container_formulas.json")

    sections = data["sections"]
    assert len(sections) == 19

    section_types = Counter(section["type"] for section in sections)
    assert section_types["formula"] == 1

    formula_sections = [
        section
        for section in sections
        if section["type"] == "formula"
    ]
    assert formula_sections[0]["clause"] == "formula-test"
    assert formula_sections[0]["content"]["latex"]
