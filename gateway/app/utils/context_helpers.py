from uuid import uuid4

from fastapi import Request

from ..core.config import CORRELATION_ID_HEADER, USER_ID_HEADER


def extract_correlation_id(request: Request) -> str:
    """Extract or generate correlation ID from request headers."""
    return request.headers.get(CORRELATION_ID_HEADER) or str(uuid4())


def extract_user_id(request: Request) -> str:
    """
    Temporary user identity source until auth is added.
    """
    return (
        request.headers.get(USER_ID_HEADER)
        or request.query_params.get("user_id")
        or "anonymous"
    )


def build_context_headers(request: Request) -> dict[str, str]:
    correlation_id = getattr(
        request.state, "correlation_id", None
    ) or extract_correlation_id(request)
    user_id = getattr(request.state, "user_id", None) or extract_user_id(request)
    return {
        CORRELATION_ID_HEADER: correlation_id,
        USER_ID_HEADER: user_id,
    }
