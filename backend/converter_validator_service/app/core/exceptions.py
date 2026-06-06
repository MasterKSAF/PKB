from fastapi import HTTPException, status


class ConverterValidatorError(HTTPException):
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: dict | None = None,
    ):
        self.error_code = error_code
        self.details = details or {}
        super().__init__(
            status_code=status_code,
            detail={
                "error": {
                    "code": error_code,
                    "message": message,
                    "details": self.details,
                }
            },
        )


class ConversionFailedError(ConverterValidatorError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="CONVERSION_FAILED",
            message=message,
            details=details,
        )


class ValidationFailedError(ConverterValidatorError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_FAILED",
            message=message,
            details=details,
        )
