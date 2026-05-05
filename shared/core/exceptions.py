class SessionNotInitializedException(Exception):
    """Raised when a shared client/session is used before startup initialization."""

    def __init__(self, name: str):
        self.name = name
        super().__init__(f"{name} is not initialized")


class MissingHeaderException(Exception):
    """Raised when required data is missing from request.state."""

    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Required state '{name}' is missing.")
