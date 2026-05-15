from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from orchestrator.db.models import LogModel
from orchestrator.schemas.log import LogEntity
from shared.repositories import BaseRepository


class LogRepository(BaseRepository[LogModel, LogEntity]):
    """Repository for Log entities."""

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model_class=LogModel, entity_class=LogEntity)

