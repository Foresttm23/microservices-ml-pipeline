class SystemException(Exception):
    """Base for all infrastructure/system level errors."""


class MissingHeaderException(SystemException):
    """Raised when a required HTTP header is missing."""


class MissingRequestStateException(SystemException):
    """Raised when FastAPI request state is unexpectedly empty."""


class SessionNotInitializedException(SystemException):
    """Raised when trying to access a database session before it's ready."""
