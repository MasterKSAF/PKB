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

# ============================================================
# Новый MD-конвейер: DocumentConverter -> enrich(DoclingDocument) -> export_to_markdown -> md_to_json
# ============================================================


def _save_docling_pictures(doc, images_dir: str) -> Dict[Tuple[int, int], str]:
    """
    Сохраняет изображения из DoclingDocument в images_dir.
    Имена файлов: page_{page_no}_{seq}.png

    Returns:
        {(page_no, seq): filename} — карта для привязки к JSON-блокам.
    """
    import os
    import base64
    import io as _io
    from PIL import Image

    os.makedirs(images_dir, exist_ok=True)
    saved = {}  # (page_no, seq) -> filename
    counter_per_page = {}  # page_no -> int

    for picture in doc.pictures:
        page_no = picture.prov[0].page_no if picture.prov else 1
        img_ref = getattr(picture, 'image', None)
        if img_ref is None:
            continue

        # Пробуем получить PIL Image разными способами
        pil_img = None
        if isinstance(img_ref, Image.Image):
            pil_img = img_ref
        elif hasattr(img_ref, 'pil_image'):
            try:
                val = img_ref.pil_image
                if isinstance(val, Image.Image):
                    pil_img = val
            except Exception:
                pass
        if pil_img is None:
            continue

        counter_per_page.setdefault(page_no, 0)
        counter_per_page[page_no] += 1
        seq = counter_per_page[page_no]
        fname = f"page_{page_no}_{seq}.png"
        fpath = os.path.join(images_dir, fname)
        try:
            pil_img.save(fpath, format='PNG')
            saved[(page_no, seq)] = fname
        except Exception as e:
            logger.warning("Failed to save picture page=%d seq=%d: %s", page_no, seq, e)

    if saved:
        print(f"  Saved {len(saved)} pictures to {images_dir}",
              file=sys.stderr, flush=True)
    return saved


def _update_image_keys(json_result: dict, images_dir: str) -> None:
    """
    Проставляет image_key в JSON-блоках типа 'image', указывая на
    сохранённые файлы изображений. Путь относительный от temp_dir
    (images_dir = temp_dir/images/).
    """
    import os
    blocks = json_result.get('content', {}).get('document', {}).get('block', [])
    counter_per_page = {}
    updated = 0
    for block in blocks:
        if block.get('type') != 'image':
            continue
        pno = block.get('page number', 1)
        counter_per_page.setdefault(pno, 0)
        counter_per_page[pno] += 1
        seq = counter_per_page[pno]
        fname = f"page_{pno}_{seq}.png"
        rel_path = os.path.join('images', fname)
        fpath = os.path.join(images_dir, fname)
        if os.path.exists(fpath):
            block['image_key'] = rel_path
            updated += 1
    if updated:
        print(f"  Updated {updated} image blocks with image_key",
              file=sys.stderr, flush=True)




def enrich_docling_document(doc, pdf_path: str):
    """
    Обогащает DoclingDocument пропущенными элементами (колонтитулы, подписи Рис.).
    Использует PyMuPDF для поиска строк, отсутствующих в Docling, и добавляет их
    через doc.add_text() с корректным ProvenanceItem.
    Поиск отсутствующих строк — по координатам (bbox), а не по тексту.

    Returns:
        (doc, bbox_map) где bbox_map = {(page_no, norm_text): [l, t, r, b], ...}
    """
    import fitz
    import re as _re
    from collections import defaultdict
    from docling_core.types.doc import DocItemLabel, ProvenanceItem, BoundingBox, CoordOrigin

    pdf = fitz.open(pdf_path)
    added_count = 0

    # Карта bbox: (page_no, norm_text) -> [l, t, r, b]
    bbox_map = {}

    # Собираем полный текст элементов Docling по страницам
    doc_fulltext_by_page = {}  # pno -> 'norm_text1 norm_text2 ...'

    # Собираем полный текст + bbox элементов Docling для карты bbox
    for item, level in doc.iterate_items():
        prov = getattr(item, 'prov', None)
        if isinstance(prov, list):
            prov = prov[0] if prov else None
        if prov is None:
            continue
        pno = prov.page_no

        # Собираем полный текст элемента (включая ячейки таблиц)
        texts = []
        text = getattr(item, 'text', '') or ''
        if text.strip():
            texts.append(text)
        if hasattr(item, 'data') and item.data is not None:
            for cell in item.data.table_cells:
                if hasattr(cell, 'text') and cell.text:
                    texts.append(cell.text)
        full_text = ' '.join(texts) if texts else ''
        norm_text = _re.sub(r'[\s\u00a0]+', ' ', full_text).strip().lower()
        if norm_text:
            doc_fulltext_by_page[pno] = doc_fulltext_by_page.get(pno, ' ') + norm_text

        # Сохраняем bbox для карты bbox_map
        label = str(getattr(item, 'label', ''))
        page_h = pdf[pno - 1].rect.height if pno <= len(pdf) else 842.0
        l = round(prov.bbox.l, 1)
        r = round(prov.bbox.r, 1)
        t_val = page_h - round(prov.bbox.t, 1)
        b_val = page_h - round(prov.bbox.b, 1)
        bbox_tl = [l, min(t_val, b_val), r, max(t_val, b_val)]

        if label in ('table',):
            bbox_map[('__table__', pno)] = bbox_tl
        elif text.strip():
            t_norm = _re.sub(r'[\s\u00a0]+', ' ', text).strip().lower()
            bbox_map[(t_norm, pno)] = bbox_tl

    # Обрабатываем только страницы, присутствующие в DoclingDocument
    for pno in sorted(doc.pages.keys()):
        page = pdf[pno - 1]
        page_h = page.rect.height
        blocks = page.get_text('dict')['blocks']

        page_doc_text = doc_fulltext_by_page.get(pno, '')

        for b in blocks:
            if b['type'] != 0:  # text only
                continue
            for line in b['lines']:
                ttext = ''.join(span['text'] for span in line['spans']).strip()
                if not ttext or len(ttext) < 3:
                    continue

                bx0, by0, bx1, by1 = line['bbox']

                t_norm = _re.sub(r'[\s\u00a0]+', ' ', ttext).lower().strip()

                # Проверка: текст уже есть в Docling (как подстрока полного текста страницы)
                if page_doc_text and t_norm in page_doc_text:
                    continue

                # Минимальные фильтры: только номера строк и пустые
                if _re.match(r'^\.?\d+\s*$', ttext.strip()):
                    continue

                is_caption = 'рис' in ttext.lower() and len(ttext) <= 80
                is_header = by1 < page_h * 0.15
                is_footer = by0 > page_h * 0.85

                if is_caption:
                    label = DocItemLabel.CAPTION
                elif is_header:
                    label = DocItemLabel.PAGE_HEADER
                elif is_footer:
                    label = DocItemLabel.PAGE_FOOTER
                else:
                    label = DocItemLabel.PARAGRAPH

                prov = ProvenanceItem(
                    page_no=pno,
                    bbox=BoundingBox(
                        l=round(bx0, 1), t=round(by0, 1),
                        r=round(bx1, 1), b=round(by1, 1),
                        coord_origin=CoordOrigin.TOPLEFT,
                    ),
                    charspan=(0, len(ttext)),
                )

                doc.add_text(label=label, text=ttext, prov=prov)
                added_count += 1

                # Сохраняем bbox для enrich-элемента
                bbox_key = (t_norm, pno)
                if bbox_key not in bbox_map:
                    bbox_map[bbox_key] = [round(bx0, 1), round(by0, 1),
                                          round(bx1, 1), round(by1, 1)]

    pdf.close()

    if added_count:
        print(f"  Enrich (DoclingDocument): added {added_count} missing items",
              file=sys.stderr, flush=True)
    return doc, bbox_map


def _create_converter():
    """Создаёт DocumentConverter с фиксированными pipeline_options."""
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption

    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = False
    pipeline_options.do_table_structure = True
    pipeline_options.table_structure_options.do_cell_matching = True
    pipeline_options.accelerator_options.num_threads = 4
    pipeline_options.layout_batch_size = 2
    pipeline_options.table_batch_size = 2
    pipeline_options.generate_picture_images = True
    pipeline_options.generate_parsed_pages = False

    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options,
            )
        }
    )


def convert_via_docling_md(pdf_path: str, max_pages: Optional[int] = None,
                            page_start: int = 1,
                            images_dir: Optional[str] = None,
                            converter: Optional[Any] = None) -> Dict[str, Any]:
    """
    Новый конвейер:
      DocumentConverter → enrich(DoclingDocument) → export_to_markdown() → md_to_json()

    Параметры (совместимы со старым _try_pipeline):
        pdf_path: путь к PDF
        max_pages: последняя страница (включительно, None = все)
        page_start: начальная страница
        converter: переиспользуемый DocumentConverter (если None — создаётся новый)

    Returns:
        JSON в формате opendataloader
    """
    from docling_core.types.doc.base import ImageRefMode
    from md_to_json import md_to_document_json

    file_name = Path(pdf_path).name
    file_bytes = Path(pdf_path).read_bytes()
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    # Используем переданный конвертер или создаём новый
    if converter is None:
        converter = _create_converter()

    # Определяем диапазон страниц
    page_end = max_pages if max_pages is not None else None

    # Обрабатываем батчами по 5 страниц (как _try_pipeline), чтобы избежать std::bad_alloc
    from docling_core.types.doc import DoclingDocument
    doc = DoclingDocument(name=Path(pdf_path).stem)
    batch_size = 5
    page_limit = page_end or 9999

    for batch_start in range(page_start, page_limit + 1, batch_size):
        batch_end = min(batch_start + batch_size - 1, page_limit)
        try:
            batch_result = converter.convert(
                pdf_path, raises_on_error=False,
                page_range=(batch_start, batch_end),
            )
            if batch_result and batch_result.document and batch_result.document.pages:
                _merge_pages(doc, batch_result.document)
        except Exception as e:
            print(f"  Batch {batch_start}-{batch_end} failed: {e}",
                  file=sys.stderr, flush=True)
            continue

    if not doc.pages:
        raise RuntimeError("DocumentConverter failed on all pages")

    print(f"  Docling OK: {len(doc.pages)} pages processed",
          file=sys.stderr, flush=True)

    # ---- Сохраняем изображения, если указана папка ----
    if images_dir:
        _save_docling_pictures(doc, images_dir)

    # Enrich на уровне DoclingDocument (возвращает карту bbox)
    doc, bbox_map = enrich_docling_document(doc, pdf_path)

    # Export каждой страницы отдельно (чтобы избежать склейки страниц в MD)
    import re as _re
    page_mds = []
    for pno in sorted(doc.pages.keys()):
        md_text = doc.export_to_markdown(
            page_no=pno,
            compact_tables=True,
            image_mode=ImageRefMode.REFERENCED,
            traverse_pictures=True,
        )
        if md_text and md_text.strip():
            page_mds.append((pno, md_text.strip()))

    if not page_mds:
        raise RuntimeError("No markdown generated")

    json_result = md_to_document_json(page_mds, file_name)

    # ---- Проставляем image_key из сохранённых картинок ----
    if images_dir:
        _update_image_keys(json_result, images_dir)

    # Проставляем bbox из карты, собранной во время enrich
    def _match_bbox(pno: int, text: str) -> Optional[list]:
        """Ищет bbox для текста в bbox_map. Возвращает [x0,y0,x1,y1] или None."""
        if not text.strip():
            return None
        norm = _re.sub(r'[\s\u00a0]+', ' ', text).strip().lower()
        norm_clean = norm.rstrip('.')
        for candidate in [norm, norm_clean, norm_clean + '.']:
            key = (candidate, pno)
            if key in bbox_map:
                return bbox_map[key]
        for (map_text, map_page), map_bbox in bbox_map.items():
            if map_page == pno and map_text != '__table__':
                if len(norm) > 10 and norm in map_text:
                    return map_bbox
                if len(map_text) > 10 and map_text in norm:
                    return map_bbox
        return None

    def _merge_bbox(bboxes: list) -> list:
        """Объединяет несколько bbox в один (по минимальным/максимальным координатам)."""
        if not bboxes:
            return [0, 0, 0, 0]
        x0 = min(b[0] for b in bboxes)
        y0 = min(b[1] for b in bboxes)
        x1 = max(b[2] for b in bboxes)
        y1 = max(b[3] for b in bboxes)
        return [x0, y0, x1, y1]

    bbox_matched = 0
    for block in json_result.get('content', {}).get('document', {}).get('block', []):
        pno = block.get('page number', 1)
        btype = block.get('type', '')
        text = block.get('content', '') or ''

        if btype == 'table':
            key = ('__table__', pno)
            if key in bbox_map:
                block['bounding box'] = bbox_map[key]
                bbox_matched += 1
            continue

        if btype == 'list':
            # Для списка — ищем bbox для каждого элемента и объединяем
            items = block.get('items', [])
            if items:
                item_bboxes = []
                for item in items:
                    item_text = item.get('content', '') if isinstance(item, dict) else str(item)
                    b = _match_bbox(pno, item_text)
                    if b:
                        item_bboxes.append(b)
                        # Сохраняем индивидуальный bbox в элемент
                        if isinstance(item, dict):
                            item['bounding box'] = b
                if item_bboxes:
                    block['bounding box'] = _merge_bbox(item_bboxes)
                    bbox_matched += 1
            continue

        if not text.strip():
            continue

        matched = _match_bbox(pno, text)
        if matched:
            block['bounding box'] = matched
            bbox_matched += 1

    if bbox_matched:
        print(f"  Bbox: restored {bbox_matched} block positions",
              file=sys.stderr, flush=True)

    # Проставляем размеры страниц из DoclingDocument
    pages_info = []
    for pno in sorted(doc.pages.keys()):
        page_obj = doc.pages[pno]
        pages_info.append({
            'page': pno,
            'width': round(page_obj.size.width, 1),
            'height': round(page_obj.size.height, 1),
        })
    json_result['content']['document']['pages'] = pages_info

    # Заполняем per_page качество
    per_page = []
    for pno in sorted(doc.pages.keys()):
        per_page.append({
            'page': pno,
            'confidence': 0.75,
            'status': 'ok',
        })
    json_result['content']['quality']['per_page'] = per_page
    json_result['content']['quality']['pages_processed'] = len(per_page)

    # Добавляем хеш
    if 'source' in json_result.get('content', {}).get('document', {}):
        json_result['content']['document']['source']['file_hash_sha256'] = file_hash

    print(f"  Converted via MD pipeline: pages={len(doc.pages)}, page_mds={len(page_mds)}, blocks={len(json_result['content']['document']['block'])}",
          file=sys.stderr, flush=True)

    return json_result


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
            target.add_picture(prov=prov, image=getattr(item, 'image', None))
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



def _split_md_by_pages(md_text: str, default_page: int = 1) -> List[Tuple[int, str]]:
    """
    Разбивает многостраничный Markdown от Docling на страницы.
    Docling разделяет страницы маркером `--- page X ---`.

    Args:
        md_text: Markdown-текст
        default_page: страница по умолчанию, если разделители не найдены
    """
    import re
    # Паттерн: --- page X --- или ---page X---
    parts = re.split(r'\n---{3,}\s*page\s+(\d+)\s*---{3,}\s*\n', md_text)
    if len(parts) < 2:
        # Нет разделителей — весь текст одна страница
        return [(default_page, md_text)]

    result = []
    # Первый элемент — текст до первой страницы (обычно пустой или преамбула)
    preamble = parts[0].strip()
    for i in range(1, len(parts), 2):
        page_num = int(parts[i])
        content = parts[i + 1] if i + 1 < len(parts) else ''
        if preamble and i == 1:
            content = preamble + '\n\n' + content
        result.append((page_num, content.strip()))

    return result if result else [(1, md_text.strip())]



# ============================================================
# 3. Старый конвейер (JSON, сохранён для обратной совместимости)
# ============================================================


def convert_docling_to_standard(pdf_path: str, max_pages: Optional[int] = None) -> Dict[str, Any]:
    """Парсит PDF → стандартизированный JSON (старый конвейер)."""
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
