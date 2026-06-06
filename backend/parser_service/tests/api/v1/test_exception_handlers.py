"""
Тесты глобальных обработчиков исключений.
Проверяют единый формат ошибок:
- ParserServiceError → соответствующий HTTP-статус и код
- RequestValidationError → 422 VALIDATION_ERROR
- необработанные Exception → 500 INTERNAL_SERVER_ERROR
"""
from fastapi.testclient import TestClient
from app.main import app
from app.core.exceptions import FileNotFoundError, UnsupportedFormatError

# Временные эндпоинты для тестирования обработчиков
@app.get("/test-file-not-found")
async def trigger_file_not_found():
    raise FileNotFoundError("test_key")

@app.get("/test-unsupported")
async def trigger_unsupported():
    raise UnsupportedFormatError("image/png")

client = TestClient(app)


def test_file_not_found_error_format():
    """Проверка: ошибка FILE_NOT_FOUND возвращает 404 и правильную структуру."""
    response = client.get("/test-file-not-found")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "FILE_NOT_FOUND"
    assert "test_key" in data["error"]["message"]


def test_unsupported_format_error_format():
    """Проверка: ошибка UNSUPPORTED_FORMAT возвращает 415."""
    response = client.get("/test-unsupported")
    assert response.status_code == 415
    data = response.json()
    assert data["error"]["code"] == "UNSUPPORTED_FORMAT"
    assert "image/png" in data["error"]["message"]


def test_validation_error_format():
    """
    Проверка: ошибка валидации Pydantic возвращает 422 VALIDATION_ERROR
    с подробностями в поле details.errors.
    """
    response = client.post("/api/v1/parser/process", json={"task_id": "not_a_number"})
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "errors" in data["error"]["details"]