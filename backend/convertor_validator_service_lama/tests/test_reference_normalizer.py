from convertor_validator_service_lama.services.reference_normalizer import (
    document_codes_equal,
    expand_gost_document_codes,
    expand_gost_document_codes_from_values,
)


def test_expands_cyrillic_gost_reference_range_with_repeated_prefix() -> None:
    text = (
        "\u041a\u0440\u0435\u043f\u0435\u0436\u043d\u044b\u0435 "
        "\u0443\u0441\u0442\u0430\u043d\u043e\u0432\u043e\u0447\u043d\u044b\u0435 "
        "\u0441\u0442\u043e\u0439\u043a\u0438 "
        "\u0441\u043b\u0435\u0434\u0443\u0435\u0442 "
        "\u0438\u0437\u0433\u043e\u0442\u043e\u0432\u043b\u044f\u0442\u044c "
        "\u043f\u043e "
        "\u0413\u041e\u0421\u0422 20862-81- "
        "\u0413\u041e\u0421\u0422 20867-81."
    )

    assert expand_gost_document_codes(text) == [
        "\u0413\u041e\u0421\u0422 20862-81",
        "\u0413\u041e\u0421\u0422 20863-81",
        "\u0413\u041e\u0421\u0422 20864-81",
        "\u0413\u041e\u0421\u0422 20865-81",
        "\u0413\u041e\u0421\u0422 20866-81",
        "\u0413\u041e\u0421\u0422 20867-81",
    ]


def test_expands_gost_reference_range_without_repeated_prefix() -> None:
    assert expand_gost_document_codes(
        "\u0413\u041e\u0421\u0422 20862-81 - 20867-81"
    ) == [
        "\u0413\u041e\u0421\u0422 20862-81",
        "\u0413\u041e\u0421\u0422 20863-81",
        "\u0413\u041e\u0421\u0422 20864-81",
        "\u0413\u041e\u0421\u0422 20865-81",
        "\u0413\u041e\u0421\u0422 20866-81",
        "\u0413\u041e\u0421\u0422 20867-81",
    ]


def test_expands_gost_reference_range_with_en_dash_and_em_dash() -> None:
    assert expand_gost_document_codes(
        "\u0413\u041e\u0421\u0422 20862-81 \u2013 \u0413\u041e\u0421\u0422 20864-81"
    ) == [
        "\u0413\u041e\u0421\u0422 20862-81",
        "\u0413\u041e\u0421\u0422 20863-81",
        "\u0413\u041e\u0421\u0422 20864-81",
    ]

    assert expand_gost_document_codes(
        "\u0413\u041e\u0421\u0422 20862-81 \u2014 \u0413\u041e\u0421\u0422 20863-81"
    ) == [
        "\u0413\u041e\u0421\u0422 20862-81",
        "\u0413\u041e\u0421\u0422 20863-81",
    ]


def test_keeps_single_gost_references_and_deduplicates() -> None:
    assert expand_gost_document_codes(
        "\u0413\u041e\u0421\u0422 20862-81, \u0413\u041e\u0421\u0422 20862-81, \u0413\u041e\u0421\u0422 20867-81"
    ) == [
        "\u0413\u041e\u0421\u0422 20862-81",
        "\u0413\u041e\u0421\u0422 20867-81",
    ]


def test_expands_gost_document_codes_from_multiple_values() -> None:
    assert expand_gost_document_codes_from_values(
        None,
        "\u0413\u041e\u0421\u0422 20862-81",
        "\u0413\u041e\u0421\u0422 20862-81- \u0413\u041e\u0421\u0422 20864-81",
    ) == [
        "\u0413\u041e\u0421\u0422 20862-81",
        "\u0413\u041e\u0421\u0422 20863-81",
        "\u0413\u041e\u0421\u0422 20864-81",
    ]


def test_document_codes_equal_normalizes_gost_prefix_and_dash_variants() -> None:
    assert document_codes_equal("GOST 20868-81", "\u0413\u041e\u0421\u0422 20868\u201481")
    assert document_codes_equal("\u0413\u041e\u0421\u0422 20868\u201381", "\u0413\u041e\u0421\u0422 20868-81")
    assert not document_codes_equal("GOST 20868-81", "\u0413\u041e\u0421\u0422 20862-81")
