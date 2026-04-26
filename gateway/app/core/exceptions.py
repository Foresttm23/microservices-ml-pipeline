class SessionNotInitializedException(Exception):
    """Raised when a shared client/session is used before startup initialization."""

    def __init__(self, session_name: str):
        self.session_name = session_name
        super().__init__(f"{session_name} is not initialized")
