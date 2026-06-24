"""
Forming unified API responses
"""

from fastapi import HTTPException


# List of (http_code, code_name, message) — supports multiple codes per HTTP status
STATUS_CODES = [
    (200, "OK", "Успех"),
    (201, "CREATED", "Создан ресурс"),
    (202, "ACCEPTED", "Запрос принят"),
    (400, "BAD_REQUEST", "Неверные параметры запроса"),
    (401, "UNAUTHORIZED", "Нет доступа — клиент не известен"),
    (403, "FORBIDDEN", "Нет доступа — нет прав на ресурс"),
    (404, "NOT_FOUND", "Ресурс не найден"),
    (408, "DECISION_TIMEOUT", "Истекло время на принятие решения"),
    (408, "PREVIEW_TRIGGER_TIMEOUT", "Таймаут выполнения preview фазы"),
    (409, "CONFLICT", "Конфликт"),
    (413, "PAYLOAD_TOO_LARGE", "Превышен размер файла"),
    (422, "VALIDATION_FAILED", "Ошибка семантической валидации"),
    (422, "PREVIEW_NOT_SUPPORTED", "Формат файла не поддерживает preview режим"),
    (500, "INTERNAL_ERROR", "Внутренняя ошибка сервера"),
    (501, "NOT_IMPLEMENTED", "Метод не реализован"),
    (503, "SERVICE_UNAVAILABLE", "Сервис временно недоступен"),
    (504, "GATEWAY_TIMEOUT", "Таймаут при вызове внутреннего сервиса"),
]


def get_status(http_code: int, code_name: str | None = None) -> dict | None:
    """
    Returns error code information.

    If code_name is provided, returns matching (http_code, code_name) pair.
    Otherwise, returns the first match for the given http_code.
    """
    for code, name, message in STATUS_CODES:
        if code == http_code:
            if code_name is None or name == code_name:
                return {"code_name": name, "message": message}
    return None


class APIException(HTTPException):
    """
    Defines a custom API exception with proper error format per API spec.
    """

    def __init__(
        self,
        code: int,
        message: str | None = None,
        details: dict | str | None = None,
    ):
        stat = get_status(code)
        message = message or stat["message"] if stat else "Unknown error"

        error_code = stat["code_name"] if stat else "INTERNAL_ERROR"

        super().__init__(
            status_code=code,
            detail={
                "error": {
                    "code": error_code,
                    "message": message,
                    "details": details or {},
                }
            },
        )
