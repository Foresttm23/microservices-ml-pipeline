from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from orchestrator.db.models import QueryModel
from orchestrator.schemas.query import QueryDetailEntity, QueryEntity
from shared.repositories import BaseRepository


class QueryRepository(BaseRepository[QueryModel, QueryEntity]):
    """Repository for Query entities."""

    def __init__(self, session: AsyncSession):
        super().__init__(
            session=session, model_class=QueryModel, entity_class=QueryEntity
        )


    async def get_chats_paginated(
        self, user_id: str, skip: int, limit: int
    ) -> tuple[list[QueryEntity], int]:
        subq = (
            select(
                QueryModel.interaction_id,
                func.min(QueryModel.created_at).label("first_msg_time"),
            )
            .where(QueryModel.user_id == user_id)
            .group_by(QueryModel.interaction_id)
            .subquery()
        )

        stmt = (
            select(QueryModel)
            .join(
                subq,
                (QueryModel.interaction_id == subq.c.interaction_id)
                & (QueryModel.created_at == subq.c.first_msg_time),
            )
            .order_by(QueryModel.created_at.desc())
        )
        return await self._get_paginated(stmt, skip, limit)

    async def get_chat_messages_paginated(
        self, user_id: str, interaction_id: UUID, skip: int, limit: int
    ) -> tuple[list[QueryDetailEntity], int]:
        from sqlalchemy.orm import selectinload

        stmt = (
            select(QueryModel)
            .where(
                QueryModel.user_id == user_id,
                QueryModel.interaction_id == interaction_id,
            )
            .options(selectinload(QueryModel.responses))
            .order_by(QueryModel.created_at.asc())
        )
        total_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(total_stmt)).scalar_one()

        paginated_stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(paginated_stmt)
        items = [
            QueryDetailEntity.model_validate(model) for model in result.scalars().all()
        ]
        return items, total
