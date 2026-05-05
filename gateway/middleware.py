from uuid import uuid4

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from gateway.utils.context_helpers import (
    extract_user_id,
)
from shared.core import get_shared_settings


class RequestContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        shared_settings = get_shared_settings()

        correlation_id = str(uuid4())
        user_id = extract_user_id(request, debug=shared_settings.DEBUG)

        request.state.correlation_id = correlation_id
        request.state.user_id = user_id

        with logger.contextualize(correlation_id=correlation_id, user_id=user_id):
            response = await call_next(request)

        # This is the internal middleware, so every method will extract from the state attr, while passing header downstream
        # response.headers[CORRELATION_ID_HEADER] = correlation_id
        # response.headers[USER_ID_HEADER] = user_id
        return response
