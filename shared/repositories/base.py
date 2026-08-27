from abc import ABC
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase as OrmModel

from shared.schemas.base import BaseDomainEntity


class BaseRepository[TModel: OrmModel, TEntity: BaseDomainEntity](ABC):
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
        data = entity.model_dump(exclude_unset=True, exclude={"id", "created_at"})
        for key, value in data.items():
            if hasattr(model, key):
                setattr(model, key, value)
        return model

    async def get_by_id(self, entity_id: Any) -> TEntity | None:
        """
        Fetch a single entity by its primary key.

        Returns:
            The domain-validated entity or None if not found.
        """
        model = await self.session.get(self.model_class, entity_id)
        return self.map_model_to_entity(model) if model else None

    async def save(self, entity: TEntity) -> TEntity:
        """
        Save a domain entity, performing an upsert operation.

        If the entity exists (based on the ID), it updates the existing record.
        Otherwise, it creates a new record.

        Returns:
            The persisted domain entity.
        """
        model = await self.session.get(self.model_class, entity.id)
        if model:
            self.update_model_from_entity(model, entity)
        else:
            model = self.map_entity_to_model(entity)
            self.session.add(model)
        await self.session.flush()
        return self.map_model_to_entity(model)

    async def _get_paginated(
        self, stmt: Select, skip: int, limit: int
    ) -> tuple[list[TEntity], int]:
        """
        Helper method to execute a paginated query and return both the entities and total count.
        """
        total_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.session.execute(total_stmt)
        total = total_result.scalar_one()

        paginated_stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(paginated_stmt)
        items = [self.map_model_to_entity(model) for model in result.scalars().all()]
        return items, total
