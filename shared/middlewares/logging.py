from __future__ import annotations

from urllib.parse import parse_qs
from uuid import uuid4

from loguru import logger
from starlette.types import ASGIApp, Receive, Scope, Send

from shared.core.config import (
    CORRELATION_ID_HEADER,
    get_shared_settings,
)


class LoggingContextMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self._settings = get_shared_settings()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # 1. Extract Correlation ID from headers
        headers = dict(scope.get("headers", []))
        correlation_id = headers.get(CORRELATION_ID_HEADER.lower().encode())
        correlation_id = correlation_id.decode() if correlation_id else str(uuid4())

        # 2. Setup state
        scope.setdefault("state", {})
        scope["state"]["correlation_id"] = correlation_id

        # 3. Extract User ID (Handling debug query params and state)
        user_id = self._extract_user_id(scope, debug=self._settings.DEBUG)
        scope["state"]["user_id"] = user_id

        # 4. Define the send wrapper to inject the header back into the response
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Convert list of tuples to a list so we can modify it
                response_headers = list(message.get("headers", []))

                # Add the correlation ID header
                response_headers.append(
                    (CORRELATION_ID_HEADER.encode().lower(), correlation_id.encode())
                )
                message["headers"] = response_headers

            await send(message)

        # 5. Execute with contextual logging
        with logger.contextualize(correlation_id=correlation_id, user_id=user_id):
            await self.app(scope, receive, send_wrapper)

    def _extract_user_id(self, scope: Scope, *, debug: bool) -> str:
        # Debug logic: check query string
        if debug:
            query_string = scope.get("query_string", b"").decode()
            params = parse_qs(query_string)
            if "user_id" in params:
                return params["user_id"][0]

        # Fallback to state (populated by JWT middleware if it ran first)
        return scope["state"].get("user_id", "anonymous")
