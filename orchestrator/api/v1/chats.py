from uuid import UUID

from fastapi import APIRouter, Query
from starlette import status

from orchestrator.dependencies.service import QueryServiceDep
from orchestrator.schemas.query import QueryDetailResponse, QueryListResponse
from shared.dependencies import UserIdDep
from shared.schemas.base import PaginatedResponse

router = APIRouter(prefix="/api/chats", tags=["chats"])


@router.get(
    "",
    response_model=PaginatedResponse[QueryListResponse],
    status_code=status.HTTP_200_OK,
)
async def get_user_chats(
    user_id: UserIdDep,
    service: QueryServiceDep,
    skip: int = Query(0, ge=0),
    limit: int | None = Query(None, gt=0),
):
    """
    Returns a paginated list of distinct chats (interactions) for the user.
    """
    items, total = await service.get_user_chats(user_id, skip=skip, limit=limit)
    return PaginatedResponse(
        items=[QueryListResponse.model_validate(item) for item in items],
        total=total,
        skip=skip,
        limit=limit or len(items),
    )


@router.get(
    "/{interaction_id}/messages",
    response_model=PaginatedResponse[QueryDetailResponse],
    status_code=status.HTTP_200_OK,
)
async def get_chat_messages(
    interaction_id: UUID,
    user_id: UserIdDep,
    service: QueryServiceDep,
    skip: int = Query(0, ge=0),
    limit: int | None = Query(None, gt=0),
):
    """
    Returns a paginated list of messages (queries) for a specific chat.
    """
    items, total = await service.get_chat_messages(
        user_id, interaction_id, skip=skip, limit=limit
    )
    return PaginatedResponse(
        items=[QueryDetailResponse.model_validate(item) for item in items],
        total=total,
        skip=skip,
        limit=limit or len(items),
    )
