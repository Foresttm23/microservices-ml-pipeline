from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel as PydanticEntity
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase as OrmModel


class BaseRepository[TModel: OrmModel, TEntity: PydanticEntity](ABC):
    """
    Abstract Base Repository using the Data Mapper pattern.

    This class mediates between the Domain layer (Pydantic) and the
    Persistence layer (SQLAlchemy), ensuring that business logic
    never touches raw database models.

    Generic Parameters:
        TModel: The SQLAlchemy Declarative model (Persistence).
        TEntity: The Pydantic model representing the Domain entity.

    Invariants:
        - Methods return Domain Entities, never ORM Models.
        - Transaction boundaries (commit/rollback) are handled by the Service layer.
    """

    def __init__(
        self,
        session: AsyncSession,
        model_class: type[TModel],
        entity_class: type[TEntity],
    ):
        """
        Initialize with a database session and necessary type factories.

        Args:
            session: Active SQLAlchemy async session.
            model_class: The ORM class used for database queries.
            entity_class: The Pydantic class used for domain validation.
        """
        self.session = session
        self.model_class = model_class
        self.entity_class = entity_class

    def map_model_to_entity(self, model: TModel) -> TEntity:
        """
        Transform a database record into a domain entity.

        Uses Pydantic's attribute loading to bridge SQLAlchemy results to the domain.
        """
        return self.entity_class.model_validate(model)

    def map_entity_to_model(self, entity: TEntity) -> TModel:
        """
        Transform a domain entity into a fresh database record.

        Used primarily for 'Create' operations where no record currently exists.
        """
        return self.model_class(**entity.model_dump())

    def update_model_from_entity(self, model: TModel, entity: TEntity) -> TModel:
        """
        Synchronize an existing database record with domain entity data.

        Used for 'Update' operations to patch an existing attached model.
        Excludes unset fields to support partial updates and prevents ID mutation.
        """
        data = entity.model_dump(exclude_unset=True, exclude={"id"})
        for key, value in data.items():
            setattr(model, key, value)
        return model

    @abstractmethod
    async def get_by_id(self, entity_id: Any) -> TEntity | None:
        """
        Fetch a single entity by its primary key.

        Returns:
            The domain-validated entity or None if not found.
        """
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> list[TEntity]:
        """
        Fetch a paginated list of entities.
        """
        pass

    @abstractmethod
    async def create(self, entity: TEntity) -> TEntity:
        """
        Persist a new domain entity.

        Note: Changes are flushed to the session but not committed.
        """
        pass

    @abstractmethod
    async def update(self, entity_id: Any, entity: TEntity) -> TEntity | None:
        """
        Modify an existing entity by ID.

        Returns:
            The updated domain entity or None if the record does not exist.
        """
        pass

    @abstractmethod
    async def delete(self, entity_id: Any) -> bool:
        """
        Remove an entity by ID.

        Returns:
            True if the record was removed, False if not found.
        """
        pass
