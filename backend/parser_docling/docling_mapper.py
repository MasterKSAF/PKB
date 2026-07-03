"""
Маппер: Docling → JsonStandardizer.
 1. StandardPdfPipeline (layout + таблицы)
 2. enrich — заполнение пустых блоков из сырого PDF
"""
import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'shared'))

import tempfile
import os

from standardizer import JsonStandardizer
from normalizer import Normalizer, ParseResult
from quality_metrics import assess_quality_from_json

logger = logging.getLogger(__name__)


def docling_to_raw_json(pdf_path: str, max_pages: Optional[int] = None) -> Dict[str, Any]:
    """
    Парсит PDF → raw JSON в формате opendataloader (с `kids`).
    Pipeline + обогащение пустых блоков из сырого PDF.
    """
    file_name = Path(pdf_path).name
    file_bytes = Path(pdf_path).read_bytes()
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    doc = _try_pipeline(pdf_path, max_pages)
    if doc is None:
        raise RuntimeError("Pipeline failed")

    print("  ✅ Pipeline OK", file=sys.stderr, flush=True)
    raw = _docling_doc_to_raw(doc, pdf_path)
    raw["file name"] = file_name
    raw["file_hash_sha256"] = file_hash

    # Обогащение: заполняем пустые блоки (таблицы, параграфы) из сырого PDF
    enriched = _enrich_empty_blocks(pdf_path, raw)
    return enriched


def _try_pipeline(pdf_path: str, max_pages: Optional[int] = None, page_start: int = 1):
    """
    StandardPdfPipeline.execute() с батчами по 5 страниц.
    Надёжнее DocumentConverter — нет std::bad_alloc на больших диапазонах.
    """
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
        pipeline_options.layout_batch_size = 2
        pipeline_options.table_batch_size = 2

        pipeline = StandardPdfPipeline(pipeline_options=pipeline_options)

        # Определяем общее количество страниц
        limits_all = DocumentLimits(page_range=(1, 1))
        in_doc_all = InputDocument(
            path_or_stream=Path(pdf_path),
            format=InputFormat.PDF,
            backend=DoclingParseV2DocumentBackend,
            limits=limits_all,
        )
        if not in_doc_all.valid:
            return None
        total_pages = in_doc_all.page_count
        page_limit = min(max_pages or total_pages, total_pages)

        from docling_core.types.doc import DoclingDocument
        result_doc = DoclingDocument(name=Path(pdf_path).stem)
        batch_size = 5

        for start in range(page_start, page_limit + 1, batch_size):
            end = min(start + batch_size - 1, page_limit)
            limits = DocumentLimits(page_range=(start, end))
            in_doc = InputDocument(
                path_or_stream=Path(pdf_path),
                format=InputFormat.PDF,
                backend=DoclingParseV2DocumentBackend,
                limits=limits,
            )
            if not in_doc.valid:
                continue

            result = pipeline.execute(in_doc, raises_on_error=False)
            if result.status.name == "SUCCESS" and result.document and result.document.pages:
                _merge_pages(result_doc, result.document)

        if result_doc.pages:
            return result_doc

    except Exception as e:
        logger.debug("Pipeline error: %s", e)
    return None


def _merge_pages(target, source):
    """Сливает содержимое source в target."""
    from docling_core.types.doc import DoclingDocument
    for page_no, page in source.pages.items():
        if page_no not in target.pages:
            target.add_page(page_no=page_no, size=page.size)
    for item, level in source.iterate_items():
        prov = getattr(item, "prov", None)
        if not prov:
            continue
        if isinstance(prov, list):
            prov = prov[0] if prov else None
        if not prov:
            continue

        label = getattr(item, "label", None)
        text = getattr(item, "text", None)
        item_type = type(item).__name__

        if item_type == "TextItem":
            target.add_text(label=label, text=text or "", prov=prov)
        elif item_type == "TableItem" and hasattr(item, "data") and item.data is not None:
            target.add_table(data=item.data, prov=prov)
        elif item_type == "PictureItem":
            target.add_picture(prov=prov)
        else:
            target.add_text(label=label, text=text or "", prov=prov)


def _enrich_empty_blocks(pdf_path: str, raw: dict) -> dict:
    """
    Обогащение: для блоков с пустым content извлекает текст из сырого PDF
    через PyMuPDF (координаты совпадают с Docling).
    """
    try:
        import fitz
    except ImportError:
        return raw

    kids = raw.get("kids", [])
    if not kids:
        return raw

    # Определяем, какие страницы нужно загрузить
    pages_needed = sorted(set(
        k.get("page number", 0) for k in kids
        if not k.get("content", "").strip()
    ))
    if not pages_needed:
        return raw

    # Открываем PDF и извлекаем текст по страницам
    doc = fitz.open(pdf_path)
    page_text_blocks = {}  # page_no -> [(bbox, text), ...]

    for pno in pages_needed:
        if pno < 1 or pno > len(doc):
            continue
        page = doc[pno - 1]
        blocks = page.get_text('dict')['blocks']
        text_blocks = []
        for b in blocks:
            if b['type'] == 0:  # text
                for line in b['lines']:
                    line_text = ''.join(span['text'] for span in line['spans']).strip()
                    if line_text:
                        lb = [round(line['bbox'][0], 1), round(line['bbox'][1], 1),
                              round(line['bbox'][2], 1), round(line['bbox'][3], 1)]
                        text_blocks.append((lb, line_text))
        page_text_blocks[pno] = text_blocks

    doc.close()

    enriched = 0
    for kid in kids:
        if kid.get("content", "").strip():
            continue

        p = kid.get("page number", 0)
        bbox = kid.get("bounding box", None)
        if not bbox or len(bbox) < 4 or p not in page_text_blocks:
            continue

        bx0, by0, bx1, by1 = bbox
        # Docling bbox в BOTTOMLEFT (y растёт вверх). PyMuPDF — SCREEN (y растёт вниз).
        # Конвертируем: screen_y0 = page_h - by1, screen_y1 = page_h - by0
        page_h = 842.0
        screen_y0 = page_h - max(by0, by1)  # верх
        screen_y1 = page_h - min(by0, by1)  # низ
        by0, by1 = screen_y0, screen_y1
        bbox_h = abs(by1 - by0)

        # Если bbox слишком мал (<20px) — берём текст всей страницы
        # (Docling часто даёт битые bbox для таблиц)
        if bbox_h < 20:
            all_text = " ".join(t for _, t in page_text_blocks[p])
            if all_text:
                kid["content"] = all_text
                enriched += 1
            continue

        matching = []
        for tb, ttext in page_text_blocks[p]:
            if min(by1, tb[3]) > max(by0, tb[1]):
                if min(bx1, tb[2]) > max(bx0, tb[0]):
                    matching.append((tb[1], ttext))

        if matching:
            matching.sort(key=lambda x: x[0])
            text = " ".join(t for _, t in matching).strip()
            if text:
                kid["content"] = text
                enriched += 1

    if enriched:
        print(f"  Enriched: {enriched} empty blocks filled",
              file=sys.stderr, flush=True)

    # --- Добавление колонтитулов, пропущенных Docling ---
    # Для ВСЕХ страниц проверяем, какие строки PyMuPDF не покрыты Docling
    import fitz as _fitz
    _doc = _fitz.open(pdf_path)
    added_footer = 0
    # Все страницы, которые есть в kids
    all_pages_in_doc = sorted(set(k.get('page number', 0) for k in kids))
    for pno in all_pages_in_doc:
        if pno < 1 or pno > len(_doc):
            continue
        page = _doc[pno - 1]
        blocks = page.get_text('dict')['blocks']
        
        # Весь текст Docling на этой странице
        page_doc_text = ' '.join(
            k.get('content', '') for k in kids
            if k.get('page number') == pno and k.get('content', '').strip()
        )
        page_doc_norm = __import__('re').sub(r'[\s\u00a0]+', ' ', page_doc_text).lower().strip()

        for b in blocks:
            if b['type'] != 0:  # text only
                continue
            for line in b['lines']:
                ttext = ''.join(span['text'] for span in line['spans']).strip()
                if not ttext or len(ttext) < 15:
                    continue
                t_norm = __import__('re').sub(r'[\s\u00a0]+', ' ', ttext).lower().strip()
                if t_norm in page_doc_norm:
                    continue
                # Строка есть в PDF, но не в Docling — добавляем
                tb = [round(line['bbox'][0], 1), round(line['bbox'][1], 1),
                      round(line['bbox'][2], 1), round(line['bbox'][3], 1)]
                kid = {
                    'type': 'paragraph',
                    'page number': pno,
                    'bounding box': tb,
                    'content': ttext,
                }
                kids.append(kid)
                added_footer += 1

    _doc.close()
    if added_footer:
        print(f"  Added {added_footer} missing lines (headers/footers)",
              file=sys.stderr, flush=True)

    # --- Добавление подписей к рисункам (Рис.), пропущенных Docling ---
    # Docling отфильтровывает короткий текст (Рис.X.X) рядом с изображениями.
    # Ищем строки вида "Рис." длиной 7-30 символов, отсутствующие в Docling.
    _doc2 = _fitz.open(pdf_path)
    added_captions = 0
    for pno in all_pages_in_doc:
        if pno < 1 or pno > len(_doc2):
            continue
        page = _doc2[pno - 1]
        blocks = page.get_text('dict')['blocks']
        
        page_doc_text = ' '.join(
            k.get('content', '') for k in kids
            if k.get('page number') == pno and k.get('content', '').strip()
        )
        page_doc_norm = __import__('re').sub(r'[\s\u00a0]+', ' ', page_doc_text).lower().strip()

        for b in blocks:
            if b['type'] != 0:
                continue
            for line in b['lines']:
                ttext = ''.join(span['text'] for span in line['spans']).strip()
                if not ttext:
                    continue
                # Только строки с "Рис." длиной от 7 до 30 символов
                if 'рис' not in ttext.lower() or len(ttext) < 7 or len(ttext) > 30:
                    continue
                t_norm = __import__('re').sub(r'[\s\u00a0]+', ' ', ttext).lower().strip()
                if t_norm in page_doc_norm:
                    continue
                tb = [round(line['bbox'][0], 1), round(line['bbox'][1], 1),
                      round(line['bbox'][2], 1), round(line['bbox'][3], 1)]
                kid = {
                    'type': 'paragraph',
                    'page number': pno,
                    'bounding box': tb,
                    'content': ttext,
                }
                kids.append(kid)
                added_captions += 1
    _doc2.close()
    if added_captions:
        print(f"  Added {added_captions} figure captions (Рис.)",
              file=sys.stderr, flush=True)

    # --- Дедупликация: удаляем параграфы, дублирующие содержимое таблиц ---
    # Docling часто возвращает одно и то же содержимое и как table.rows, и как
    # фрагментированные paragraph-блоки. Удаляем параграфы, слова которых
    # >70% перекрываются с содержимым таблиц на той же странице.
    deduped = 0
    pages = sorted(set(k.get('page number', 0) for k in kids))
    for pno in pages:
        page_kids = [k for k in kids if k.get('page number') == pno]
        # Собираем все слова из table.rows на этой странице
        import re as _re
        table_words = set()
        for k in page_kids:
            if k.get('type') == 'table':
                for r in k.get('rows', []):
                    for c in r.get('cells', []):
                        for kid in c.get('kids', []):
                            w = _re.findall(r'[а-яёa-z0-9]+', kid.get('content', '').lower())
                            table_words.update(w)
        if not table_words:
            continue
        # Помечаем параграфы на удаление, если их слова >70% в table_words
        to_remove = []
        for ki, k in enumerate(page_kids):
            if k.get('type') != 'paragraph':
                continue
            ptext = k.get('content', '')
            p_words = set(_re.findall(r'[а-яёa-z0-9]+', ptext.lower()))
            if not p_words:
                continue
            overlap = len(p_words & table_words)
            if overlap / len(p_words) > 0.7:
                # Проверка: не удаляем, если параграф короче 15 символов
                # (короткие строки могут быть номерами страниц, а не дублями)
                if len(ptext.strip()) > 15:
                    to_remove.append(ki)
        # Удаляем в обратном порядке, чтобы не сбить индексы
        global_indices = []
        for ki in to_remove:
            kid_ref = page_kids[ki]
            # Находим его индекс в общем списке kids
            for gi, gk in enumerate(kids):
                if gk is kid_ref:
                    global_indices.append(gi)
                    break
        for gi in sorted(global_indices, reverse=True):
            kids.pop(gi)
            deduped += 1

    if deduped:
        print(f"  Dedup: removed {deduped} paragraph blocks (duplicate of table rows)",
              file=sys.stderr, flush=True)

    # --- Заполняем table.content из rows, если content пустой ---
    filled_tables = 0
    for k in kids:
        if k.get('type') == 'table':
            if not k.get('content', '').strip() and k.get('rows'):
                parts = []
                for r in k['rows']:
                    row_parts = []
                    for c in r.get('cells', []):
                        ct = ' '.join(cell_kid.get('content', '') for cell_kid in c.get('kids', []) if cell_kid.get('content', '').strip())
                        if ct.strip():
                            row_parts.append(ct.strip())
                    if row_parts:
                        parts.append(' | '.join(row_parts))
                if parts:
                    k['content'] = ' '.join(parts)
                    filled_tables += 1

    if filled_tables:
        print(f"  Filled content for {filled_tables} tables from rows",
              file=sys.stderr, flush=True)

    raw["kids"] = kids
    return raw


def _docling_doc_to_raw(doc, pdf_path: str) -> Dict[str, Any]:
    """Конвертирует DoclingDocument в raw JSON (opendataloader-формат)."""
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
        "number of pages": len(doc.pages) if doc.pages else 1,
        "kids": kids,
    }


def convert_docling_to_standard(pdf_path: str, max_pages: Optional[int] = None) -> Dict[str, Any]:
    """Парсит PDF → стандартизированный JSON."""
    raw = docling_to_raw_json(pdf_path, max_pages)

    std = JsonStandardizer()
    standardized = std.transform(raw, Path(pdf_path).name)

    # Оценка качества через quality_metrics
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
