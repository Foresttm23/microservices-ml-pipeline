from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from orchestrator.db.models import ResponseModel
from orchestrator.schemas.response import ResponseEntity
from shared.repositories import BaseRepository


class ResponseRepository(BaseRepository[ResponseModel, ResponseEntity]):
    """Repository for Response entities."""

    def __init__(self, session: AsyncSession):
        super().__init__(
            session=session, model_class=ResponseModel, entity_class=ResponseEntity
        )

    async def get_by_id(self, response_id: UUID) -> ResponseEntity | None:
        """Fetch a response entity by its ID."""
        stmt = select(ResponseModel).where(ResponseModel.id == response_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self.map_model_to_entity(model) if model else None

    async def get_by_query_id(self, query_id: UUID) -> list[ResponseEntity]:
        """Fetch all responses for a given query."""
        stmt = select(ResponseModel).where(ResponseModel.query_id == query_id)
        result = await self.session.execute(stmt)
        return [self.map_model_to_entity(model) for model in result.scalars().all()]

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[ResponseEntity]:
        """Fetch all responses with pagination."""
        stmt = select(ResponseModel).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return [self.map_model_to_entity(model) for model in result.scalars().all()]

    async def create(self, entity: ResponseEntity) -> ResponseEntity:
        raise NotImplementedError("Use ResponseEntity.create() and save()")

    async def update(self, entity_id: UUID, entity: ResponseEntity) -> ResponseEntity | None:
        raise NotImplementedError(
            "Response updates should be performed via entity methods"
        )

    async def delete(self, entity_id: UUID) -> bool:
        raise NotImplementedError("Response deletion is not supported")

    async def save(self, entity: ResponseEntity) -> ResponseEntity:
        """
        Persist a response entity.

        Creates a new ResponseModel or updates existing one.
        """
        existing_model = await self.session.get(ResponseModel, entity.id)

        if existing_model:
            # Update existing model
            existing_model.content = entity.content
            existing_model.tokens_used = entity.tokens_used
        else:
            # Create new model
            new_model = ResponseModel(
                id=entity.id,
                query_id=entity.query_id,
                content=entity.content,
                tokens_used=entity.tokens_used,
            )
            self.session.add(new_model)

        await self.session.flush()
        return entity

    async def add(self, entity: ResponseEntity) -> ResponseEntity:
        """Add a new response entity (alias for save)."""
        return await self.save(entity)

