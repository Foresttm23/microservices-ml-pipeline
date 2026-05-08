
from fastapi import APIRouter
from loguru import logger
from starlette import status

from orchestrator.core.dependencies import (
    CorrelationIdDep,
    DBSessionDep,
    QueryRepoDep,
    UserIdDep,
)
from orchestrator.services.query_service import QueryService
from shared.schemas import PipelineRequest, PipelineResponse

router = APIRouter()


@router.post("/api/run/{pipeline_id}", status_code=status.HTTP_202_ACCEPTED)
async def run_pipeline(
    pipeline_id: str,
    payload: PipelineRequest,
    correlation_id: CorrelationIdDep,
    user_id: UserIdDep,
    session: DBSessionDep,
    query_repo: QueryRepoDep,
) -> PipelineResponse:
    """
    Accepts a pipeline request.
    FastAPI dependencies now handle validation and header extraction.
    """
    logger.info("Processing pipeline request")

    service = QueryService(session, query_repo)
    query_id = await service.create_and_enqueue_task(
        correlation_id=correlation_id,
        user_id=user_id,
        message=payload.message,
        pipeline_id=pipeline_id,
    )

    return PipelineResponse(
        status="accepted",
        query_id=query_id,
        correlation_id=correlation_id,
        message="Task enqueued",
    )
