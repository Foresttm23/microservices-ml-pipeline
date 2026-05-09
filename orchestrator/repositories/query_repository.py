from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from orchestrator.db.models import QueryModel
from orchestrator.schemas.query import QueryEntity
from shared.repositories import BaseRepository


class QueryRepository(BaseRepository[QueryModel, QueryEntity]):
    """Repository for Query entities."""

    def __init__(self, session: AsyncSession):
        super().__init__(
            session=session, model_class=QueryModel, entity_class=QueryEntity
        )

    async def get_by_correlation_id(self, correlation_id: UUID) -> QueryEntity | None:
        stmt = select(QueryModel).where(QueryModel.correlation_id == correlation_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self.map_model_to_entity(model) if model else None

    async def get_by_id(self, query_id: UUID) -> QueryEntity | None:
        stmt = select(QueryModel).where(QueryModel.id == query_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self.map_model_to_entity(model) if model else None

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[QueryEntity]:
        stmt = select(QueryModel).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return [self.map_model_to_entity(model) for model in result.scalars().all()]

    async def create(self, entity: QueryEntity) -> QueryEntity:
        raise NotImplementedError("Use QueryEntity.create() and save()")

    async def update(self, entity_id: UUID, entity: QueryEntity) -> QueryEntity | None:
        raise NotImplementedError(
            "Query updates should be performed via domain methods"
        )

    async def delete(self, entity_id: UUID) -> bool:
        raise NotImplementedError("Query deletion is not supported")

    async def save(self, entity: QueryEntity) -> QueryEntity:
        """
        Persist a query entity.

        Creates a new QueryModel or updates existing one.
        """
        existing_model = await self.session.get(QueryModel, entity.id)

        if existing_model:
            # Update existing model
            existing_model.state = entity.state
            existing_model.message = entity.message
        else:
            # Create new model
            new_model = QueryModel(
                id=entity.id,
                user_id=entity.user_id,
                correlation_id=entity.correlation_id,
                interaction_id=entity.interaction_id,
                message=entity.message,
                state=entity.state,
            )
            self.session.add(new_model)

        await self.session.flush()
        return entity


