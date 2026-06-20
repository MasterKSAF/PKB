import hashlib

import pytest

from app.core.exceptions import MetadataValidationError, NormalizationFailedError
from app.services.normalizer import (
    build_title_key,
    compute_business_key,
    era_from_year,
    infer_era,
    infer_source_type,
    normalize_title,
)


def test_normalize_title_lowercase_and_spaces():
    assert normalize_title("  СТОЙКИ   УСТАНОВОЧНЫЕ  ") == "стойки установочные"


def test_normalize_title_replaces_yo():
    assert normalize_title("ёлка") == "елка"


def test_normalize_title_empty_raises():
    with pytest.raises(NormalizationFailedError):
        normalize_title("   ")


def test_build_title_key_with_null_codes():
    key = build_title_key(
        era="USSR",
        source_type_normalized="gost",
        mks_oks_code="47.020",
        okstu_code=None,
        doc_code="20868-81",
        normalized_title="стойки установочные крепежные",
    )
    assert key == (
        "USSR|gost|47.020||20868-81|стойки установочные крепежные"
    )


def test_compute_business_key_api_example():
    result = compute_business_key(
        era="USSR",
        source_type="GOST",
        mks_oks_code="47.020",
        okstu_code=None,
        doc_code="20868-81",
        title="СТОЙКИ УСТАНОВОЧНЫЕ КРЕПЕЖНЫЕ",
    )
    expected_key = (
        "USSR|gost|47.020||20868-81|стойки установочные крепежные"
    )
    assert result.title_key == expected_key
    assert result.normalized_title == "стойки установочные крепежные"
    assert result.source_type_normalized == "gost"
    assert result.era_normalized == "ussr"
    assert result.title_hash_sha256 == hashlib.sha256(
        expected_key.encode("utf-8")
    ).hexdigest()


def test_compute_business_key_gost_r_example():
    result = compute_business_key(
        era="RF",
        source_type="GOST_R",
        mks_oks_code=None,
        okstu_code=None,
        doc_code="2.105-95",
        title="ЕСКД",
    )
    assert result.title_key == "RF|gost_r|||2.105-95|ескд"
    assert result.source_type_normalized == "gost_r"


def test_invalid_era_raises():
    with pytest.raises(MetadataValidationError):
        compute_business_key(
            era="INVALID",
            source_type="GOST",
            doc_code="1",
            title="Test",
        )


def test_infer_era_and_source_type():
    assert infer_era("Комитет СССР") == "USSR"
    assert infer_source_type("ГОСТ 20868-81") == "GOST"
    assert infer_source_type("ГОСТ Р 2.105-95") == "GOST_R"
    assert infer_source_type("РОССИЙСКИЙ МОРСКОЙ РЕГИСТР") == "RMRS"


def test_era_from_year():
    assert era_from_year(1981, "документ") == "USSR"
    assert era_from_year(1995, "документ") == "CIS"
    assert era_from_year(2023, "документ") == "RF"
    assert era_from_year(None, "Комитет СССР") == "USSR"
