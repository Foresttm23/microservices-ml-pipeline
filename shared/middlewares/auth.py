from __future__ import annotations

from typing import Any, Protocol, cast

import jwt
from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class JWTSettingsProtocol(Protocol):
    """Protocol defining required JWT configuration fields."""

    JWT_ENABLED: bool
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_ISSUER: str | None
    JWT_AUDIENCE: str | None
    JWT_USER_ID_CLAIM: str
    JWT_LEEWAY_SECONDS: int
    JWT_PUBLIC_PATHS: list[str]


class JWTAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, settings: JWTSettingsProtocol) -> None:
        self._settings = settings
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> JSONResponse | Any | None:
        # 1. Start as anonymous
        request.state.user_id = "anonymous"

        # Global bypasses
        if not self._settings.JWT_ENABLED or request.method == "OPTIONS":
            return await call_next(request)

        # 2. Try to extract and decode the token
        token = self._extract_bearer_token(request)
        if token:
            return await self._handle_token_auth(request, call_next, token)

        return await self._fallback_to_anonymous(request, call_next)

    async def _handle_token_auth(
        self, request: Request, call_next, token: str
    ) -> JSONResponse | Any:
        try:
            payload = self._decode_token(token)
            user_id = payload.get(self._settings.JWT_USER_ID_CLAIM)

            if user_id:
                request.state.user_id = str(user_id)
                # Success! Contextualize logs and move to the next middleware
                with logger.contextualize(user_id=request.state.user_id):
                    return await call_next(request)

            return await self._fallback_to_anonymous(request, call_next)

        except jwt.PyJWTError as exc:
            logger.warning("JWT validation failed: {}", exc)
            return self._unauthorized("Invalid or expired token")

    async def _fallback_to_anonymous(
        self, request: Request, call_next
    ) -> JSONResponse | Any | None:
        if request.state.user_id == "anonymous":
            if not self._is_public_path(request.url.path):
                return self._unauthorized("Authentication required for this resource")

        return await call_next(request)

    def _decode_token(self, token: str) -> dict[str, object]:
        audience = self._settings.JWT_AUDIENCE
        issuer = self._settings.JWT_ISSUER
        leeway = float(self._settings.JWT_LEEWAY_SECONDS)
        options = None if audience else cast(Any, {"verify_aud": False})

        return jwt.decode(
            token,
            key=self._settings.JWT_SECRET_KEY,
            algorithms=[self._settings.JWT_ALGORITHM],
            leeway=leeway,
            issuer=issuer,
            audience=audience,
            options=options,
        )

    def _extract_bearer_token(self, request: Request) -> str | None:
        auth_header = request.headers.get("authorization")
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        return parts[1]

    def _is_public_path(self, path: str) -> bool:
        return any(
            path.startswith(prefix) for prefix in self._settings.JWT_PUBLIC_PATHS
        )

    @staticmethod
    def _unauthorized(message: str) -> JSONResponse:
        return JSONResponse(status_code=401, content={"detail": message})
