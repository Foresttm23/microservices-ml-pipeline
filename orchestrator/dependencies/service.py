from typing import Annotated

from fastapi import Depends

from orchestrator.dependencies.repo import QueryRepoDep
from orchestrator.services.query_service import QueryService
from shared.dependencies import DBSessionDep


def get_query_service(session: DBSessionDep, repo: QueryRepoDep) -> QueryService:
    return QueryService(session, repo)


QueryServiceDep = Annotated[QueryService, Depends(get_query_service)]
