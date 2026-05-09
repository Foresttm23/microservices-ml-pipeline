from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from orchestrator.db.models import LogModel, QueryModel, ResponseModel
from orchestrator.schemas.query import QueryEntity
from shared.repositories import BaseRepository


class QueryRepository(BaseRepository[QueryModel, QueryEntity]):
    """Repository for Query entities."""

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model_class=QueryModel, entity_class=QueryEntity)

    async def add(self, query: QueryModel) -> QueryModel:
        """Just persistence. No business logic."""
        self.session.add(query)
        await self.session.flush()
        return query

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

    async def get_model_by_id(self, query_id: UUID) -> QueryModel | None:
        stmt = select(QueryModel).where(QueryModel.id == query_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[QueryEntity]:
        stmt = select(QueryModel).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return [self.map_model_to_entity(model) for model in result.scalars().all()]

    async def create(self, entity: QueryEntity) -> QueryEntity:
        raise NotImplementedError("Use QueryModel.create and add()")

    async def update(self, entity_id: UUID, entity: QueryEntity) -> QueryEntity | None:
        raise NotImplementedError("Query updates should be performed via domain methods")

    async def delete(self, entity_id: UUID) -> bool:
        raise NotImplementedError("Query deletion is not supported")

    async def add_response(self, response: ResponseModel) -> ResponseModel:
        self.session.add(response)
        await self.session.flush()
        return response

    async def add_log(self, log_entry: LogModel) -> LogModel:
        self.session.add(log_entry)
        await self.session.flush()
        return log_entry

