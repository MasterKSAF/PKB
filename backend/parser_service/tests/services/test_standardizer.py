"""
Тесты для стандартизатора JSON (standardizer.py)
Проверяют преобразование как сырого JSON, так и контейнера от нормализатора.
"""
import pytest
from app.services.standardizer import JsonStandardizer


def test_standardizer_transform_container():
    """Проверка: на входе контейнер (с ключами document_info, content, metadata).
    Стандартизируется только поле 'content', остальное сохраняется."""
    input_data = {
        "document_info": {"task_id": 123},
        "content": {
            "kids": [{"type": "paragraph", "page number": 1, "content": "Hello"}],
            "number of pages": 1
        },
        "metadata": {"some": "value"}
    }
    result = JsonStandardizer.transform(input_data, file_name="orig.pdf")

    # Документ-инфо и метаданные не должны потеряться
    assert result["document_info"] == {"task_id": 123}
    assert result["metadata"]["some"] == "value"

    # Внутри content структура должна быть преобразована
    assert result["content"]["document"]["source"]["file_name"] == "orig.pdf"
    assert result["content"]["document"]["block"][0]["content"] == "Hello"
    assert result["content"]["document"]["block"][0]["type"] == "paragraph"


def test_standardizer_transform_raw():
    raw = {
        "kids": [{"type": "image", "source": "1d_images/fig1.png", "page number": 1}],
        "number of pages": 1,
        "file name": "raw_name.pdf"
    }
    result = JsonStandardizer.transform(raw, file_name="override.pdf")
    assert result["document"]["source"]["file_name"] == "override.pdf"
    assert result["document"]["block"][0]["type"] == "image"
    assert "image_key" in result["document"]["block"][0]
    # Исправлено: ожидаем имя файла без префикса 1d_images/
    assert result["document"]["block"][0]["image_key"] == "fig1.png"
    

def test_standardizer_missing_fields():
    """Проверка: при отсутствии полей используются значения по умолчанию."""
    result = JsonStandardizer.transform({})

    assert result["document"]["source"]["page_count"] == 1
    assert result["document"]["pages"] == [{"page": 1, "width": 210.0, "height": 297.0}]
    assert result["document"]["block"] == []  # пустой блок