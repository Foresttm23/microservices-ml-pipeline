from shared.core.exceptions.base import BaseAppException


class SessionNotInitializedException(BaseAppException):
    """Raised when a shared client/session is used before startup initialization."""

    def __init__(self, name: str):
        self.name = name
        # We pass the status code (503) and the formatted message to the base
        super().__init__(
            detail=f"Service dependency not ready: {name}", status_code=503
        )


class MissingHeaderException(BaseAppException):
    """Raised when required data is missing from request.state."""

    def __init__(self, name: str):
        self.name = name
        super().__init__(
            detail=f"Internal configuration error: Missing {name} header",
            status_code=500,
        )


class MissingRequestStateException(BaseAppException):
    """Raised when request.state is missing required context data."""

    def __init__(self, name: str):
        self.name = name
        super().__init__(
            detail=f"Internal configuration error: Missing request state '{name}'",
            status_code=500,
        )
