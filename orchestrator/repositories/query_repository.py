from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from orchestrator.db.models import QueryModel


class QueryRepository:
    """Repository for Query entities."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        correlation_id: UUID,
        user_id: str,
        message: str,
        state: str = "PENDING",  # Todo make this str enum instead.
    ) -> QueryModel:
        """Create a new query record."""
        query = QueryModel(
            user_id=user_id,
            correlation_id=correlation_id,
            interaction_id=uuid4(),
            message=message,
            state=state,
        )
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

    async def update_state(self, query_id: UUID, state: str) -> QueryModel | None:
        """Update query state."""
        query = await self.get_by_id(query_id)
        if query:
            query.state = state
        return query
