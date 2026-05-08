from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from orchestrator.db.models import QueryModel
from orchestrator.schemas.query import QueryEntity
from shared.repositories import BaseRepository


class QueryRepository(BaseRepository[QueryModel, QueryEntity]):
    """Repository for Query entities."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.model_class: type[QueryModel] = QueryModel
        self.entity_class: type[QueryEntity] = QueryEntity

    async def add(self, query: QueryModel) -> QueryModel:
        """Just persistence. No business logic."""
        self.session.add(query)
        await self.session.flush()
        return query

    async def get_by_correlation_id(self, correlation_id: UUID) -> QueryModel | None:
        """Get a query by correlation ID."""
        stmt = select(QueryModel).where(QueryModel.correlation_id == correlation_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, query_id: UUID) -> QueryModel | None:
        """Get a query by ID."""
        stmt = select(QueryModel).where(QueryModel.id == query_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

