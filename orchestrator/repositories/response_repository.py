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

