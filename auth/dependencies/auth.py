from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request

from auth.dependencies.service import AuthServiceDep
from shared.core.exceptions import UnauthorizedException


async def get_current_user(request: Request, auth_service: AuthServiceDep) -> UUID:
    token = _extract_bearer_token(request)
    if not token:
        raise UnauthorizedException("Missing token")

    try:
        payload = auth_service.decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedException("Invalid token claim")
        return UUID(str(user_id))
    except (ValueError, Exception) as exc:
        raise UnauthorizedException("Invalid or expired token") from exc


CurrentUserIdDep = Annotated[UUID, Depends(get_current_user)]


def _extract_bearer_token(request: Request) -> str | None:
    auth_header = request.headers.get("authorization")
    if not auth_header:
        return None

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1]
