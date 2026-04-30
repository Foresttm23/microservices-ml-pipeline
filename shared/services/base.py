from abc import ABC, abstractmethod
from typing import Any

from loguru import logger
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

    @abstractmethod
    async def get_by_id(self, entity_id: Any) -> TEntity | None:
        """
        Retrieve a single entity by its unique identifier.

        Returns:
            The domain entity if found, otherwise None.
        """
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> list[TEntity]:
        """
        Retrieve a paginated collection of entities.
        """
        pass

    @abstractmethod
    async def create(self, entity: TEntity) -> TEntity:
        """
        Execute business validation and persist a new entity.

        This method is responsible for:
        - Validating domain rules.
        - Calling the repository to save data.
        - Committing the transaction if successful.

        Raises:
            ValueError: If domain validation fails.
            Exception: If database persistence fails.
        """
        pass

    @abstractmethod
    async def update(self, entity_id: Any, entity: TEntity) -> TEntity | None:
        """
        Update an existing entity's state.

        This method should verify existence, apply business rules,
        and commit changes.
        """
        pass

    @abstractmethod
    async def delete(self, entity_id: Any) -> bool:
        """
        Remove an entity and handle associated cleanup.

        Returns:
            True if deletion was successful and committed, False if not found.
        """
        pass
