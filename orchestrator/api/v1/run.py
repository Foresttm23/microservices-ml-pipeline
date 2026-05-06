from uuid import UUID

from fastapi import APIRouter, Depends, Header
from loguru import logger
from starlette import status

from orchestrator.core.dependencies import get_db_session
from orchestrator.services.query_service import QueryService
from shared.core import CORRELATION_ID_HEADER, USER_ID_HEADER
from shared.schemas import PipelineRequest, PipelineResponse

router = APIRouter()


@router.post("/api/run/{pipeline_id}", status_code=status.HTTP_202_OK)
async def run_pipeline(
    pipeline_id: str,
    payload: PipelineRequest,
    correlation_id: UUID = Header(..., alias=CORRELATION_ID_HEADER),
    user_id: str = Header(..., alias=USER_ID_HEADER),
    session=Depends(get_db_session),
) -> PipelineResponse:
    """
    Accepts a pipeline request.
    Validation and header extraction are now handled by FastAPI dependencies.
    """
    logger.info(f"Processing pipeline {pipeline_id} for user {user_id}")

    service = QueryService(session)
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
