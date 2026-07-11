"""
Integration test: полный пайплайн на реальном PDF без Docling Serve.

Использует DocumentConverter + enrich_docling_document напрямую.
Проверяет что номера страниц (3, 5, 16-18, 23-26, 31-32, 35-38) не попадают в blocks.
"""

import re
import sys
from pathlib import Path

_PROJECT = Path(__file__).parent.parent.parent.parent.parent
_DOCLING_DIR = _PROJECT / "app" / "services" / "parsers" / "docling"
sys.path.insert(0, str(_DOCLING_DIR))

# Импортируем enrich + html_to_json без app.config
from docling_core.types.doc import DocItemLabel, ProvenanceItem, BoundingBox, CoordOrigin
from docling_core.types.doc.base import ImageRefMode
from html_to_json import html_to_document_json

PDF_PATH = _PROJECT / "pdf" / "2-020101-174-12.pdf"


def _enrich(doc, pdf_path: str):
    """Локальная копия enrich_docling_document (без зависимостей от app.config)."""
    import fitz
    import re as _re
    pdf = fitz.open(pdf_path)
    added_count = 0

    doc_fulltext_by_page = {}
    for item, level in doc.iterate_items():
        prov = getattr(item, 'prov', None)
        if isinstance(prov, list):
            prov = prov[0] if prov else None
        if prov is None:
            continue
        pno = prov.page_no
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

    for pno in sorted(doc.pages.keys()):
        page = pdf[pno - 1]
        page_h = page.rect.height
        blocks = page.get_text('dict', sort=True)['blocks']
        page_doc_text = doc_fulltext_by_page.get(pno, '')

        for b in blocks:
            if b['type'] != 0:
                continue
            for line in b['lines']:
                ttext = ''.join(span['text'] for span in line['spans']).strip()
                if not ttext or len(ttext) < 3:
                    continue
                bx0, by0, bx1, by1 = line['bbox']
                t_norm = _re.sub(r'[\s\u00a0]+', ' ', ttext).lower().strip()
                if page_doc_text and t_norm in page_doc_text:
                    continue
                # Фильтр номеров страниц (такой же как в docling_mapper.py)
                if _re.match(r'^[\d\s\-—\/]+$', ttext.strip()):
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
                    bbox=BoundingBox(l=round(bx0, 1), t=round(by0, 1),
                                     r=round(bx1, 1), b=round(by1, 1),
                                     coord_origin=CoordOrigin.TOPLEFT),
                    charspan=(0, len(ttext)),
                )
                doc.add_text(label=label, text=ttext, prov=prov)
                added_count += 1
    pdf.close()
    if added_count:
        print(f"  Enrich: added {added_count} items", file=sys.stderr, flush=True)
    return doc


def test_page_numbers_filtered_from_full_pipeline():
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling_core.types.doc import DoclingDocument

    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = False
    pipeline_options.do_table_structure = True
    pipeline_options.table_structure_options.do_cell_matching = True
    pipeline_options.accelerator_options.num_threads = 4
    pipeline_options.layout_batch_size = 2
    pipeline_options.table_batch_size = 2
    pipeline_options.generate_picture_images = True
    pipeline_options.generate_parsed_pages = False

    converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
    )

    result = converter.convert(str(PDF_PATH), raises_on_error=False)
    doc = result.document

    doc = _enrich(doc, str(PDF_PATH))

    page_htmls = []
    for pno in sorted(doc.pages.keys()):
        html = doc.export_to_html(page_no=pno, image_mode=ImageRefMode.REFERENCED)
        if html and html.strip():
            page_htmls.append((pno, html.strip()))

    assert page_htmls, "No HTML generated"

    json_result = html_to_document_json(page_htmls, PDF_PATH.name)
    blocks = json_result.get("content", {}).get("document", {}).get("block", [])
    assert blocks, "No blocks generated"

    page_like = re.compile(r"^[\d\s\-\—\/]+$")
    problems = [
        f"  page={b.get('page number')} type={b.get('type')} content={repr((b.get('content') or '').strip())}"
        for b in blocks
        if page_like.match((b.get("content") or "").strip())
    ]
    assert not problems, (
        f"\n{len(problems)} page-number-like blocks:\n" + "\n".join(problems)
        + f"\nTotal blocks: {len(blocks)}"
    )
    print(f"\n  OK: {len(blocks)} blocks, no page numbers.")


if __name__ == "__main__":
    assert PDF_PATH.exists(), f"PDF not found: {PDF_PATH}"
    test_page_numbers_filtered_from_full_pipeline()
    print("  PASS")
