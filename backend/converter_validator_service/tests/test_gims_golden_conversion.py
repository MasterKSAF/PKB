from pathlib import Path
import json

import pytest

from app.services.converter_service import convert
from app.services.metadata_extractor import extract_preview_metadata


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "gims_raw_first10.json"


def load_gims_raw() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def item_text(item: dict) -> str:
    payload = item.get("content")
    if isinstance(payload, dict):
        if isinstance(payload.get("text"), str):
            return payload["text"]
        if isinstance(payload.get("items"), list):
            return "\n".join(str(x) for x in payload["items"])
    return str(payload or "")


def test_gims_preview_extracts_basic_metadata():
    raw = load_gims_raw()

    meta = extract_preview_metadata(raw)

    assert meta["title"]
    assert "ПРАВИЛА классификации" in meta["title"]
    assert "Государственной инспекции по" in meta["title"]
    assert meta["year"] == 2004
    assert meta["document_type"] == "normative"
    assert meta["era"] == "RF"
    assert meta["language"] == "ru"
    assert meta["jurisdiction"] == "RU"


@pytest.mark.xfail(
    strict=True,
    reason=(
        "GIMS issuing body is present on the title pages, "
        "but metadata_extractor currently only reads source.author."
    ),
)
def test_gims_preview_should_extract_issuing_body():
    raw = load_gims_raw()

    meta = extract_preview_metadata(raw)

    assert meta["issuing_body"]
    assert (
        "Государственная инспекция по маломерным судам"
        in meta["issuing_body"]
        or "ГИМС" in meta["issuing_body"]
    )


@pytest.mark.asyncio
async def test_gims_convert_preserves_key_body_headings():
    raw = load_gims_raw()

    result = await convert(
        task_id=8,
        version_id=1,
        raw_json=raw,
        use_llm=False,
    )

    texts = [item_text(item) for item in result["document"]["content"]]

    assert any(text.strip() == "ВВЕДЕНИЕ" for text in texts)
    assert any("ЧАСТЬ I" in text and "КЛАССИФИКАЦИЯ" in text for text in texts)
    assert any(text.strip().startswith("1. Общие положения") for text in texts)
    assert any(
        text.strip().startswith("1.1. Определения и понятия")
        for text in texts
    )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "build_hierarchy currently maps every raw block into one content item, "
        "so conversion is effectively raw block pass-through."
    ),
)
@pytest.mark.asyncio
async def test_gims_convert_should_not_be_raw_block_passthrough():
    raw = load_gims_raw()

    result = await convert(
        task_id=8,
        version_id=1,
        raw_json=raw,
        use_llm=False,
    )

    raw_blocks = raw["document"]["block"]
    content = result["document"]["content"]

    assert len(content) != len(raw_blocks)


@pytest.mark.xfail(
    strict=True,
    reason=(
        "TOC pages 3-6 are currently placed into main document.content "
        "instead of being marked as front_matter/toc or excluded from body hierarchy."
    ),
)
@pytest.mark.asyncio
async def test_gims_convert_should_not_put_toc_dot_leaders_into_main_content():
    raw = load_gims_raw()

    result = await convert(
        task_id=8,
        version_id=1,
        raw_json=raw,
        use_llm=False,
    )

    toc_like = [
        item
        for item in result["document"]["content"]
        if item.get("page") in {3, 4, 5, 6}
        and "..." in item_text(item)
    ]

    assert toc_like == []
