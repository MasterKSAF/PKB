"""Нормализация метаданных и вычисление бизнес-ключа документа."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Final

from app.core.exceptions import MetadataValidationError, NormalizationFailedError

VALID_ERAS: Final[frozenset[str]] = frozenset(
    {"USSR", "CIS", "RF", "CURRENT"}
)

SOURCE_TYPE_TO_KEY: Final[dict[str, str]] = {
    "GOST": "gost",
    "GOST_R": "gost_r",
    "OST": "ost",
    "RD": "rd",
    "TU": "tu",
    "ISO": "iso",
    "DNV": "dnv",
    "ASTM": "astm",
    "RMRS": "rmrs",
    "OTHER": "other",
}

_GOST_R_RE = re.compile(r"гост\s*р|gost\s*r", re.IGNORECASE)
_GOST_RE = re.compile(r"гост|gost", re.IGNORECASE)
_RMRS_RE = re.compile(r"морск\w*\s+регистр|rmrs", re.IGNORECASE)
_OST_RE = re.compile(r"ост\d*|ost\d*", re.IGNORECASE)
_RD_RE = re.compile(r"(?:рд|rd)[\s\d]", re.IGNORECASE)
_TU_RE = re.compile(r"(?:ту|tu)[\s\d]", re.IGNORECASE)
_PKPS_RE = re.compile(r"пкпс", re.IGNORECASE)
_ISO_RE = re.compile(r"\biso\s*\d", re.IGNORECASE)
_DNV_RE = re.compile(r"\bdnv[-_\s]", re.IGNORECASE)
_ASTM_RE = re.compile(r"\bastm\s", re.IGNORECASE)
_SNIP_RE = re.compile(r"снип|сп\s|санпин", re.IGNORECASE)
_USSR_MARKERS = ("ссср", "ussr")


@dataclass(frozen=True)
class BusinessKeyResult:
    title_hash_sha256: str
    title_key: str
    normalized_title: str
    source_type_normalized: str
    era_normalized: str


def normalize_title(title: str) -> str:
    """MVP: lowercase, ё→е, схлопывание пробелов."""
    text = title.strip().lower().replace("ё", "е")
    normalized = " ".join(text.split())
    if not normalized:
        raise NormalizationFailedError("Title is empty after normalization")
    return normalized


def normalize_era(value: str) -> tuple[str, str]:
    """Возвращает (era для title_key, era_normalized)."""
    canonical = value.strip().upper()
    if canonical not in VALID_ERAS:
        raise MetadataValidationError(
            f"Invalid era: {value!r}. Allowed: {', '.join(sorted(VALID_ERAS))}"
        )
    return canonical, canonical.lower()


def normalize_source_type(value: str) -> str:
    canonical = value.strip().upper().replace("-", "_")
    if canonical not in SOURCE_TYPE_TO_KEY:
        allowed = ", ".join(sorted(SOURCE_TYPE_TO_KEY))
        raise MetadataValidationError(
            f"Invalid source_type: {value!r}. Allowed: {allowed}"
        )
    return SOURCE_TYPE_TO_KEY[canonical]


def _segment(value: str | None) -> str:
    if value is None:
        return ""
    return str(value).strip()


def build_title_key(
    *,
    era: str,
    source_type_normalized: str,
    mks_oks_code: str | None,
    okstu_code: str | None,
    doc_code: str,
    normalized_title: str,
) -> str:
    return "|".join(
        [
            era,
            source_type_normalized,
            _segment(mks_oks_code),
            _segment(okstu_code),
            _segment(doc_code),
            normalized_title,
        ]
    )


def compute_business_key(
    *,
    era: str,
    source_type: str,
    doc_code: str,
    title: str,
    mks_oks_code: str | None = None,
    okstu_code: str | None = None,
) -> BusinessKeyResult:
    doc_code_value = doc_code.strip()
    title_value = title.strip()
    if not doc_code_value:
        raise MetadataValidationError("doc_code is required")
    if not title_value:
        raise MetadataValidationError("title is required")

    era_key, era_normalized = normalize_era(era)
    source_type_normalized = normalize_source_type(source_type)
    normalized_title = normalize_title(title_value)
    title_key = build_title_key(
        era=era_key,
        source_type_normalized=source_type_normalized,
        mks_oks_code=mks_oks_code,
        okstu_code=okstu_code,
        doc_code=doc_code_value,
        normalized_title=normalized_title,
    )
    title_hash_sha256 = hashlib.sha256(title_key.encode("utf-8")).hexdigest()
    return BusinessKeyResult(
        title_hash_sha256=title_hash_sha256,
        title_key=title_key,
        normalized_title=normalized_title,
        source_type_normalized=source_type_normalized,
        era_normalized=era_normalized,
    )


def era_from_year(year: int | None, *texts: str | None) -> str:
    inferred = infer_era(*texts)
    if inferred != "CURRENT":
        return inferred
    if year is None:
        return "CURRENT"
    if year < 1992:
        return "USSR"
    if year <= 1999:
        return "CIS"
    return "RF"


def infer_era(*texts: str | None) -> str:
    combined = " ".join(t for t in texts if t).lower()
    if any(marker in combined for marker in _USSR_MARKERS):
        return "USSR"
    if _GOST_R_RE.search(combined):
        return "RF"
    return "CURRENT"


def infer_source_type(*texts: str | None) -> str:
    combined = " ".join(t for t in texts if t)
    if _RMRS_RE.search(combined):
        return "RMRS"
    if _GOST_R_RE.search(combined):
        return "GOST_R"
    if _GOST_RE.search(combined):
        return "GOST"
    if _OST_RE.search(combined):
        return "OST"
    if _RD_RE.search(combined):
        return "RD"
    if _TU_RE.search(combined):
        return "TU"
    if _PKPS_RE.search(combined):
        return "RD"
    if _ISO_RE.search(combined):
        return "ISO"
    if _DNV_RE.search(combined):
        return "DNV"
    if _ASTM_RE.search(combined):
        return "ASTM"
    if _SNIP_RE.search(combined):
        return "OTHER"
    return "OTHER"
