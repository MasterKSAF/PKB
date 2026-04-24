"""MVP classifier + metadata extraction.

This is intentionally heuristic-based for MVP:
- identify doc_type mostly by file extension/content type
- detect language from sample text
- detect scan-ish PDFs by checking extracted text length
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz  # pymupdf

from neuroassistant.domain import ClassificationResult
from neuroassistant.utils import detect_language


@dataclass(frozen=True, slots=True)
class ClassifierConfig:
    pdf_text_min_chars: int = 50


def classify_file(
    path: Path,
    content_type: str | None,
    config: ClassifierConfig | None = None,
) -> ClassificationResult:
    cfg = config or ClassifierConfig()
    suffix = path.suffix.lower()

    if suffix in {".pdf"} or (content_type or "").lower() == "application/pdf":
        return _classify_pdf(path, cfg)

    if suffix in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}:
        return ClassificationResult(
            doc_type="scan",
            language="unknown",
            is_scan=True,
            page_count=1,
            scan_quality=None,
            scan_quality_reasons=[],
            needs_preprocessing=True,
        )

    if suffix in {".doc", ".docx"}:
        return ClassificationResult(
            doc_type="office",
            language="unknown",
            is_scan=False,
            page_count=None,
            needs_preprocessing=False,
        )

    if suffix in {".html", ".htm", ".xml"}:
        return ClassificationResult(
            doc_type="web",
            language="unknown",
            is_scan=False,
            page_count=None,
            needs_preprocessing=False,
        )

    return ClassificationResult(
        doc_type="other",
        language="unknown",
        is_scan=None,
        page_count=None,
        needs_preprocessing=False,
    )


def _classify_pdf(path: Path, cfg: ClassifierConfig) -> ClassificationResult:
    doc = fitz.open(str(path))
    try:
        page_count = doc.page_count
        sample_parts: list[str] = []
        for i in range(min(3, page_count)):
            page = doc.load_page(i)
            txt = page.get_text("text") or ""
            if txt:
                sample_parts.append(txt[:2000])

        sample = "\n".join(sample_parts)
        lang = detect_language(sample)
        is_scan = len(sample.strip()) < cfg.pdf_text_min_chars
        needs_preproc = is_scan

        scan_quality = None
        reasons: list[str] = []
        if is_scan:
            scan_quality = "unknown"
            reasons.append("low_text_layer")

        return ClassificationResult(
            doc_type="pdf",
            language=lang,
            is_scan=is_scan,
            page_count=page_count,
            scan_quality=scan_quality,
            scan_quality_reasons=reasons,
            needs_preprocessing=needs_preproc,
        )
    finally:
        doc.close()

