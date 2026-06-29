from app.services.metadata_extractor import extract_preview_metadata


def _make_raw_json(file_name: str, blocks: list[dict], author: str | None = None) -> dict:
    """Helper to build a raw_json dict similar to parser output."""
    doc: dict = {
        "source": {
            "file_name": file_name,
            "file_hash_sha256": "abc123",
            "page_count": 1,
        },
        "block": blocks,
    }
    if author:
        doc["source"]["author"] = author
    return {
        "metadata": {"schema": "raw_ocr_v4", "task_id": "test"},
        "document": doc,
    }


def test_extract_from_gost_header(raw_gost_sample):
    meta = extract_preview_metadata(raw_gost_sample)
    assert meta["doc_code"] == "20868-81"
    assert meta["document_type"] == "normative"
    assert meta["year"] == 1981
    assert meta["era"] == "USSR"
    assert meta["source_type"] == "GOST"
    assert meta["validity_status"] == "active"
    assert meta["jurisdiction"] == "RU"
    assert meta["language"] == "ru"
    assert meta["pkb_codes"] == []
    assert meta["issuing_body"]


def test_extract_from_circular(raw_circular_sample):
    meta = extract_preview_metadata(raw_circular_sample)
    assert meta["doc_code"] == "311-05-1950ц"
    # Автор "Российский морской регистр судоходства" → RMRS
    assert meta["source_type"] == "RMRS"
    assert meta["issuing_body"]


def test_extract_pkps_from_filename():
    """ПКПС: из пустых блоков doc_code не извлекается, title — из имени файла."""
    raw = _make_raw_json(
        file_name="ПКПС_Часть_VIII_Системы_и_трубопроводы,_изд_2018.pdf",
        blocks=[],
    )
    meta = extract_preview_metadata(raw)
    assert meta["doc_code"] is None
    assert meta["title"] is not None
    assert "ПКПС" in meta["title"]
    assert meta["source_type"] == "RD"


def test_extract_pkps_from_content():
    """ПКПС doc_code извлекается из текстового блока с латинскими/цифровыми символами."""
    raw = _make_raw_json(
        file_name="document.pdf",
        blocks=[
            {"number": 1, "type": "paragraph", "content": "ПКПС-VIII-2018"},
            {"number": 2, "type": "paragraph", "content": "Системы и трубопроводы"},
        ],
    )
    meta = extract_preview_metadata(raw)
    assert meta["doc_code"] == "ПКПС-VIII-2018"
    assert meta["year"] == 2018
    assert meta["source_type"] == "RD"


def test_extract_ost_from_filename():
    """ОСТ: из пустых блоков doc_code не извлекается (ОСТ5 без пробела)."""
    raw = _make_raw_json(
        file_name="ОСТ5_2067_73_Имущество_АСИ_ППИ_и_ЗИП_Крепление_на_судах.pdf",
        blocks=[],
    )
    meta = extract_preview_metadata(raw)
    # Имя файла не подходит под ОСТ regex (ОСТ5_ без пробела после ОСТ5)
    assert meta["doc_code"] is None
    assert meta["title"] is not None


def test_extract_ost_from_content():
    raw = _make_raw_json(
        file_name="doc.pdf",
        blocks=[
            {"number": 1, "type": "paragraph", "content": "ОСТ 5.2067-73 Имущество АСИ"},
        ],
    )
    meta = extract_preview_metadata(raw)
    assert meta["doc_code"] == "5.2067-73"
    assert meta["year"] == 1973
    assert meta["source_type"] == "OST"


def test_extract_rd_from_content():
    raw = _make_raw_json(
        file_name="doc.pdf",
        blocks=[
            {"number": 1, "type": "paragraph", "content": "РД 5.1234-95 Методы испытаний"},
        ],
    )
    meta = extract_preview_metadata(raw)
    assert meta["doc_code"] == "5.1234-95"
    assert meta["year"] == 1995
    assert meta["source_type"] == "RD"


def test_extract_nd_from_content():
    raw = _make_raw_json(
        file_name="doc.pdf",
        blocks=[
            {"number": 1, "type": "paragraph", "content": "НД № 2-020101-063"},
        ],
    )
    meta = extract_preview_metadata(raw)
    assert meta["doc_code"] is not None
    assert "020101" in meta["doc_code"]
    assert meta["source_type"] == "OTHER"


def test_extract_tu_from_content():
    raw = _make_raw_json(
        file_name="doc.pdf",
        blocks=[
            {"number": 1, "type": "paragraph", "content": "ТУ 1234-567-890"},
        ],
    )
    meta = extract_preview_metadata(raw)
    assert meta["doc_code"] == "1234-567-890"
    assert meta["source_type"] == "TU"


def test_extract_pkps_with_spaces():
    """ПКПС с пробелом вместо дефиса."""
    raw = _make_raw_json(
        file_name="doc.pdf",
        blocks=[
            {"number": 1, "type": "paragraph", "content": "ПКПС VIII 2018 Системы"},
        ],
    )
    meta = extract_preview_metadata(raw)
    assert meta["doc_code"] == "ПКПС-VIII-2018"
    assert meta["year"] == 2018
    assert meta["source_type"] == "RD"


def test_extract_rd5_from_content():
    """РД5 с кодом."""
    raw = _make_raw_json(
        file_name="doc.pdf",
        blocks=[
            {"number": 1, "type": "paragraph", "content": "РД5.1234-95"},
        ],
    )
    meta = extract_preview_metadata(raw)
    assert meta["doc_code"] == "5.1234-95"
    assert meta["year"] == 1995
    assert meta["source_type"] == "RD"


def test_extract_ost_with_year_in_content():
    """ОСТ год извлекается из кода."""
    raw = _make_raw_json(
        file_name="doc.pdf",
        blocks=[
            {"number": 1, "type": "paragraph", "content": "ОСТ 5.2067-73 Имущество"},
        ],
    )
    meta = extract_preview_metadata(raw)
    assert meta["doc_code"] == "5.2067-73"
    assert meta["year"] == 1973
    assert meta["era"] == "USSR"


def test_extract_ost_no_space_not_matched():
    """ОСТ5.2067-73 без пробела после ОСТ5 не извлекается (сознательно)."""
    raw = _make_raw_json(
        file_name="doc.pdf",
        blocks=[
            {"number": 1, "type": "paragraph", "content": "ОСТ5.2067-73 Имущество"},
        ],
    )
    meta = extract_preview_metadata(raw)
    # ОСТ5. — нет пробела после ОСТ5, regex требует \s
    assert meta["doc_code"] is None
    # source_type через infer_source_type всё равно определится по тексту
    assert meta["source_type"] == "OST"


def test_title_fallback_from_filename():
    """_find_title fallback: из имени файла, когда блоки пусты."""
    raw = _make_raw_json(
        file_name="РД_5_1234_95_Методы_испытаний.pdf",
        blocks=[],
    )
    meta = extract_preview_metadata(raw)
    assert meta["title"] is not None
    assert "Методы испытаний" in meta["title"]


def test_ost_underscore_filename_no_false_positive():
    """ОСТ5_ в имени файла без пробела не захватывается как код."""
    raw = _make_raw_json(
        file_name="ОСТ5_2067_73_Имущество.pdf",
        blocks=[],
    )
    meta = extract_preview_metadata(raw)
    assert meta["doc_code"] is None  # нет пробела после ОСТ5
    assert meta["title"] is not None


def test_extract_metadata_pkps_no_error():
    """extract_metadata (без LLM) не падает для ПКПС."""
    from app.services.converter_service import extract_metadata
    raw = _make_raw_json(
        file_name="doc.pdf",
        blocks=[
            {"number": 1, "type": "paragraph", "content": "ПКПС-VIII-2018"},
            {"number": 2, "type": "paragraph", "content": "Системы и трубопроводы"},
        ],
    )
    meta = extract_metadata(raw)
    assert meta["doc_code"] == "ПКПС-VIII-2018"
    assert meta["title"] is not None


# ─── ГОСТ Р ─────────────────────────────────────────────────

def test_extract_gost_r_from_content():
    raw = _make_raw_json(
        file_name="doc.pdf",
        blocks=[{"number": 1, "type": "paragraph", "content": "ГОСТ Р 2.105-95 ЕСКД"}],
    )
    meta = extract_preview_metadata(raw)
    assert meta["doc_code"] == "2.105-95"
    assert meta["year"] == 1995
    assert meta["source_type"] == "GOST_R"


# ─── ISO ─────────────────────────────────────────────────────

def test_extract_iso_from_content():
    raw = _make_raw_json(
        file_name="doc.pdf",
        blocks=[{"number": 1, "type": "paragraph", "content": "ISO 9001:2015 Quality"}],
    )
    meta = extract_preview_metadata(raw)
    assert meta["doc_code"] == "9001:2015"
    assert meta["year"] == 2015
    assert meta["source_type"] == "ISO"


def test_extract_iso_without_year():
    raw = _make_raw_json(
        file_name="doc.pdf",
        blocks=[{"number": 1, "type": "paragraph", "content": "ISO 14001 Environmental"}],
    )
    meta = extract_preview_metadata(raw)
    assert meta["doc_code"] == "14001"
    assert meta["source_type"] == "ISO"


# ─── DNV ─────────────────────────────────────────────────────

def test_extract_dnv_from_content():
    raw = _make_raw_json(
        file_name="doc.pdf",
        blocks=[{"number": 1, "type": "paragraph", "content": "DNV-CG-0150"}],
    )
    meta = extract_preview_metadata(raw)
    assert meta["doc_code"] is not None
    assert "DNV" in meta["doc_code"]
    assert meta["source_type"] == "DNV"


def test_extract_dnv_os():
    raw = _make_raw_json(
        file_name="doc.pdf",
        blocks=[{"number": 1, "type": "paragraph", "content": "DNV-OS-E101"}],
    )
    meta = extract_preview_metadata(raw)
    assert meta["doc_code"] is not None
    assert meta["source_type"] == "DNV"


# ─── ASTM ────────────────────────────────────────────────────

def test_extract_astm_from_content():
    raw = _make_raw_json(
        file_name="doc.pdf",
        blocks=[{"number": 1, "type": "paragraph", "content": "ASTM A36 Standard"}],
    )
    meta = extract_preview_metadata(raw)
    assert meta["doc_code"] == "A36"
    assert meta["source_type"] == "ASTM"


def test_extract_astm_numeric():
    raw = _make_raw_json(
        file_name="doc.pdf",
        blocks=[{"number": 1, "type": "paragraph", "content": "ASTM F1153"}],
    )
    meta = extract_preview_metadata(raw)
    assert meta["doc_code"] is not None
    assert meta["source_type"] == "ASTM"


# ─── СНиП / СП ──────────────────────────────────────────────

def test_extract_snip_from_content():
    raw = _make_raw_json(
        file_name="doc.pdf",
        blocks=[{"number": 1, "type": "paragraph", "content": "СНиП 2.04.01-85 Водопровод"}],
    )
    meta = extract_preview_metadata(raw)
    assert meta["doc_code"] == "2.04.01-85"
    assert meta["year"] == 1985
    assert meta["source_type"] == "OTHER"


def test_extract_sp_from_content():
    raw = _make_raw_json(
        file_name="doc.pdf",
        blocks=[{"number": 1, "type": "paragraph", "content": "СП 20.13330.2016 Нагрузки"}],
    )
    meta = extract_preview_metadata(raw)
    assert meta["doc_code"] is not None
    assert meta["source_type"] == "OTHER"


# ─── Чертежи ────────────────────────────────────────────────

def test_extract_drawing_from_content():
    raw = _make_raw_json(
        file_name="doc.pdf",
        blocks=[{"number": 1, "type": "paragraph", "content": "Чертёж ПКБ.123.456"}],
    )
    meta = extract_preview_metadata(raw)
    assert meta["doc_code"] == "ПКБ.123.456"
    assert meta["source_type"] is not None
