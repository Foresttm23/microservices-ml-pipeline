from typing import Annotated

from fastapi import Depends

from orchestrator.repositories.log_repository import LogRepository
from orchestrator.repositories.query_repository import QueryRepository
from orchestrator.repositories.response_repository import ResponseRepository
from shared.dependencies import DBSessionDep


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
