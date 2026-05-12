from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request

from shared.core.exceptions import UnauthorizedException


async def get_current_user(request: Request) -> UUID:
    """Extract authenticated user ID from request state set by JWTAuthMiddleware."""
    user_id = getattr(request.state, "user_id", "anonymous")

    if user_id == "anonymous":
        raise UnauthorizedException("Authentication required")

    try:
        return UUID(user_id)
    except (ValueError, TypeError) as exc:
        raise UnauthorizedException("Invalid user ID") from exc


CurrentUserIdDep = Annotated[UUID, Depends(get_current_user)]

