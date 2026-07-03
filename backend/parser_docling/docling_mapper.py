"""
Маппер: Docling → JsonStandardizer.
 1. StandardPdfPipeline (layout + таблицы)
 2. layout_analyzer (группировка строк, заголовки, списки)
 3. DoclingPdfParser (сырые строки)
"""
import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'shared'))

import tempfile
import os

from standardizer import JsonStandardizer
from normalizer import Normalizer, ParseResult
from layout_analyzer import parse_pdf as layout_parse
from quality_metrics import assess_quality_from_json

logger = logging.getLogger(__name__)


def docling_to_raw_json(pdf_path: str, max_pages: Optional[int] = None) -> Dict[str, Any]:
    """
    Парсит PDF → raw JSON в формате opendataloader (с `kids`).
    Последовательно пробует три метода.
    """
    file_name = Path(pdf_path).name
    file_bytes = Path(pdf_path).read_bytes()
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    # --- Метод 1: Pipeline ---
    doc = _try_pipeline(pdf_path, max_pages)
    if doc is not None:
        print("  ✅ Pipeline OK", file=sys.stderr, flush=True)
        return _docling_doc_to_raw(doc, pdf_path)

    # --- Метод 2: Layout analyzer ---
    print("  Pipeline failed → layout analyzer...", file=sys.stderr, flush=True)
    raw = layout_parse(pdf_path, max_pages=max_pages)
    if raw and raw.get("kids"):
        raw["file name"] = file_name
        raw["file_hash_sha256"] = file_hash
        print(f"  ✅ Layout analyzer: {len(raw['kids'])} blocks", file=sys.stderr, flush=True)
        return raw

    # --- Метод 3: Raw DoclingPdfParser (строки) ---
    print("  Layout analyzer failed → raw parser...", file=sys.stderr, flush=True)
    doc = _build_via_parse(pdf_path, max_pages)
    if doc is not None:
        raw = _docling_doc_to_raw(doc, pdf_path)
        print(f"  ✅ Raw parser: {len(raw.get('kids', []))} blocks", file=sys.stderr, flush=True)
        return raw

    raise RuntimeError("All parsing methods failed")


def _try_pipeline(pdf_path: str, max_pages: Optional[int] = None):
    """Прямой вызов StandardPdfPipeline.execute() с InputDocument + backend."""
    try:
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.document import InputDocument
        from docling.backend.docling_parse_v2_backend import DoclingParseV2DocumentBackend
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.datamodel.settings import DocumentLimits
        from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline

        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = False
        pipeline_options.do_table_structure = True
        pipeline_options.table_structure_options.do_cell_matching = True
        pipeline_options.accelerator_options.num_threads = 4

        pipeline = StandardPdfPipeline(pipeline_options=pipeline_options)

        limits = DocumentLimits(page_range=(1, max_pages or 9223372036854775807))
        in_doc = InputDocument(
            path_or_stream=Path(pdf_path),
            format=InputFormat.PDF,
            backend=DoclingParseV2DocumentBackend,
            limits=limits,
        )
        if not in_doc.valid:
            return None

        result = pipeline.execute(in_doc, raises_on_error=False)
        if result.status.name == "SUCCESS" and result.document and result.document.pages:
            return result.document
    except Exception as e:
        logger.debug("Pipeline error: %s", e)
    return None


def _build_via_parse(pdf_path: str, max_pages: Optional[int] = None):
    from docling_parse.pdf_parser import DoclingPdfParser
    from docling_core.types.doc import DoclingDocument, BoundingBox, ProvenanceItem, Size, DocItemLabel

    parser = DoclingPdfParser(loglevel="error")
    pdf_doc = parser.load(pdf_path, lazy=True)
    total = pdf_doc.number_of_pages()
    limit = min(max_pages or total, total)

    doc = DoclingDocument(name=Path(pdf_path).stem)
    for page_idx in range(limit):
        page = pdf_doc.get_page(page_idx + 1)
        page_no = page_idx + 1
        dim = page.dimension
        doc.add_page(page_no=page_no, size=Size(
            width=getattr(dim, "width", 595),
            height=getattr(dim, "height", 842),
        ))
        words = list(page.word_cells) if hasattr(page, "word_cells") and page.word_cells else []
        lines = []
        current, last_y = [], None
        for wc in words:
            yc = (wc.rect.r_y1 + wc.rect.r_y3) / 2
            if last_y is not None and abs(yc - last_y) > 5:
                lines.append(current); current = []
            current.append(wc); last_y = yc
        if current:
            lines.append(current)

        for line_words in lines:
            text = " ".join(wc.text for wc in line_words).strip()
            if not text:
                continue
            f, lw = line_words[0], line_words[-1]
            bbox = BoundingBox(l=f.rect.r_x0, t=f.rect.r_y3, r=lw.rect.r_x2, b=f.rect.r_y1)
            prov = ProvenanceItem(page_no=page_no, bbox=bbox, charspan=(0, len(text)))
            doc.add_text(label=DocItemLabel.PARAGRAPH, text=text, prov=prov)

        if (page_idx + 1) % 20 == 0:
            print(f"  Raw parsed {page_idx + 1}/{limit}", file=sys.stderr, flush=True)
    return doc


def _docling_doc_to_raw(doc, pdf_path: str) -> Dict[str, Any]:
    """Конвертирует DoclingDocument в raw JSON (opendataloader-формат)."""
    file_name = Path(pdf_path).name
    file_hash = hashlib.sha256(Path(pdf_path).read_bytes()).hexdigest()

    kids = []
    for item, level in doc.iterate_items():
        prov = getattr(item, "prov", None)
        if not prov:
            continue
        if isinstance(prov, list):
            prov = prov[0] if prov else None
        if not prov:
            continue

        page = prov.page_no
        bbox = [round(prov.bbox.l, 1), round(prov.bbox.t, 1),
                round(prov.bbox.r, 1), round(prov.bbox.b, 1)]
        label = getattr(item, "label", None)

        type_name = "paragraph"
        if label:
            ls = str(label)
            if ls == "title" or ls == "section_header":
                type_name = "heading"
            elif ls == "table":
                type_name = "table"
            elif ls == "picture":
                type_name = "image"

        kid = {"type": type_name, "page number": page, "bounding box": bbox}
        text = getattr(item, "text", "") or ""
        if text.strip():
            kid["content"] = text
        if type_name == "heading":
            kid["heading level"] = 1 if str(label) == "title" else 2

        if type_name == "table" and hasattr(item, "data") and item.data is not None:
            td = item.data
            kid["number of rows"] = td.num_rows
            kid["number of columns"] = td.num_cols
            # Собираем ячейки по grid
            grid = [[""] * td.num_cols for _ in range(td.num_rows)]
            for cell in td.table_cells:
                r = cell.start_row_offset_idx if hasattr(cell, 'start_row_offset_idx') else 0
                c = cell.start_col_offset_idx if hasattr(cell, 'start_col_offset_idx') else 0
                if 0 <= r < td.num_rows and 0 <= c < td.num_cols:
                    grid[r][c] = cell.text if hasattr(cell, 'text') and cell.text else ""
            rows = []
            for r_idx in range(td.num_rows):
                cells = []
                for c_idx in range(td.num_cols):
                    cells.append({
                        "row number": r_idx + 1, "column number": c_idx + 1,
                        "row span": 1, "column span": 1, "page number": page,
                        "bounding box": bbox,
                        "kids": [{"content": grid[r_idx][c_idx], "font": {}}],
                    })
                rows.append({"type": "table row", "row number": r_idx + 1, "cells": cells})
            kid["rows"] = rows

        kids.append(kid)

    return {
        "file name": file_name,
        "file_hash_sha256": file_hash,
        "number of pages": len(doc.pages) if doc.pages else 1,
        "kids": kids,
    }


def convert_docling_to_standard(pdf_path: str, max_pages: Optional[int] = None) -> Dict[str, Any]:
    """Парсит PDF → стандартизированный JSON."""
    raw = docling_to_raw_json(pdf_path, max_pages)

    std = JsonStandardizer()
    standardized = std.transform(raw, Path(pdf_path).name)

    # Оценка качества через quality_metrics (как в parser_service)
    try:
        tmp_path = tempfile.mktemp(suffix='.json')
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(raw, f, ensure_ascii=False)
        reports = assess_quality_from_json(tmp_path)
        os.unlink(tmp_path)
        if reports:
            scores = [r.overall_score for r in reports.values()]
            avg_conf = round(sum(scores) / len(scores), 3) if scores else 0.0
            if "quality" in standardized:
                standardized["quality"]["confidence"] = avg_conf
                for pp in standardized["quality"].get("per_page", []):
                    page = pp["page"]
                    if page in reports:
                        pp["confidence"] = round(reports[page].overall_score, 3)
                        pp["status"] = "low_confidence" if reports[page].is_problematic else "ok"
            print(f"  Quality: avg_confidence={avg_conf:.3f}", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"  Quality assessment error: {e}", file=sys.stderr, flush=True)
        logger.debug("Quality assessment failed: %s", e)

    parse_result = ParseResult(
        full_json=standardized,
        images=[],
        total_pages=raw.get("number of pages", 1),
        temp_dir=None,
    )

    import asyncio
    normalizer = Normalizer()
    container = asyncio.run(normalizer.normalize(parse_result, task_id=0))
    return container["content"]
