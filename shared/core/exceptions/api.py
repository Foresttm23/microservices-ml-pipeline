class BaseAppException(Exception):
    """Base for all application-level errors."""


class BadRequestException(BaseAppException):
    """Raised for HTTP 400."""


class UnauthorizedException(BaseAppException):
    """Raised for HTTP 401."""


class NotFoundException(BaseAppException):
    """Raised for HTTP 404."""
