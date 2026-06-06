"""
Тесты для контекста выполнения пайплайна (ProcessingContext)
Проверяют:
- создание с обязательными полями
- значения по умолчанию для опциональных полей
- корректность поля original_file_name
- независимость опций между экземплярами
"""
import pytest
from app.services.pipeline.context import ProcessingContext
from app.services.parsers.base import ParseResult


class TestProcessingContext:
    def test_create_with_required_only(self):
        """Только обязательные поля (task_id, version_id, file_key)."""
        ctx = ProcessingContext(task_id=123, version_id="ver-1", file_key="doc.pdf")
        assert ctx.task_id == 123
        assert ctx.version_id == "ver-1"
        assert ctx.file_key == "doc.pdf"
        # Опциональные поля имеют значения по умолчанию
        assert ctx.options == {}
        assert ctx.file_bytes is None
        assert ctx.mime_type is None
        assert ctx.parse_result is None
        assert ctx.final_json is None
        assert ctx.max_pages is None
        assert ctx.original_file_name == ""

    def test_create_with_all_fields(self):
        """Контекст со всеми возможными полями."""
        parse_res = ParseResult(full_json={"a": 1})
        ctx = ProcessingContext(
            task_id=456,
            version_id="ver-2",
            file_key="report.pdf",
            options={"extract_tables": True},
            file_bytes=b"pdfdata",
            mime_type="application/pdf",
            parse_result=parse_res,
            final_json={"doc": {}},
            max_pages=5,
            original_file_name="original.pdf"
        )
        assert ctx.options["extract_tables"] is True
        assert ctx.file_bytes == b"pdfdata"
        assert ctx.mime_type == "application/pdf"
        assert ctx.parse_result is parse_res
        assert ctx.final_json == {"doc": {}}
        assert ctx.max_pages == 5
        assert ctx.original_file_name == "original.pdf"

    def test_options_default_factory(self):
        """Проверка, что options является отдельным словарём для каждого экземпляра."""
        ctx1 = ProcessingContext(task_id=1, version_id="v1", file_key="a.pdf")
        ctx2 = ProcessingContext(task_id=2, version_id="v2", file_key="b.pdf")
        ctx1.options["test"] = 42
        assert "test" not in ctx2.options

    def test_original_file_name_default_empty_string(self):
        """original_file_name по умолчанию – пустая строка."""
        ctx = ProcessingContext(task_id=1, version_id="v", file_key="f")
        assert ctx.original_file_name == ""

    def test_max_pages_optional_none(self):
        """max_pages по умолчанию None."""
        ctx = ProcessingContext(task_id=1, version_id="v", file_key="f")
        assert ctx.max_pages is None