"""MVP preprocessing for scanned PDFs and images.

We keep this intentionally simple:
- render scanned PDF pages to images (PNG)
- apply basic grayscale + autocontrast + median filter

This is meant to reduce OCR risk; OCR itself is not part of this MVP.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz  # pymupdf
from PIL import Image
from PIL import ImageFilter
from PIL import ImageOps


@dataclass(frozen=True, slots=True)
class PreprocessMetrics:
    pages_rendered: int
    pages_preprocessed: int


def preprocess_pdf_to_images(
    pdf_path: Path,
    pages_dir: Path,
    preprocessed_dir: Path,
    dpi: int = 200,
) -> PreprocessMetrics:
    pages_dir.mkdir(parents=True, exist_ok=True)
    preprocessed_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_path))
    rendered = 0
    preprocessed = 0
    try:
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        for page_index in range(doc.page_count):
            page = doc.load_page(page_index)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            raw_path = pages_dir / f"page_{page_index + 1:04d}.png"
            pix.save(str(raw_path))
            rendered += 1

            img = Image.open(raw_path)
            out = _basic_preprocess_image(img)
            out_path = preprocessed_dir / raw_path.name
            out.save(out_path)
            preprocessed += 1

        return PreprocessMetrics(
            pages_rendered=rendered,
            pages_preprocessed=preprocessed,
        )
    finally:
        doc.close()


def preprocess_image(
    image_path: Path,
    preprocessed_path: Path,
) -> None:
    img = Image.open(image_path)
    out = _basic_preprocess_image(img)
    preprocessed_path.parent.mkdir(parents=True, exist_ok=True)
    out.save(preprocessed_path)


def _basic_preprocess_image(img: Image.Image) -> Image.Image:
    gray = ImageOps.grayscale(img)
    contrast = ImageOps.autocontrast(gray)
    denoised = contrast.filter(ImageFilter.MedianFilter(size=3))
    return denoised

