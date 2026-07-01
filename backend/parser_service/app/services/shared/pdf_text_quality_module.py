from __future__ import annotations

import argparse
import json
import re
import string
from dataclasses import asdict, dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Any


DEFAULT_PAGES_LIMIT = 5
SAMPLE_TEXT_LIMIT = 500
GOOD_THRESHOLD = 80
BAD_THRESHOLD = 50


class TextLayerQualityCode(IntEnum):
    """Stable suitability codes for a logical parser pipeline."""

    GOOD = 0
    SUSPECT = 1
    BAD = 2
    PDF_READ_ERROR = 3


STATUS_LABELS_RU = {
    TextLayerQualityCode.GOOD: "Хороший текстовый слой",
    TextLayerQualityCode.SUSPECT: "Подозрительный текстовый слой",
    TextLayerQualityCode.BAD: "Плохой текстовый слой",
    TextLayerQualityCode.PDF_READ_ERROR: "Ошибка чтения PDF",
}

CODE_DESCRIPTIONS_RU = {
    TextLayerQualityCode.GOOD: (
        "Текстовый слой пригоден для автоматического извлечения. "
        "Можно передавать текст в логический парсер."
    ),
    TextLayerQualityCode.SUSPECT: (
        "Текстовый слой частично пригоден, но есть признаки риска. "
        "Желательно логировать предупреждение или проверить альтернативным извлечением."
    ),
    TextLayerQualityCode.BAD: (
        "Текстовый слой непригоден или отсутствует. "
        "Для надежного парсинга нужен OCR или другой способ извлечения."
    ),
    TextLayerQualityCode.PDF_READ_ERROR: (
        "PDF не удалось открыть или прочитать. Это техническая ошибка входного файла, "
        "а не оценка качества текстового слоя."
    ),
}

MARKER_LABELS_RU = {
    "no_text": "текстовый слой отсутствует",
    "pdf_error": "ошибка чтения PDF",
    "question_marks": "есть знаки вопроса вместо символов",
    "many_question_marks": "много знаков вопроса вместо текста",
    "question_mark_sequence": "последовательности ?????",
    "replacement_char": "есть символы замены �",
    "many_suspicious_symbols": "много нестандартных символов",
    "broken_font_encoding": "битая кодировка встроенного шрифта",
    "pseudo_translit_klass": "псевдолатиница вместо русского текста",
    "pseudo_translit_pravila": "псевдолатиница вместо русского текста",
    "pseudo_translit_obsl": "псевдолатиница вместо русского текста",
    "pseudo_translit_soot": "псевдолатиница вместо русского текста",
}

# Explicit markers of broken text layers in old Russian-language PDFs.
# Ordinary Latin text and normal English documents are not treated as errors.
SUSPICIOUS_WORD_PATTERNS = {
    "QORRIJRKIJ": re.compile(r"\bQORRIJRKIJ\b", re.IGNORECASE),
    "MOQRKOJ": re.compile(r"\bMOQRKOJ\b", re.IGNORECASE),
    "QFDIRSQ": re.compile(r"\bQFDIRSQ\b", re.IGNORECASE),
    "RTEOVOERSCA": re.compile(r"\bRTEOVOERSCA\b", re.IGNORECASE),
    "pRAWILA": re.compile(r"\bpRAWILA\b", re.IGNORECASE),
    "KLASSIFIKACII": re.compile(r"\bKLASSIFIKACII\b", re.IGNORECASE),
    "POSTROJKI": re.compile(r"\bPOSTROJKI\b", re.IGNORECASE),
    "SUDOW": re.compile(r"\bSUDOW\b", re.IGNORECASE),
    "OBSLUVIWANIQ": re.compile(r"\bOBSLUVIWANIQ\b", re.IGNORECASE),
    "TEHNOLOGI": re.compile(r"\b[A-Za-z]*TEHNOLOGI[A-Za-z]*\b", re.IGNORECASE),
    "SOOTWETSTW": re.compile(r"\b[A-Za-z]*SOOTWETSTW[A-Za-z]*\b", re.IGNORECASE),
    "USTANAWLIW": re.compile(r"\b[A-Za-z]*USTANAWLIW[A-Za-z]*\b", re.IGNORECASE),
}

TRANSLITERATION_PATTERNS = {
    "pseudo_translit_klass": re.compile(r"\b[A-Za-z]*KLASSIFIK[A-Za-z]*\b", re.IGNORECASE),
    "pseudo_translit_pravila": re.compile(r"\b[Pp]RAWILA\b"),
    "pseudo_translit_obsl": re.compile(r"\b[A-Za-z]*OBSLUVIW[A-Za-z]*\b", re.IGNORECASE),
    "pseudo_translit_soot": re.compile(r"\b[A-Za-z]*SOOTWETSTW[A-Za-z]*\b", re.IGNORECASE),
}

ALLOWED_SYMBOLS = set(string.ascii_letters + string.digits + string.whitespace)
ALLOWED_SYMBOLS.update(
    ".,;:!?()[]{}<>+-=*/\\'\"`~@#$%^&_|\u00a0"
    "\u2013\u2014\u2012\u2212\u00ab\u00bb\u201c\u201d\u201e\u2018\u2019"
)


@dataclass(slots=True)
class TextQualityResult:
    code: int
    code_name: str
    code_ru: str
    score: int
    is_usable: bool
    needs_ocr: bool
    problem_ru: str
    language_detected: str
    markers: list[str] = field(default_factory=list)
    markers_ru: list[str] = field(default_factory=list)
    metrics: dict[str, int | float | bool] = field(default_factory=dict)
    sample_text: str = ""
    source_name: str = ""
    source_path: str = ""
    file_size_mb: float = 0.0
    pages_total: int = 0
    pages_scanned: int = 0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def assess_pdf_file(pdf_path: str | Path, pages_limit: int = DEFAULT_PAGES_LIMIT) -> int:
    """Return only the suitability code for a PDF file."""
    return analyze_pdf_file(pdf_path, pages_limit=pages_limit).code


def assess_text(text: str) -> int:
    """Return only the suitability code for already extracted text."""
    return analyze_text(text).code


def analyze_pdf_file(
    pdf_path: str | Path,
    pages_limit: int = DEFAULT_PAGES_LIMIT,
) -> TextQualityResult:
    """Extract text from a PDF text layer and return detailed quality diagnostics."""
    path = Path(pdf_path)
    if pages_limit < 1:
        raise ValueError("pages_limit must be >= 1")

    try:
        text, pages_total, pages_scanned = extract_text_from_pdf(path, pages_limit)
    except Exception as exc:
        return pdf_read_error_result(path, exc)

    file_size_mb = round(path.stat().st_size / (1024 * 1024), 3) if path.exists() else 0.0
    return analyze_text(
        text,
        source_name=path.name,
        source_path=str(path),
        file_size_mb=file_size_mb,
        pages_total=pages_total,
        pages_scanned=pages_scanned,
    )


def analyze_text(
    text: str,
    *,
    source_name: str = "",
    source_path: str = "",
    file_size_mb: float = 0.0,
    pages_total: int = 0,
    pages_scanned: int = 0,
) -> TextQualityResult:
    """Analyze plain text that was extracted by any upstream PDF reader."""
    text = text or ""
    counts = count_chars(text)
    extracted_chars = counts["extracted_chars"]
    normalized_text = normalize_whitespace(text)

    markers: list[str] = []
    if extracted_chars == 0:
        markers.append("no_text")

    mojibake_detected, transliteration_detected, detected_markers = detect_suspicious_markers(
        text,
        normalized_text,
    )
    markers.extend(detected_markers)

    question_ratio = safe_ratio(counts["question_marks_count"], extracted_chars)
    replacement_ratio = safe_ratio(counts["replacement_char_count"], extracted_chars)
    printable_ratio = safe_ratio(counts["printable_chars"], extracted_chars)
    cyrillic_ratio = safe_ratio(counts["cyrillic_chars"], extracted_chars)
    latin_ratio = safe_ratio(counts["latin_chars"], extracted_chars)
    suspicious_uppercase_ratio = calculate_suspicious_uppercase_ratio(text)
    suspicious_symbol_ratio = calculate_suspicious_symbol_ratio(text)

    if question_ratio > 0.01:
        markers.append("many_question_marks")
    if replacement_ratio > 0:
        markers.append("replacement_char")
    if suspicious_symbol_ratio > 0.05:
        markers.append("many_suspicious_symbols")

    score = calculate_quality_score(
        extracted_chars=extracted_chars,
        question_ratio=question_ratio,
        replacement_ratio=replacement_ratio,
        printable_ratio=printable_ratio,
        mojibake_detected=mojibake_detected,
        transliteration_detected=transliteration_detected,
        suspicious_uppercase_ratio=suspicious_uppercase_ratio,
        suspicious_symbol_ratio=suspicious_symbol_ratio,
    )
    code = quality_code_from_score(score)
    unique_markers = sorted(set(markers))

    metrics: dict[str, int | float | bool] = {
        "extracted_chars": extracted_chars,
        "cyrillic_chars": counts["cyrillic_chars"],
        "latin_chars": counts["latin_chars"],
        "digit_chars": counts["digit_chars"],
        "whitespace_chars": counts["whitespace_chars"],
        "question_marks_count": counts["question_marks_count"],
        "replacement_char_count": counts["replacement_char_count"],
        "printable_ratio": printable_ratio,
        "cyrillic_ratio": cyrillic_ratio,
        "latin_ratio": latin_ratio,
        "question_ratio": question_ratio,
        "replacement_ratio": replacement_ratio,
        "suspicious_uppercase_ratio": suspicious_uppercase_ratio,
        "suspicious_symbol_ratio": suspicious_symbol_ratio,
        "mojibake_detected": mojibake_detected,
        "transliteration_detected": transliteration_detected,
    }

    return build_result(
        code=code,
        score=score,
        markers=unique_markers,
        language_detected=detect_language(counts["cyrillic_chars"], counts["latin_chars"]),
        metrics=metrics,
        sample_text=normalized_text[:SAMPLE_TEXT_LIMIT],
        source_name=source_name,
        source_path=source_path,
        file_size_mb=file_size_mb,
        pages_total=pages_total,
        pages_scanned=pages_scanned,
    )


def decode_quality_code(code: int | TextLayerQualityCode) -> str:
    """Return a human-readable Russian explanation for a suitability code."""
    quality_code = TextLayerQualityCode(int(code))
    return f"{quality_code.value} {quality_code.name}: {CODE_DESCRIPTIONS_RU[quality_code]}"


def quality_code_info(code: int | TextLayerQualityCode) -> dict[str, str | int | bool]:
    """Return code metadata for structured logging or an API response."""
    quality_code = TextLayerQualityCode(int(code))
    return {
        "code": quality_code.value,
        "code_name": quality_code.name,
        "code_ru": STATUS_LABELS_RU[quality_code],
        "description_ru": CODE_DESCRIPTIONS_RU[quality_code],
        "is_usable": quality_code == TextLayerQualityCode.GOOD,
        "needs_ocr": quality_code == TextLayerQualityCode.BAD,
    }


def result_to_log_message(result: TextQualityResult) -> str:
    """Build a compact human-readable message for service logs."""
    markers = "; ".join(result.markers_ru) if result.markers_ru else "маркеры не обнаружены"
    return (
        f"{result.code} {result.code_name}: {result.code_ru}; "
        f"score={result.score}; {result.problem_ru}; markers={markers}"
    )


def extract_text_from_pdf(pdf_path: Path, pages_limit: int) -> tuple[str, int, int]:
    """Extract plain text from the first pages_limit pages using PyMuPDF."""
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PyMuPDF is required for PDF input. Install it with: pip install PyMuPDF") from exc

    with fitz.open(pdf_path) as document:
        pages_total = document.page_count
        pages_scanned = min(pages_total, pages_limit)
        chunks: list[str] = []

        for page_index in range(pages_scanned):
            page = document.load_page(page_index)
            chunks.append(page.get_text("text") or "")

    return "\n".join(chunks), pages_total, pages_scanned


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def count_chars(text: str) -> dict[str, int]:
    return {
        "extracted_chars": len(text),
        "cyrillic_chars": len(re.findall(r"[А-Яа-яЁё]", text)),
        "latin_chars": len(re.findall(r"[A-Za-z]", text)),
        "digit_chars": sum(char.isdigit() for char in text),
        "whitespace_chars": sum(char.isspace() for char in text),
        "question_marks_count": text.count("?"),
        "replacement_char_count": text.count("\ufffd"),
        "printable_chars": sum(char.isprintable() or char.isspace() for char in text),
    }


def safe_ratio(numerator: int | float, denominator: int | float) -> float:
    if denominator <= 0:
        return 0.0
    return round(float(numerator) / float(denominator), 4)


def detect_language(cyrillic_chars: int, latin_chars: int) -> str:
    letters = cyrillic_chars + latin_chars
    if letters < 40:
        return "UNKNOWN"

    cyrillic_share = cyrillic_chars / letters
    latin_share = latin_chars / letters

    if cyrillic_share >= 0.7:
        return "CYRILLIC"
    if latin_share >= 0.7:
        return "LATIN"
    if cyrillic_share >= 0.2 and latin_share >= 0.2:
        return "MIXED"
    return "UNKNOWN"


def detect_suspicious_markers(text: str, normalized_text: str) -> tuple[bool, bool, list[str]]:
    markers: list[str] = []

    for marker, pattern in SUSPICIOUS_WORD_PATTERNS.items():
        if pattern.search(normalized_text):
            markers.append(marker)

    transliteration_detected = False
    for marker, pattern in TRANSLITERATION_PATTERNS.items():
        if pattern.search(normalized_text):
            transliteration_detected = True
            markers.append(marker)

    question_marks_count = text.count("?")
    replacement_char_count = text.count("\ufffd")
    if "?????" in text:
        markers.append("question_mark_sequence")
    if question_marks_count:
        markers.append("question_marks")
    if replacement_char_count:
        markers.append("replacement_char")

    mojibake_detected = bool(
        replacement_char_count
        or "?????" in text
        or any(marker in markers for marker in SUSPICIOUS_WORD_PATTERNS)
    )
    return mojibake_detected, transliteration_detected, sorted(set(markers))


def calculate_suspicious_uppercase_ratio(text: str) -> float:
    words = re.findall(r"\b[A-Za-z]{2,}\b", text)
    if not words:
        return 0.0

    suspicious = 0
    for word in words:
        if len(word) < 6:
            continue
        uppercase_letters = sum(char.isupper() for char in word)
        if uppercase_letters / len(word) >= 0.8:
            suspicious += 1

    return safe_ratio(suspicious, len(words))


def calculate_suspicious_symbol_ratio(text: str) -> float:
    if not text:
        return 0.0

    suspicious = 0
    for char in text:
        if char in ALLOWED_SYMBOLS:
            continue
        if re.match(r"[А-Яа-яЁё]", char):
            continue
        suspicious += 1

    return safe_ratio(suspicious, len(text))


def calculate_quality_score(
    extracted_chars: int,
    question_ratio: float,
    replacement_ratio: float,
    printable_ratio: float,
    mojibake_detected: bool,
    transliteration_detected: bool,
    suspicious_uppercase_ratio: float,
    suspicious_symbol_ratio: float,
) -> int:
    if extracted_chars == 0:
        return 0

    score = 100

    if extracted_chars < 200:
        score -= 45
    elif extracted_chars < 1000:
        score -= 20

    if question_ratio > 0.10:
        score -= 45
    elif question_ratio > 0.05:
        score -= 30
    elif question_ratio > 0.01:
        score -= 15

    if replacement_ratio > 0.02:
        score -= 40
    elif replacement_ratio > 0.005:
        score -= 25
    elif replacement_ratio > 0:
        score -= 10

    if printable_ratio < 0.70:
        score -= 35
    elif printable_ratio < 0.85:
        score -= 20
    elif printable_ratio < 0.95:
        score -= 8

    if mojibake_detected:
        score -= 30

    if transliteration_detected:
        score -= 25

    uppercase_has_context = (
        mojibake_detected
        or transliteration_detected
        or question_ratio > 0.01
        or replacement_ratio > 0
        or suspicious_symbol_ratio > 0.05
    )
    if uppercase_has_context:
        if suspicious_uppercase_ratio > 0.35:
            score -= 15
        elif suspicious_uppercase_ratio > 0.20:
            score -= 8
        elif suspicious_uppercase_ratio > 0.10:
            score -= 4

    if suspicious_symbol_ratio > 0.20:
        score -= 30
    elif suspicious_symbol_ratio > 0.10:
        score -= 18
    elif suspicious_symbol_ratio > 0.05:
        score -= 8

    return max(0, min(100, int(round(score))))


def quality_code_from_score(score: int) -> TextLayerQualityCode:
    if score >= GOOD_THRESHOLD:
        return TextLayerQualityCode.GOOD
    if score >= BAD_THRESHOLD:
        return TextLayerQualityCode.SUSPECT
    return TextLayerQualityCode.BAD


def translate_markers_ru(markers: list[str]) -> list[str]:
    labels: list[str] = []

    for marker in sorted(set(markers)):
        if marker in SUSPICIOUS_WORD_PATTERNS:
            labels.append("битая кодировка встроенного шрифта")
        else:
            labels.append(MARKER_LABELS_RU.get(marker, marker))

    return sorted(set(labels))


def describe_text_layer_problem_ru(code: TextLayerQualityCode, markers: list[str]) -> str:
    if code == TextLayerQualityCode.PDF_READ_ERROR:
        return CODE_DESCRIPTIONS_RU[TextLayerQualityCode.PDF_READ_ERROR]

    if code == TextLayerQualityCode.GOOD:
        return CODE_DESCRIPTIONS_RU[TextLayerQualityCode.GOOD]

    if "no_text" in markers:
        return "Текстовый слой отсутствует. Нужен OCR."

    if any(marker in SUSPICIOUS_WORD_PATTERNS for marker in markers):
        return (
            "Текст визуально может читаться, но текстовый слой поврежден. "
            "Нужен OCR или альтернативное извлечение."
        )

    if "many_suspicious_symbols" in markers:
        return (
            "В текстовом слое много нестандартных символов. "
            "Возможна битая кодировка шрифта или формульно-табличный PDF."
        )

    if "many_question_marks" in markers or "question_mark_sequence" in markers:
        return "В текстовом слое много замененных символов. Автоматическое извлечение ненадежно."

    return CODE_DESCRIPTIONS_RU[code]


def build_result(
    *,
    code: TextLayerQualityCode,
    score: int,
    markers: list[str],
    language_detected: str,
    metrics: dict[str, int | float | bool],
    sample_text: str,
    source_name: str = "",
    source_path: str = "",
    file_size_mb: float = 0.0,
    pages_total: int = 0,
    pages_scanned: int = 0,
    error: str | None = None,
) -> TextQualityResult:
    return TextQualityResult(
        code=code.value,
        code_name=code.name,
        code_ru=STATUS_LABELS_RU[code],
        score=score,
        is_usable=code == TextLayerQualityCode.GOOD,
        needs_ocr=code == TextLayerQualityCode.BAD,
        problem_ru=describe_text_layer_problem_ru(code, markers),
        language_detected=language_detected,
        markers=markers,
        markers_ru=translate_markers_ru(markers),
        metrics=metrics,
        sample_text=sample_text,
        source_name=source_name,
        source_path=source_path,
        file_size_mb=file_size_mb,
        pages_total=pages_total,
        pages_scanned=pages_scanned,
        error=error,
    )


def pdf_read_error_result(pdf_path: Path, error: Exception) -> TextQualityResult:
    file_size_mb = round(pdf_path.stat().st_size / (1024 * 1024), 3) if pdf_path.exists() else 0.0
    return build_result(
        code=TextLayerQualityCode.PDF_READ_ERROR,
        score=0,
        markers=["pdf_error"],
        language_detected="UNKNOWN",
        metrics={},
        sample_text="",
        source_name=pdf_path.name,
        source_path=str(pdf_path),
        file_size_mb=file_size_mb,
        error=str(error),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check PDF text-layer quality.")
    parser.add_argument("input", help="PDF file path, or plain text when --text is used.")
    parser.add_argument("--text", action="store_true", help="Treat input argument as already extracted text.")
    parser.add_argument("--pages", type=int, default=DEFAULT_PAGES_LIMIT, help="PDF pages to scan.")
    parser.add_argument("--json", action="store_true", help="Print full JSON result.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = analyze_text(args.input) if args.text else analyze_pdf_file(args.input, pages_limit=args.pages)

    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(result_to_log_message(result))

    return 0 if result.code != TextLayerQualityCode.PDF_READ_ERROR.value else 1


if __name__ == "__main__":
    raise SystemExit(main())

# пример : python pdf_text_quality_module.py docs/example.pdf --json
