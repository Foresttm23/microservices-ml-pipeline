from shared.core.exceptions.base import BaseAppException


class BadRequestException(BaseAppException):
    """Raised for HTTP 400 Bad Request errors."""

    def __init__(self, detail: str = "The request parameters are invalid."):
        super().__init__(detail=detail, status_code=400)


class UnauthorizedException(BaseAppException):
    """Raised for HTTP 401 Unauthorized errors."""

    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(detail=detail, status_code=401)


class NotFoundException(BaseAppException):
    """Raised for HTTP 404 Not Found errors."""

    def __init__(self, detail: str = "Resource not found"):
        super().__init__(detail=detail, status_code=404)
