import pytest
from app.services.parsers.docling.text_cleaner import (
    soft_clean_line,
    is_garbage_line,
    process_extracted_text,
)


class TestSoftCleanLine:
    def test_removes_control_chars_silently(self):
        assert soft_clean_line("abc\x00def\x1fghi") == "abcdefghi"

    def test_keeps_tab_newline_as_space(self):
        assert soft_clean_line("a\tb\nc") == "a b c"

    def test_removes_cid_sequences(self):
        assert soft_clean_line("text /31/32 /16/18/24 more") == "text more"

    def test_removes_cid_single(self):
        assert soft_clean_line("/39/48/65/66/76") == ""

    def test_removes_long_cid(self):
        raw = "/82/85/76/69/83 /70/79/82 /84/72/69 /67/76/65/83/83"
        assert soft_clean_line(raw) == ""

    def test_collapses_multiple_spaces(self):
        assert soft_clean_line("a   b    c") == "a b c"

    def test_preserves_normal_russian(self):
        line = "Электронный аналог печатного издания"
        assert soft_clean_line(line) == line

    def test_preserves_normal_text_with_specials(self):
        line = "НД № 2-020101-088"
        assert soft_clean_line(line) == line


class TestIsGarbageLine:
    def test_empty_returns_true(self):
        assert is_garbage_line("") is True
        assert is_garbage_line("   ") is True

    def test_whitelisted_words_return_false(self):
        assert is_garbage_line("image") is False
        assert is_garbage_line("pdf") is False

    def test_all_uppercase_latin_returns_true(self):
        assert is_garbage_line("QORRIJRKIJ MOQRKOJ QFDIRSQ RTEOVOERSCA") is True

    def test_short_avg_word_length_returns_true(self):
        assert is_garbage_line("y , m g Z") is True

    def test_single_letter_garbage(self):
        assert is_garbage_line("b a") is True
        assert is_garbage_line("e h") is True
        assert is_garbage_line("Z") is True
        assert is_garbage_line("h") is True

    def test_low_allowed_ratio_returns_true(self):
        assert is_garbage_line("‰ 2-020101-088") is True

    def test_no_letters_returns_true(self):
        assert is_garbage_line("l \\ _") is True

    def test_valid_russian_returns_false(self):
        line = "Электронный аналог печатного издания"
        assert is_garbage_line(line) is False

    def test_russian_doc_number_returns_false(self):
        assert is_garbage_line("НД № 2-020101-088") is False

    def test_label_date_returns_false(self):
        assert is_garbage_line("h 14.09.15") is False

    def test_english_text_returns_false(self):
        assert is_garbage_line("This is a sample paragraph for testing") is False

    def test_corrupt_doc_number_latin_kept(self):
        assert is_garbage_line("ND N 2-020101-087-E") is False

    def test_mixed_garbage_cid_returns_true(self):
        assert is_garbage_line(soft_clean_line("text /31/32 /16/18/24/27 more")) is True


class TestProcessExtractedText:
    def test_filters_known_garbage_keeps_known_valid(self):
        raw = """b a

^ Z

g b

/31/32 /16/18/24/27/16 /31/30 /30/17/30/32/35 /20/30/18/16/29/24/46

/28/30/32/33/26/24/37 /33/35 /20/30/18

/39/48/65/66/76 /73/73/73

/33/24/19/29/16/27/44/29/43/21 /33/32/21/20/33/34/18/16

‰ 2-020101-088

image

/33/48/61/58/66 /45 /31/53/66/53/64/49/67/64/51 /50/48/49/54

Z

y , m g Z

e h

l \\ _

]

i _ q

j ` ^

_ g Z l g h

]

h

g h

]

h 14.09.15

QORRIJRKIJ MOQRKOJ QFDIRSQ RTEOVOERSCA

Электронный аналог печатного
издания, утвержденного 14.09.15

НД № 2-020101-088"""
        result = process_extracted_text(raw)
        lines = [l for l in result.split("\n") if l.strip()]
        assert "image" in lines
        assert "Электронный аналог печатного" in result
        assert "издания, утвержденного 14.09.15" in result
        assert "НД № 2-020101-088" in result
        assert "h 14.09.15" in result
        assert "b a" not in lines
        assert "e h" not in lines
        assert "Z" not in lines
        assert "QORRIJRKIJ MOQRKOJ QFDIRSQ RTEOVOERSCA" not in lines
        assert "/31/32" not in result

    def test_cid_encoded_english_filtered(self):
        raw = """/82/85/76/69/83

/70/79/82 /84/72/69 /67/76/65/83/83/73/70/73/67/65 /84/73/79/78
/65/78/68 /67/79/78/83/84/82/85/67/84/73/79/78 /79/70 /83/69/65
/45/71/79/73/78/71 /83/72/73/80/83

/80 /65/82/84 /88/73/73 /82/69/70/82/73/71/69/82/65 /84/73/78/71
/80/76/65/78/84/83

ND N 2-020101-087-E"""
        result = process_extracted_text(raw)
        assert result.strip() == "ND N 2-020101-087-E"

    def test_empty_input_returns_empty(self):
        assert process_extracted_text("") == ""
        assert process_extracted_text("  \n  \n  ") == ""
