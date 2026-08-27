from shared.core.exceptions.api import (
    BadRequestException,
    NotFoundException,
    UnauthorizedException,
)
from shared.core.exceptions.base import ErrorDefinition
from shared.core.exceptions.system import (
    MissingHeaderException,
    MissingRequestStateException,
    SessionNotInitializedException,
)

GENERAL_ERROR_MAP: dict[type[Exception], ErrorDefinition] = {
    BadRequestException: ErrorDefinition(
        code="bad_request",
        status_code=400,
        detail="The request parameters are invalid.",
    ),
    UnauthorizedException: ErrorDefinition(
        code="unauthorized",
        status_code=401,
        detail="Unauthorized access.",
    ),
    NotFoundException: ErrorDefinition(
        code="not_found",
        status_code=404,
        detail="The requested resource was not found.",
    ),
}


SYSTEM_ERROR_MAP: dict[type[Exception], ErrorDefinition] = {
    MissingHeaderException: ErrorDefinition(
        code="sys_missing_header",
        status_code=400,
        detail="A required security header is missing.",
    ),
    MissingRequestStateException: ErrorDefinition(
        code="sys_internal_state_error",
        status_code=500,
        detail="Internal server state error.",
    ),
    SessionNotInitializedException: ErrorDefinition(
        code="sys_session_error",
        status_code=500,
        detail="Database session was not properly initialized.",
    ),
}
