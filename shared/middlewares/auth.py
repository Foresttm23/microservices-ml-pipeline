from __future__ import annotations

from typing import Any, Protocol, cast

import jwt
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.types import ASGIApp, Receive, Scope, Send


# TODO move JWTSettingsProtocol to protocols and decode_jwt_token to utils

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


def decode_jwt_token(token: str, settings: JWTSettingsProtocol) -> dict[str, object]:
    audience = settings.JWT_AUDIENCE
    issuer = settings.JWT_ISSUER
    leeway = float(settings.JWT_LEEWAY_SECONDS)
    options = None if audience else cast(Any, {"verify_aud": False})

    return jwt.decode(
        token,
        key=settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        leeway=leeway,
        issuer=issuer,
        audience=audience,
        options=options,
    )


class JWTAuthMiddleware:
    def __init__(self, app: ASGIApp, settings: JWTSettingsProtocol) -> None:
        self.app = app
        self.settings = settings

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # Only process HTTP requests
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Initialize state if not present (equivalent to request.state)
        scope.setdefault("state", {})
        scope["state"]["user_id"] = "anonymous"

        # 1. Global bypasses
        method = scope.get("method", "")
        if not self.settings.JWT_ENABLED or method == "OPTIONS":
            await self.app(scope, receive, send)
            return

        # 2. Path matching
        path = scope.get("path", "")
        is_public = any(path.startswith(p) for p in self.settings.JWT_PUBLIC_PATHS)

        # 3. Extract and validate token
        token = self._get_bearer_token(scope)

        if token:
            try:
                payload = decode_jwt_token(token, self.settings)
                user_id = payload.get(self.settings.JWT_USER_ID_CLAIM)

                if user_id:
                    scope["state"]["user_id"] = str(user_id)
                    with logger.contextualize(user_id=scope["state"]["user_id"]):
                        await self.app(scope, receive, send)
                    return

            except jwt.PyJWTError as exc:
                logger.warning("JWT validation failed: {}", exc)
                response = self._unauthorized("Invalid or expired token")
                await response(scope, receive, send)
                return

        # 4. Final check for private paths
        if not is_public and scope["state"]["user_id"] == "anonymous":
            response = self._unauthorized("Authentication required for this resource")
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)

    def _get_bearer_token(self, scope: Scope) -> str | None:
        headers = scope.get("headers", [])
        for key, value in headers:
            if key == b"authorization":
                try:
                    auth_str = value.decode("latin-1")
                    parts = auth_str.split()
                    if len(parts) == 2 and parts[0].lower() == "bearer":
                        return parts[1]
                except UnicodeDecodeError:
                    return None
        return None

    @staticmethod
    def _unauthorized(message: str) -> JSONResponse:
        return JSONResponse(status_code=401, content={"detail": message})
