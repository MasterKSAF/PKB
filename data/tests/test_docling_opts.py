"""
Test docling-serve options: flat form fields vs JSON options.

Verifies that flat form fields (matching OpenAPI schema) are applied
by measuring processing speed: FAST mode + no OCR + no cell matching
should complete ~2 sec/page.
"""
import json, sys, time
from pathlib import Path
import requests

DOCLING_URL = "http://localhost:5001/v1/convert/file"
PDF = Path("data/pdf_check/2-020101-174-3.pdf")
PAGES = (20, 22)  # 3 pages with complex tables

if not PDF.exists():
    print(f"[FAIL] PDF not found: {PDF}")
    sys.exit(1)

def test_flat_fields() -> float:
    """Send flat form fields (OpenAPI schema), return elapsed seconds."""
    with open(PDF, "rb") as f:
        files = {"files": (PDF.name, f, "application/pdf")}
        data = {
            "to_formats": "json",
            "do_ocr": "false",
            "do_table_structure": "true",
            "table_mode": "fast",
            "table_cell_matching": "false",
            "do_formula_enrichment": "false",
            "include_images": "true",
            "page_range": str(PAGES[0]),
            # second page_range value sent via files list
        }
        # page_range needs two values; requests sends as list
        data["page_range"] = [str(PAGES[0]), str(PAGES[1])]

        t0 = time.time()
        r = requests.post(DOCLING_URL, files=files, data=data, timeout=120)
        elapsed = time.time() - t0

    assert r.status_code == 200, f"Flat fields: HTTP {r.status_code} {r.text[:200]}"
    body = r.json()
    assert body.get("document", {}).get("json_content"), f"Flat fields: no json_content"
    return elapsed


def verify_fast_timing(elapsed: float, pages: int = PAGES[1] - PAGES[0] + 1):
    """Check that speed is ~2 sec/page (FAST mode), not ~50 sec/page."""
    print(f"  Pages: {pages}, time: {elapsed:.1f}s, speed: {elapsed/pages:.1f}s/page")
    max_expected = pages * 8  # 8 sec/page as safety margin
    assert elapsed < max_expected, (
        f"Too slow: {elapsed:.1f}s for {pages} pages "
        f"(expected <{max_expected}s for FAST mode). "
        f"Options may not be applied!"
    )


if __name__ == "__main__":
    print(f"PDF: {PDF}")
    print(f"Pages: {PAGES[0]}-{PAGES[1]}")
    print()

    # --- Flat form fields ---
    print("=== Flat form fields (OpenAPI schema) ===")
    t_flat = test_flat_fields()
    print(f"  Time: {t_flat:.1f}s")
    verify_fast_timing(t_flat)
    print("  [PASS]")

    print()
    print("[PASS] All checks passed")
