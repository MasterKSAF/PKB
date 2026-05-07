#
#  Forming unified API responses
#
from fastapi import HTTPException


def get_status(code: int) -> dict | None:
    """
    Возвращает описание кодов запросов
    """


    status_codes = {
        200: {
            "code_name": "OK",
            "message": "Успех",
            # "comment": None
        },
        201: {
            "code_name": "CREATED",
            "message": "Создан ресурс",
            # "comment": None
        },
        202: {
            "code_name": "ACCEPTED",
            "message": "Запрос принят",
            # "comment": "Когда нет немедленного ответа, например, поставить документ на обработку."
        },
        400: {
            "code_name": "BAD_REQUEST",
            "message": "Неверные параметры",
            # "comment": None
        },
        401: {
            "code_name": "UNAUTHORIZED",
            "message": "Нет доступа - клиент не известен",
            # "comment": None
        },
        403: {
            "code_name": "FORBIDDEN",
            "message": "Нет доступа - нет прав на ресурс, клиент известен",
            # "comment": None
        },
        404: {
                "code_name": "NOT_FOUND",
                "message": "Не найдено, нет такого адреса/ресурса",
                # "comment": None
            },
        422: {
            "code_name": "UNPROCESSABLE_FORMAT",
            "message": "Ошибка валидации/ семантическая ошибка",
            # "comment": None
        },
        500: {
            "code_name": "INTERNAL_SERVER_ERROR",
            "message": "Внутренняя ошибка сервера",
            # "comment": None
        },
        501: {
            "code_name": "NOT_IMPLEMENTED",
            "message": "Метод не внедрён",
            # "comment": "GET and HEAD не должны возвращать этот код"
        }
    }
    if status_codes.get(code) is not None:
        return status_codes.get(code)
    else:
        return None


class APIException(HTTPException):
    """"
    Defines a custom API exception
    """

    def __init__(
            self,
            code: int,
            message: str | None = None,
            details: dict | str | None = None,
    ):
        stat = get_status(code)
        message = message or stat["message"]

        super().__init__(
            status_code=code,
            detail={
                "code": code,
                "code_name": stat["code_name"],
                "message": message,
                "details": details
            }
        )