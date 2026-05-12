from typing import Annotated
from fastapi import Depends
from auth.services.auth_service import AuthService
from auth.dependencies.repo import UserRepoDep, TokenRepoDep
from shared.dependencies import DBSessionDep

async def get_auth_service(
    session: DBSessionDep,
    user_repo: UserRepoDep,
    token_repo: TokenRepoDep
) -> AuthService:
    return AuthService(session=session, user_repo=user_repo, token_repo=token_repo)

AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]