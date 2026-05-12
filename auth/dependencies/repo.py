from typing import Annotated

from fastapi import Depends

from auth.repositories.token_repository import RefreshTokenRepository
from auth.repositories.user_repository import UserRepository
from shared.dependencies import DBSessionDep


async def get_user_repo(session: DBSessionDep) -> UserRepository:
    return UserRepository(session)


UserRepoDep = Annotated[UserRepository, Depends(get_user_repo)]


async def get_token_repo(session: DBSessionDep) -> RefreshTokenRepository:
    return RefreshTokenRepository(session)


TokenRepoDep = Annotated[RefreshTokenRepository, Depends(get_token_repo)]
