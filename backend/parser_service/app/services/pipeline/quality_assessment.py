"""
Оценка качества извлечения документа — можно ли доверять тексту или нужен OCR.
Запускается после стандартизации, анализирует финальный JSON.
"""
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

COVERAGE_GOOD_THRESHOLD = 0.70
COVERAGE_BAD_THRESHOLD = 0.30
EMPTY_BLOCK_BAD_THRESHOLD = 0.90
MIN_CHARS_PER_BLOCK = 3.0


def assess_document_quality(
    final_json: Dict[str, Any],
    quality_code: str | None = None,
    total_pages: int | None = None,
) -> Dict[str, Any]:
    """
    Анализирует стандартизированный JSON и возвращает quality-секцию с вердиктом.

    Returns:
        Словарь с полями:
          - verdict: "good" | "partial" | "needs_ocr"
          - needs_ocr: bool
          - confidence: float (0..1)
          - page_coverage_ratio: float
          - total_blocks: int
          - total_chars: int
          - empty_blocks: int
          - block_types: dict[str, int]
          - text_layer_quality: str | None
          - pages_scanned: int
          - pages_with_content: int
    """
    if not isinstance(final_json, dict):
        final_json = {}

    # ── Извлекаем document и quality с учётом формата ────────────────────
    # Приоритет: 1) верхний уровень, 2) content.document (docling-формат)
    doc = final_json.get("document") or final_json.get("content", {}).get("document") or {}

    blocks = doc.get("block", []) if isinstance(doc, dict) else []
    pages = doc.get("pages", []) if isinstance(doc, dict) else []

    _total_pages = total_pages or len(pages) or 1

    # ── Per-page coverage ──────────────────────────────────────────────
    pages_seen: set[int] = set()
    for b in blocks:
        p = b.get("page number", b.get("page", 1))
        if isinstance(p, (int, float)):
            pages_seen.add(int(p))

    pages_with_content = len(pages_seen)
    # Fallback: если blocks не дали страниц, пробуем per_page из content.quality
    if pages_with_content == 0 and _total_pages > 0:
        per_page_data = final_json.get("content", {}).get("quality", {}).get("per_page", [])
        pages_with_content = sum(1 for pp in per_page_data if pp.get("status") in ("ok", "low_confidence"))
    page_coverage_ratio = pages_with_content / max(_total_pages, 1)

    # ── Block-level metrics ────────────────────────────────────────────
    total_blocks = len(blocks)
    total_chars = 0
    empty_blocks = 0
    block_types: dict[str, int] = {}

    for b in blocks:
        bt = b.get("type", "unknown")
        block_types[bt] = block_types.get(bt, 0) + 1

        content = b.get("content") or ""
        if isinstance(content, str):
            n = len(content.strip())
            total_chars += n
            if n == 0:
                empty_blocks += 1

    mean_chars_per_block = total_chars / max(total_blocks, 1)
    empty_blocks_ratio = empty_blocks / max(total_blocks, 1)

    # ── Verdict ────────────────────────────────────────────────────────
    confidence = 0.0
    verdict = "needs_ocr"
    needs_ocr = True
    reasons: list[str] = []

    if total_blocks == 0:
        reasons.append("no blocks extracted")
        confidence = 0.0
        needs_ocr = True
        verdict = "needs_ocr"
    elif quality_code == "GOOD" and page_coverage_ratio >= COVERAGE_GOOD_THRESHOLD:
        confidence = min(0.70 + 0.30 * page_coverage_ratio, 1.0)
        needs_ocr = False
        verdict = "good"
        reasons.append("good")
    elif quality_code == "BAD":
        confidence = max(0.1, page_coverage_ratio * 0.3)
        needs_ocr = True
        verdict = "needs_ocr"
        reasons.append("bad text layer")
    elif page_coverage_ratio < COVERAGE_BAD_THRESHOLD:
        confidence = max(0.1, page_coverage_ratio * 0.3)
        needs_ocr = True
        verdict = "needs_ocr"
        reasons.append("low page coverage")
    elif empty_blocks_ratio >= EMPTY_BLOCK_BAD_THRESHOLD:
        confidence = max(0.1, 0.5 * (1.0 - empty_blocks_ratio))
        needs_ocr = True
        verdict = "needs_ocr"
        reasons.append("mostly empty blocks")
    elif quality_code == "SUSPECT" or (page_coverage_ratio < COVERAGE_GOOD_THRESHOLD):
        confidence = 0.3 + 0.4 * page_coverage_ratio
        needs_ocr = True
        verdict = "partial"
        reasons.append("partial")
    else:
        confidence = max(0.1, mean_chars_per_block / 50.0)
        needs_ocr = confidence < 0.5
        verdict = "needs_ocr" if needs_ocr else "partial"
        reasons.append("low text density" if needs_ocr else "partial")

    confidence = max(0.0, min(1.0, round(confidence, 2)))

    # ── Per-page breakdown ─────────────────────────────────────────────
    per_page: list[Dict[str, Any]] = []
    for p in range(1, _total_pages + 1):
        page_blocks = [b for b in blocks if b.get("page", 1) == p]
        status = "ok" if page_blocks else "empty"
        per_page.append({
            "page": p,
            "status": status,
            "blocks": len(page_blocks),
        })

    return {
        "verdict": verdict,
        "needs_ocr": needs_ocr,
        "confidence": confidence,
        "text_layer_quality": quality_code or "UNKNOWN",
        "page_coverage_ratio": round(page_coverage_ratio, 3),
        "total_blocks": total_blocks,
        "total_chars": total_chars,
        "empty_blocks": empty_blocks,
        "mean_chars_per_block": round(mean_chars_per_block, 1),
        "empty_blocks_ratio": round(empty_blocks_ratio, 3),
        "block_types": block_types,
        "pages_scanned": _total_pages,
        "pages_with_content": pages_with_content,
        "per_page": per_page,
        "pages_failed": _total_pages - pages_with_content,
        "notifications": [{"category": "quality", "message": f"verdict: {verdict}"}],
        "reasons": reasons,
    }
