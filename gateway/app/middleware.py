from uuid import uuid4

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

CORRELATION_ID_HEADER = "X-Correlation-ID"
USER_ID_HEADER = "X-User-ID"


def _extract_correlation_id(request: Request) -> str:
	return request.headers.get(CORRELATION_ID_HEADER) or str(uuid4())


def _extract_user_id(request: Request) -> str:
	# Temporary user identity source until auth is added.
	return request.headers.get(USER_ID_HEADER) or request.query_params.get("user_id") or "anonymous"


def build_context_headers(request: Request) -> dict[str, str]:
	correlation_id = getattr(request.state, "correlation_id", None) or _extract_correlation_id(
		request
	)
	user_id = getattr(request.state, "user_id", None) or _extract_user_id(request)
	return {
		CORRELATION_ID_HEADER: correlation_id,
		USER_ID_HEADER: user_id,
	}


class RequestContextMiddleware(BaseHTTPMiddleware):
	def __init__(self, app: ASGIApp) -> None:
		super().__init__(app)

	async def dispatch(self, request: Request, call_next) -> Response:
		correlation_id = _extract_correlation_id(request)
		user_id = _extract_user_id(request)

		request.state.correlation_id = correlation_id
		request.state.user_id = user_id

		with logger.contextualize(correlation_id=correlation_id, user_id=user_id):
			response = await call_next(request)

		response.headers[CORRELATION_ID_HEADER] = correlation_id
		response.headers[USER_ID_HEADER] = user_id
		return response


