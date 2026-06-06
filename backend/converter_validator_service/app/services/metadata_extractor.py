import re
from typing import Any

_GOST_CODE_RE = re.compile(
    r"(?:ГОСТ|GOST)\s*(\d[\d.]*(?:-\d{2,4})?)",
    re.IGNORECASE,
)
_YEAR_IN_CODE_RE = re.compile(r"-(\d{2,4})\s*$")
_REVISION_RE = re.compile(
    r"(?:изм\.|изменение|ред\.|revision)\s*№?\s*(\d+)",
    re.IGNORECASE,
)


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
    return texts


def _find_doc_code(texts: list[str]) -> str | None:
    for text in texts:
        match = _GOST_CODE_RE.search(text)
        if match:
            prefix = "ГОСТ" if "ГОСТ" in text.upper() else "GOST"
            return f"{prefix} {match.group(1)}"
    return None


def _is_file_name(text: str) -> bool:
    lower = text.lower()
    return lower.endswith(".pdf") or lower.endswith(".docx") or lower.endswith(".doc")


def _find_title(texts: list[str], doc_code: str | None) -> str:
    candidates: list[str] = []
    for text in texts:
        if _is_file_name(text):
            continue
        if doc_code and doc_code.replace(" ", "") in text.replace(" ", ""):
            if len(text) < 40:
                continue
        if len(text) > 20 and not _GOST_CODE_RE.fullmatch(text.strip()):
            if "технические требования" in text.lower() or "." in text:
                return text
        if len(text) > 15:
            candidates.append(text)
    if candidates:
        return max(candidates, key=len)
    for text in texts:
        if not _is_file_name(text) and len(text) > 10:
            return text
    return texts[0] if texts else "Без названия"


def _infer_document_type(doc_code: str | None, title: str) -> str:
    combined = f"{doc_code or ''} {title}".lower()
    if "чертеж" in combined or "черт." in combined:
        return "drawing"
    if "спецификац" in combined:
        return "specification"
    return "normative"


def _infer_year(doc_code: str | None, texts: list[str]) -> str:
    if doc_code:
        match = _YEAR_IN_CODE_RE.search(doc_code.replace(" ", ""))
        if match:
            year_part = match.group(1)
            if len(year_part) == 2:
                return f"19{year_part}" if int(year_part) >= 50 else f"20{year_part}"
            return year_part
    for text in texts:
        year_match = re.search(r"\b(19|20)\d{2}\b", text)
        if year_match:
            return year_match.group(0)
    return ""


def _infer_revision(texts: list[str]) -> str | None:
    for text in texts:
        match = _REVISION_RE.search(text)
        if match:
            return match.group(1)
    return None


def extract_preview_metadata(raw_json: dict[str, Any]) -> dict[str, str | None]:
    texts = _iter_text_blocks(raw_json)
    doc_code = _find_doc_code(texts) or ""
    title = _find_title(texts, doc_code or None)
    return {
        "doc_code": doc_code,
        "title": title,
        "document_type": _infer_document_type(doc_code or None, title),
        "year": _infer_year(doc_code or None, texts),
        "revision": _infer_revision(texts),
    }
