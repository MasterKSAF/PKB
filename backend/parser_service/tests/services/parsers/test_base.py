"""
Тесты для базовых классов парсеров (base.py)
Проверяют:
- создание ParseResult с разными полями и значениями по умолчанию
- абстрактность BaseParser (требует реализации метода parse)
"""
import pytest
from app.services.parsers.base import ParseResult, BaseParser


class TestParseResult:
    def test_create_with_minimal_fields(self):
        """ParseResult можно создать только с full_json; остальные поля — значения по умолчанию."""
        pr = ParseResult(full_json={"key": "value"})
        assert pr.full_json == {"key": "value"}
        assert pr.images == []
        assert pr.total_pages == 1

    def test_create_with_all_fields(self):
        """ParseResult с явно заданными полями сохраняет их."""
        images = [(1, b"image_data", ".png")]
        pr = ParseResult(
            full_json={"pages": [1, 2, 3]},
            images=images,
            total_pages=3
        )
        assert pr.full_json["pages"] == [1, 2, 3]
        assert pr.images == images
        assert pr.total_pages == 3

    def test_images_default_factory(self):
        """Поле images для каждого экземпляра создаёт новый список, а не общий."""
        pr1 = ParseResult(full_json={})
        pr2 = ParseResult(full_json={})
        pr1.images.append((1, b"x", ".png"))
        # Изменение одного экземпляра не влияет на другой
        assert len(pr2.images) == 0


class TestBaseParser:
    def test_abstract_method_raises(self):
        """Прямое создание BaseParser невозможно (TypeError)."""
        with pytest.raises(TypeError):
            BaseParser()

    def test_concrete_subclass_must_implement_parse(self):
        """Класс, наследующий BaseParser без реализации parse, тоже нельзя инстанциировать."""
        class IncompleteParser(BaseParser):
            pass
        with pytest.raises(TypeError):
            IncompleteParser()

    def test_proper_implementation(self):
        """Корректная реализация parse позволяет создать экземпляр."""
        class GoodParser(BaseParser):
            async def parse(self, file_bytes, options):
                return ParseResult(full_json={"status": "ok"})

        parser = GoodParser()
        assert hasattr(parser, "parse")
        assert callable(parser.parse)