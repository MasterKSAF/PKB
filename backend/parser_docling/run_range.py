"""
Запуск Docling парсинга с поддержкой диапазона страниц.
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
from docling.datamodel.base_models import InputFormat
from docling.datamodel.document import InputDocument
from docling.backend.docling_parse_v2_backend import DoclingParseV2DocumentBackend
from docling.datamodel.settings import DocumentLimits

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'shared'))
from docling_mapper import _try_pipeline, _docling_doc_to_raw, _enrich_empty_blocks


def main():
    parser = argparse.ArgumentParser(description='Run Docling parse with page range')
    parser.add_argument('--start', type=int, default=1, help='Start page')
    parser.add_argument('--end', type=int, default=None, help='End page')
    parser.add_argument('-o', '--output', default=None, help='Output JSON path')
    parser.add_argument('--quiet', action='store_true', help='Suppress progress output')
    args = parser.parse_args()

    if args.quiet:
        import docling_mapper as dm
        dm.print = lambda *a, **kw: None

    pdf_path = 'pdf/2-020101-174-1.pdf'

    limits = DocumentLimits(page_range=(1, 1))
    in_doc = InputDocument(
        path_or_stream=Path(pdf_path), format=InputFormat.PDF,
        backend=DoclingParseV2DocumentBackend, limits=limits,
    )
    total = in_doc.page_count
    start_page = args.start
    end_page = args.end or total

    if not args.quiet:
        print(f"Parsing pages {start_page}–{end_page} (of {total})", flush=True)

    out_path = args.output or f'output_{start_page}-{end_page}.json'

    t0 = time.time()
    doc = _try_pipeline(pdf_path, max_pages=end_page, page_start=start_page)
    elapsed = time.time() - t0

    if doc is None:
        print("Pipeline failed", flush=True)
        sys.exit(1)

    if not args.quiet:
        print(f"  Pipeline OK", flush=True)

    raw = _docling_doc_to_raw(doc, pdf_path)
    raw["file name"] = Path(pdf_path).name
    raw["file_hash_sha256"] = ""

    enriched = _enrich_empty_blocks(pdf_path, raw)

    print(f"\n{'='*50}", flush=True)
    print(f"Time: {elapsed:.1f}s ({elapsed/60:.1f} min)", flush=True)

    blocks = enriched.get("kids", [])
    print(f"Blocks: {len(blocks)}", flush=True)
    types = {}
    for b in blocks:
        t = b.get('type', 'unknown')
        types[t] = types.get(t, 0) + 1
    for t, c in sorted(types.items()):
        print(f"  {t}: {c}", flush=True)

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to {out_path}", flush=True)


if __name__ == '__main__':
    main()
