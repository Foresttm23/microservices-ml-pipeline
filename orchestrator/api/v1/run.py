import json
from json import JSONDecodeError
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from loguru import logger

from orchestrator.core.dependencies import get_db_session
from orchestrator.services.query_service import QueryService
from shared.core import CORRELATION_ID_HEADER, USER_ID_HEADER, MissingHeaderException

router = APIRouter()


def extract_value_from_header(request: Request, header_name: str) -> str:
    """Extract UUID from a required header."""
    header_value = request.headers.get(header_name)
    if not header_value:
        raise MissingHeaderException(header_name)

    return header_value


def extract_uuid_from_header(request: Request, header_name: str) -> UUID:
    """Extract UUID from a required header."""
    header_value = extract_value_from_header(request, header_name)

    try:
        return UUID(header_value)
    except ValueError:
        # Todo raise error and a handler. Gateway should always be the source of truth for correlation_id and user_id and should always pass valid UUIDs.
        raise


@router.post("/api/run/{pipeline_id}")
async def run_pipeline(
    pipeline_id: str,
    request: Request,
    session=Depends(get_db_session),
) -> Response:
    """Accept a pipeline run request, create a task, and return 202 Accepted."""
    logger.info(f"Received pipeline run request for {pipeline_id}")

    try:
        correlation_id = extract_uuid_from_header(request, CORRELATION_ID_HEADER)
        user_id = extract_value_from_header(request, USER_ID_HEADER)

        try:
            body = await request.json()
            message = body.get("message", "")
        except JSONDecodeError:
            content = await request.body()
            message = content.decode("utf-8") if content else ""

        if not message:
            raise HTTPException(
                status_code=400, detail="Message is required"
            )  # todo implement a generic exception and handler for this type of errors.

        service = QueryService(session)
        query_id = await service.create_and_enqueue_task(
            correlation_id=correlation_id,
            user_id=user_id,
            message=message,
            pipeline_id=pipeline_id,
        )

        return Response(
            content=json.dumps(
                {
                    "status": "accepted",
                    "query_id": str(query_id),
                    "correlation_id": str(correlation_id),
                    "message": "Task enqueued for processing",
                }
            ),
            status_code=202,
            media_type="application/json",
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error processing pipeline run: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
