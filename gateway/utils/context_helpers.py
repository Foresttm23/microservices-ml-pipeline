from fastapi import Request

from shared.core import CORRELATION_ID_HEADER, USER_ID_HEADER
from shared.core.exceptions import MissingRequestStateException


def build_context_headers(request: Request) -> dict[str, str]:
    try:
        return {
            CORRELATION_ID_HEADER: request.state.correlation_id,
            USER_ID_HEADER: request.state.user_id,
        }
    except AttributeError:
        raise MissingRequestStateException("correlation_id or user_id are empty")
