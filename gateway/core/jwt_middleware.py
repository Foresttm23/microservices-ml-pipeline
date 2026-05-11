from __future__ import annotations

from typing import Any, cast

import jwt
from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from gateway.core.config import get_settings


class JWTAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        self._settings = get_settings()
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        if not self._settings.JWT_ENABLED:
            return await call_next(request)

        if request.method == "OPTIONS" or self._is_public_path(request.url.path):
            return await call_next(request)

        token = self._extract_bearer_token(request)
        if not token:
            return self._unauthorized("Missing or invalid Authorization header")

        try:
            payload = self._decode_token(token)
        except jwt.PyJWTError as exc:
            logger.warning("JWT validation failed: {}", exc)
            return self._unauthorized("Invalid or expired token")

        user_id = payload.get(self._settings.JWT_USER_ID_CLAIM)
        if not user_id:
            return self._unauthorized("Missing user id claim")

        request.state.user_id = str(user_id)
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
