from shared.core.exceptions import ErrorDefinition


class AuthServiceError(Exception):
    """Base class for auth service errors."""


class EmailAlreadyRegistered(AuthServiceError):
    """Raised when a user tries to register an existing email."""


class InvalidCredentials(AuthServiceError):
    """Raised when user credentials are invalid."""


class InvalidRefreshToken(AuthServiceError):
    """Raised when a refresh token is malformed or has wrong type."""


class RefreshTokenNotFound(AuthServiceError):
    """Raised when a refresh token is not found in storage."""


class RefreshTokenRevoked(AuthServiceError):
    """Raised when a refresh token is already revoked."""


class RefreshTokenExpired(AuthServiceError):
    """Raised when a refresh token is expired."""


class InvalidTokenClaims(AuthServiceError):
    """Raised when a token is missing required claims."""


AUTH_ERROR_MAP = {
    EmailAlreadyRegistered: ErrorDefinition(
        code="auth_email_exists",
        status_code=400,
        detail="An account with this email already exists.",
    ),
    InvalidCredentials: ErrorDefinition(
        code="auth_invalid_credentials",
        status_code=401,
        detail="Invalid credentials",
    ),
    InvalidRefreshToken: ErrorDefinition(
        code="auth_invalid_refresh_token",
        status_code=401,
        detail="Invalid refresh token",
    ),
    RefreshTokenNotFound: ErrorDefinition(
        code="auth_refresh_not_found",
        status_code=401,
        detail="Refresh token not found",
    ),
    RefreshTokenRevoked: ErrorDefinition(
        code="auth_refresh_revoked",
        status_code=401,
        detail="Refresh token revoked",
    ),
    RefreshTokenExpired: ErrorDefinition(
        code="auth_refresh_expired",
        status_code=401,
        detail="Refresh token expired",
    ),
    InvalidTokenClaims: ErrorDefinition(
        code="auth_invalid_token_claims",
        status_code=401,
        detail="Invalid refresh token",
    ),
}
