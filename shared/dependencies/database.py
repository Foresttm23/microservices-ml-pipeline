from typing import Annotated, AsyncGenerator

from shared.db.session import db_session_manager
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a database session for dependency injection.

    Yields:
        AsyncSession: Active database session
    """
    async with db_session_manager.session() as session:
        yield session


DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]
