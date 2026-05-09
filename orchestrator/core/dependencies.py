"""Dependency injection for orchestrator service."""

from typing import Annotated, AsyncGenerator
from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from orchestrator.db.session import db_session_manager
from orchestrator.repositories.log_repository import LogRepository
from orchestrator.repositories.query_repository import QueryRepository
from orchestrator.repositories.response_repository import ResponseRepository
from shared.core import CORRELATION_ID_HEADER, USER_ID_HEADER


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a database session for dependency injection.

    Yields:
        AsyncSession: Active database session
    """
    async with db_session_manager.session() as session:
        yield session


DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


async def get_query_repo(session: DBSessionDep) -> QueryRepository:
    """Provide QueryRepository dependency."""
    return QueryRepository(session)


QueryRepoDep = Annotated[QueryRepository, Depends(get_query_repo)]


async def get_response_repo(session: DBSessionDep) -> ResponseRepository:
    """Provide ResponseRepository dependency."""
    return ResponseRepository(session)


ResponseRepoDep = Annotated[ResponseRepository, Depends(get_response_repo)]


async def get_log_repo(session: DBSessionDep) -> LogRepository:
    """Provide LogRepository dependency."""
    return LogRepository(session)


LogRepoDep = Annotated[LogRepository, Depends(get_log_repo)]


CorrelationIdDep = Annotated[UUID, Header(..., alias=CORRELATION_ID_HEADER)]
UserIdDep = Annotated[str, Header(..., alias=USER_ID_HEADER)]
