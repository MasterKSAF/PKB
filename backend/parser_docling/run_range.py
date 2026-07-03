"""
Запуск Docling парсинга с поддержкой диапазона страниц.
Режимы:
  --mode json  (по умолчанию) — старый конвейер: Pipeline → enrich(JSON) → standardize → normalize
  --mode md    — новый конвейер: DocumentConverter → enrich(DoclingDocument) → export_to_markdown → md_to_json
"""
import os
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'

import warnings
warnings.filterwarnings('ignore')

# Monkey-patch huggingface_hub symlink for Windows
import huggingface_hub.file_download as hf_dl
_orig = hf_dl._create_symlink
def _patched(src, dst, new_blob=False):
    try: _orig(src, dst, new_blob)
    except OSError:
        import shutil
        abs_src = os.path.abspath(os.path.expanduser(src))
        abs_dst = os.path.abspath(os.path.expanduser(dst))
        if new_blob: shutil.move(abs_src, abs_dst, copy_function=shutil.copy2)
        else: shutil.copy2(abs_src, abs_dst)
hf_dl._create_symlink = _patched

import sys, json, time, argparse
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'shared'))


def run_json_mode(pdf_path: str, start_page: int, end_page: int, out_path: str, quiet: bool):
    """Старый конвейер: JSON."""
    from docling_mapper import _try_pipeline, _docling_doc_to_raw, _enrich_empty_blocks

    if not quiet:
        print(f"[JSON mode] Parsing pages {start_page}–{end_page}", flush=True)

    doc = _try_pipeline(pdf_path, max_pages=end_page, page_start=start_page)
    if doc is None:
        print("Pipeline failed", flush=True)
        sys.exit(1)

    if not quiet:
        print("  Pipeline OK", flush=True)

    raw = _docling_doc_to_raw(doc, pdf_path)
    raw["file name"] = Path(pdf_path).name
    raw["file_hash_sha256"] = ""

    enriched = _enrich_empty_blocks(pdf_path, raw)

    blocks = enriched.get("kids", [])
    if not quiet:
        types = {}
        for b in blocks:
            t = b.get('type', 'unknown')
            types[t] = types.get(t, 0) + 1
        print(f"  Blocks: {len(blocks)}", flush=True)
        for t, c in sorted(types.items()):
            print(f"    {t}: {c}", flush=True)

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)
    print(f"Saved to {out_path}", flush=True)


def run_md_mode(pdf_path: str, start_page: int, end_page: int, out_path: str, quiet: bool):
    """Новый конвейер: MD."""
    from docling_mapper import convert_via_docling_md

    if not quiet:
        print(f"[MD mode] Parsing pages {start_page}–{end_page}", flush=True)
    result = convert_via_docling_md(pdf_path=pdf_path, max_pages=end_page, page_start=start_page)

    blocks = result['content']['document']['block']
    if not quiet:
        types = {}
        for b in blocks:
            t = b.get('type', 'unknown')
            types[t] = types.get(t, 0) + 1
        print(f"  Blocks: {len(blocks)}", flush=True)
        for t, c in sorted(types.items()):
            print(f"    {t}: {c}", flush=True)

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"Saved to {out_path}", flush=True)


def main():
    parser = argparse.ArgumentParser(description='Run Docling parse with page range')
    parser.add_argument('--start', type=int, default=1, help='Start page')
    parser.add_argument('--end', type=int, default=None, help='End page')
    parser.add_argument('-o', '--output', default=None, help='Output JSON path')
    parser.add_argument('--quiet', action='store_true', help='Suppress progress output')
    parser.add_argument('--mode', choices=['json', 'md'], default='json',
                        help='Pipeline mode: json (старый) or md (новый MD)')
    args = parser.parse_args()

    pdf_path = 'pdf/2-020101-174-1.pdf'

    # Определяем кол-во страниц через быстрый проброс
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.document import InputDocument
    from docling.datamodel.settings import DocumentLimits


    # Определяем кол-во страниц через быстрый проброс
    limits = DocumentLimits(page_range=(1, 1))
    from docling.backend.docling_parse_backend import DoclingParseDocumentBackend
    in_doc = InputDocument(
        path_or_stream=Path(pdf_path), format=InputFormat.PDF,
        backend=DoclingParseDocumentBackend, limits=limits,
    )
    total = in_doc.page_count
    start_page = args.start
    end_page = args.end or total

    out_path = args.output or f'output_{start_page}-{end_page}_{args.mode}.json'

    t0 = time.time()

    if args.mode == 'json':
        run_json_mode(pdf_path, start_page, end_page, out_path, args.quiet)
    else:
        run_md_mode(pdf_path, start_page, end_page, out_path, args.quiet)

    elapsed = time.time() - t0
    print(f"\nTime: {elapsed:.1f}s ({elapsed/60:.1f} min)", flush=True)


if __name__ == '__main__':
    main()
