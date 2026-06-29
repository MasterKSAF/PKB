import re
from typing import Any

from app.services.normalizer import era_from_year, infer_era, infer_source_type

_GOST_CODE_RE = re.compile(
    r"(?:ГОСТ|GOST)\s*(\d[\d.]*(?:-\d{2,4})?)",
    re.IGNORECASE,
)
_CIRCULAR_RE = re.compile(
    r"ЦИРКУЛЯРНОЕ\s+ПИСЬМО\s*[№N#]\s*(\S+)",
    re.IGNORECASE,
)
_YEAR_IN_CODE_RE = re.compile(r"-(\d{2,4})\s*$")
_MKS_OKS_RE = re.compile(
    r"(?:МКС|ОКС|ICS)\s*[:\s]*?(\d{2}(?:\.\d{3}(?:\.\d{2})?)?(?:-\d{2})?)",
    re.IGNORECASE,
)
_OKSTU_RE = re.compile(
    r"(?:ОКСТУ|ОК\.СТУ)\s*[:\s]*?(\d{2}(?:\.\d{2}){1,2})",
    re.IGNORECASE,
)
_UDK_RE = re.compile(
    r"(?:УДК|UDC)\s*[:\s]*?([\d.:]+)",
    re.IGNORECASE,
)
_CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")


def _iter_text_blocks(raw_json: dict[str, Any]) -> list[str]:
    texts: list[str] = []
    doc = raw_json.get("document") or {}
    source = doc.get("source") or {}
    for block in doc.get("block") or []:
        content = block.get("content")
        if isinstance(content, str) and content.strip():
            texts.append(content.strip())
        elif block.get("type") == "text_block":
            for part in block.get("block") or []:
                part_text = part.get("content")
                if isinstance(part_text, str) and part_text.strip():
                    texts.append(part_text.strip())

    title_val = source.get("title")
    if isinstance(title_val, str) and title_val.strip():
        texts.append(title_val.strip())
    file_name = source.get("file_name")
    if isinstance(file_name, str) and file_name.strip():
        texts.append(file_name.strip())
    author = source.get("author")
    if isinstance(author, str) and author.strip():
        texts.append(author.strip())
    return texts


def _find_doc_code(texts: list[str]) -> str | None:
    for text in texts:
        match = _GOST_CODE_RE.search(text)
        if match:
            return match.group(1)
        match = _CIRCULAR_RE.search(text)
        if match:
            return match.group(1)
    return None


def _is_file_name(text: str) -> bool:
    lower = text.lower()
    return lower.endswith(".pdf") or lower.endswith(".docx") or lower.endswith(".doc")


def _find_title(texts: list[str], doc_code: str | None) -> str | None:
    candidates: list[str] = []
    for text in texts:
        if _is_file_name(text):
            continue
        if doc_code and doc_code.replace(" ", "") in text.replace(" ", ""):
            if len(text) < 40:
                continue
        if len(text) > 20 and not _GOST_CODE_RE.search(text):
            if "технические требования" in text.lower() or "." in text:
                return text
        if len(text) > 15:
            candidates.append(text)
    if candidates:
        return max(candidates, key=len)
    for text in texts:
        if not _is_file_name(text) and len(text) > 10:
            return text
    return texts[0] if texts else None


def _infer_document_type(doc_code: str | None, title: str) -> str:
    combined = f"{doc_code or ''} {title}".lower()
    if "чертеж" in combined or "черт." in combined:
        return "drawing"
    if "спецификац" in combined:
        return "specification"
    return "normative"


def _infer_year(doc_code: str | None, texts: list[str]) -> int | None:
    if doc_code:
        match = _YEAR_IN_CODE_RE.search(doc_code.replace(" ", ""))
        if match:
            year_part = match.group(1)
            if len(year_part) == 2:
                value = int(year_part)
                return 1900 + value if value >= 50 else 2000 + value
            return int(year_part)
    for text in texts:
        year_match = re.search(r"\b(19|20)\d{2}\b", text)
        if year_match:
            return int(year_match.group(0))
    return None


def _extract_code(pattern: re.Pattern[str], texts: list[str]) -> str | None:
    for text in texts:
        match = pattern.search(text)
        if match:
            return match.group(1)
    return None


def _infer_language(title: str) -> str:
    if _CYRILLIC_RE.search(title):
        return "ru"
    return "en"


def _infer_jurisdiction(source_type: str) -> str:
    if source_type in {"DNV", "ASTM", "ISO"}:
        return "INTL"
    return "RU"


def extract_preview_metadata(raw_json: dict[str, Any]) -> dict[str, Any]:
    texts = _iter_text_blocks(raw_json)
    doc = raw_json.get("document") or {}
    source = doc.get("source") or {}
    doc_code = _find_doc_code(texts)
    title = _find_title(texts, doc_code)
    year = _infer_year(doc_code, texts)
    issuing_body = source.get("author")
    if isinstance(issuing_body, str):
        issuing_body = issuing_body.strip() or None
    else:
        issuing_body = None

    source_type = infer_source_type(doc_code, title, source.get("title"), issuing_body)
    era = era_from_year(
        year,
        title,
        issuing_body,
        source.get("title"),
    )

    return {
        "doc_code": doc_code,
        "title": title,
        "mks_oks_code": _extract_code(_MKS_OKS_RE, texts),
        "okstu_code": _extract_code(_OKSTU_RE, texts),
        "udk_code": _extract_code(_UDK_RE, texts),
        "pkb_codes": [],
        "document_type": _infer_document_type(doc_code, title or ""),
        "year": year,
        "era": era,
        "validity_status": "active",
        "issuing_body": issuing_body,
        "jurisdiction": _infer_jurisdiction(source_type),
        "source_type": source_type,
        "language": _infer_language(title or ""),
    }
