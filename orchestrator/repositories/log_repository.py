from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from orchestrator.db.models import LogModel
from orchestrator.schemas.log import LogEntity
from shared.repositories import BaseRepository


class LogRepository(BaseRepository[LogModel, LogEntity]):
    """Repository for Log entities."""

    def __init__(self, session: AsyncSession):
        super().__init__(
            session=session, model_class=LogModel, entity_class=LogEntity
        )

    async def get_by_id(self, log_id: UUID) -> LogEntity | None:
        """Fetch a log entity by its ID."""
        stmt = select(LogModel).where(LogModel.id == log_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self.map_model_to_entity(model) if model else None

    async def get_by_query_id(self, query_id: UUID) -> list[LogEntity]:
        """Fetch all logs for a given query."""
        stmt = select(LogModel).where(LogModel.query_id == query_id)
        result = await self.session.execute(stmt)
        return [self.map_model_to_entity(model) for model in result.scalars().all()]

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[LogEntity]:
        """Fetch all logs with pagination."""
        stmt = select(LogModel).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return [self.map_model_to_entity(model) for model in result.scalars().all()]

    async def create(self, entity: LogEntity) -> LogEntity:
        raise NotImplementedError("Use LogEntity.create() and save()")

    async def update(self, entity_id: UUID, entity: LogEntity) -> LogEntity | None:
        raise NotImplementedError(
            "Log updates should be performed via entity methods"
        )

    async def delete(self, entity_id: UUID) -> bool:
        raise NotImplementedError("Log deletion is not supported")

    async def save(self, entity: LogEntity) -> LogEntity:
        """
        Persist a log entity.

        Creates a new LogModel or updates existing one.
        """
        existing_model = await self.session.get(LogModel, entity.id)

        if existing_model:
            # Update existing model
            existing_model.message = entity.message
            existing_model.metadata_ = entity.metadata_
        else:
            # Create new model
            new_model = LogModel(
                id=entity.id,
                query_id=entity.query_id,
                message=entity.message,
                metadata_=entity.metadata_,
            )
            self.session.add(new_model)

        await self.session.flush()
        return entity

    async def add(self, entity: LogEntity) -> LogEntity:
        """Add a new log entity (alias for save)."""
        return await self.save(entity)

