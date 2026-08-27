from abc import ABC
from typing import Any

from pydantic import BaseModel as PydanticEntity
from sqlalchemy.ext.asyncio import AsyncSession

from shared.repositories.base import BaseRepository


class BaseService[TEntity: PydanticEntity, TRepo: BaseRepository](ABC):
    """
    Abstract Base Service representing the Application Layer.

    Responsibilities:
    - Orchestrate domain logic and repository operations.
    - Define transaction boundaries (Unit of Work).
    - Convert data between API requirements and Domain entities.
    - Prevent the leak of Persistence (ORM) details into the API layer.

    Generic Parameters:
        TEntity: The Pydantic model representing the Domain entity.
        TRepo: The concrete repository implementation for the entity.
    """

    def __init__(self, session: AsyncSession, repo: TRepo):
        """
        Initialize the service with its dependencies.

        Args:
            session: AsyncSession for managing database transactions.
            repo: The specific repository instance for data access.
        """
        self.session = session
        self.repo = repo

    async def get_by_id(self, entity_id: Any) -> TEntity | None:
        """Fetch a single entity by its primary key."""
        return await self.repo.get_by_id(entity_id)
