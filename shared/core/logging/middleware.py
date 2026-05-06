from uuid import uuid4

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from shared.core.config import (
    CORRELATION_ID_HEADER,
    get_shared_settings,
)


class LoggingContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        self._settings = get_shared_settings()
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        correlation_id = str(uuid4())
        user_id = self._extract_user_id(request, debug=self._settings.DEBUG)

        request.state.correlation_id = correlation_id
        request.state.user_id = user_id

        with logger.contextualize(correlation_id=correlation_id, user_id=user_id):
            response = await call_next(request)

            response.headers[CORRELATION_ID_HEADER] = correlation_id

        return response

    @staticmethod
    def _extract_user_id(request: Request, *, debug: bool) -> str:
        """
        Receives a request object and extracts the user id from it.
        If JWT middleware isnt implemented yet, it will return "anonymous" as user id, allowing shared chat for non-logged in users.
        Has a feature, where users will have shared chat if they are not logged in. user_id = "anonymous"

        In debug mode, accepts user_id from query params for testing purposes, allowing developers to simulate different users without needing authentication.
        """
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return user_id

        if debug:  # Temporary workaround for testing in debug mode, allowing user_id to be passed as a query parameter
            query_user_id = request.query_params.get("user_id")
            if query_user_id:
                return query_user_id

        # 3. Fallback
        return "anonymous"
