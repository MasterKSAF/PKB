"""
HTTP-клиент для Docling Serve.
Отправляет PDF в docling-serve и возвращает DoclingDocument.
"""
import logging
from pathlib import Path
from typing import Optional

import httpx
import fitz

from app.config import settings
from docling_core.types.doc import DoclingDocument

logger = logging.getLogger(__name__)


SERVE_URL = settings.docling_serve_url.rstrip("/")
TIMEOUT = settings.docling_serve_timeout


def _build_multipart_body(
    params: list[tuple[str, str]],
    pdf_path: str,
) -> tuple[bytes, str]:
    """Build multipart/form-data body manually.

    httpx 0.28.x has a bug mixing list-of-tuples data with dict files,
    so we encode the full multipart body ourselves.
    """
    boundary = "----DoclingFormBoundary7MA4YWxk"
    parts = []

    for name, value in params:
        parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{value}\r\n".encode()
        )

    file_name = Path(pdf_path).name
    with open(pdf_path, "rb") as f:
        file_bytes = f.read()
    parts.append(
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="files"; filename="{file_name}"\r\n'
        f"Content-Type: application/pdf\r\n\r\n".encode()
    )
    parts.append(file_bytes)
    parts.append(b"\r\n")

    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), boundary


def request_docling_document(
    pdf_path: str,
    max_pages: Optional[int] = None,
) -> tuple[DoclingDocument, dict]:
    """Отправляет PDF в docling-serve, возвращает (DoclingDocument, raw_response)."""
    import time
    t_start = time.time()

    url = f"{SERVE_URL}/v1/convert/file"

    params: list[tuple[str, str]] = [
        ("to_formats", "json"),
        ("do_ocr", str(settings.docling_do_ocr).lower()),
        ("do_table_structure", str(settings.docling_table_structure).lower()),
        ("table_mode", "accurate"),
        ("do_formula_enrichment", str(settings.docling_formula_enrichment).lower()),
        ("include_images", "true"),
    ]
    # Always send page_range — docling-serve defaults to <50 pages if omitted
    try:
        pdf_doc = fitz.open(pdf_path)
        total_pages = pdf_doc.page_count
        pdf_doc.close()
    except Exception:
        total_pages = 9999
    page_end = total_pages if max_pages is None else min(max_pages, total_pages)
    params.append(("page_range", "1"))
    params.append(("page_range", str(page_end)))

    t_build = time.time()
    body, boundary = _build_multipart_body(params, pdf_path)
    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    t_http = time.time()
    logger.debug("TIMING request_docling_document: build_body=%.3fs, pdf=%s, size=%d",
                 t_http - t_build, pdf_path, len(body))

    with httpx.Client(timeout=TIMEOUT) as client:
        response = client.post(url, content=body, headers=headers)
        response.raise_for_status()
        raw = response.json()
    t_response = time.time()
    logger.debug("TIMING request_docling_document: http_post=%.3fs",
                 t_response - t_http)

    if raw.get("status") == "failure":
        raise RuntimeError(
            f"docling-serve failed: {raw.get('errors', 'unknown error')}"
        )

    doc_data = raw.get("document", {})
    json_content = doc_data.get("json_content")
    if not json_content:
        raise RuntimeError("docling-serve returned no json_content")

    doc = DoclingDocument.model_validate(json_content)
    t_end = time.time()
    logger.debug("TIMING request_docling_document: validate=%.3fs, total=%.3fs",
                 t_end - t_response, t_end - t_start)
    return doc, raw
