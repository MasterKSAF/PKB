"""
Forming unified API responses
"""

from fastapi import HTTPException


def get_status(code: int) -> dict | None:
    """
    Returns error code information.
    """
    status_codes = {
        200: {"code_name": "OK", "message": "Успех"},
        201: {"code_name": "CREATED", "message": "Создан ресурс"},
        202: {"code_name": "ACCEPTED", "message": "Запрос принят"},
        400: {"code_name": "BAD_REQUEST", "message": "Неверные параметры запроса"},
        401: {
            "code_name": "UNAUTHORIZED",
            "message": "Нет доступа — клиент не известен",
        },
        403: {"code_name": "FORBIDDEN", "message": "Нет доступа — нет прав на ресурс"},
        404: {"code_name": "NOT_FOUND", "message": "Ресурс не найден"},
        409: {"code_name": "CONFLICT", "message": "Конфликт"},
        413: {"code_name": "PAYLOAD_TOO_LARGE", "message": "Превышен размер файла"},
        422: {
            "code_name": "VALIDATION_FAILED",
            "message": "Ошибка семантической валидации",
        },
        500: {"code_name": "INTERNAL_ERROR", "message": "Внутренняя ошибка сервера"},
        501: {"code_name": "NOT_IMPLEMENTED", "message": "Метод не реализован"},
        503: {
            "code_name": "SERVICE_UNAVAILABLE",
            "message": "Сервис временно недоступен",
        },
        504: {
            "code_name": "GATEWAY_TIMEOUT",
            "message": "Таймаут при вызове внутреннего сервиса",
        },
    }
    return status_codes.get(code)


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
