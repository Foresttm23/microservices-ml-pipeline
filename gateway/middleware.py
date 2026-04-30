from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from gateway.core.config import CORRELATION_ID_HEADER, USER_ID_HEADER
from gateway.utils.context_helpers import (
    build_context_headers,
    extract_correlation_id,
    extract_user_id,
)

# Re-export for backward compatibility (deprecated - use utils.context_helpers instead)
__all__ = ["RequestContextMiddleware", "build_context_headers"]


class RequestContextMiddleware(BaseHTTPMiddleware):
	def __init__(self, app: ASGIApp) -> None:
		super().__init__(app)

	async def dispatch(self, request: Request, call_next) -> Response:
		correlation_id = extract_correlation_id(request)
		user_id = extract_user_id(request)

		request.state.correlation_id = correlation_id
		request.state.user_id = user_id

		with logger.contextualize(correlation_id=correlation_id, user_id=user_id):
			response = await call_next(request)

		response.headers[CORRELATION_ID_HEADER] = correlation_id
		response.headers[USER_ID_HEADER] = user_id
		return response


