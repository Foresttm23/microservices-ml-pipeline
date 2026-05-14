from datetime import datetime
from uuid import UUID, uuid4

from typing import Generic, TypeVar, Sequence
from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class BaseDomainEntity(BaseSchema):
    id: UUID = Field(default_factory=uuid4)


class CreatedAtMixin(BaseSchema):
    created_at: datetime | None = None


class UpdatedAtMixin(BaseSchema):
    updated_at: datetime | None = None


class PaginatedResponse[T](BaseModel):
    items: Sequence[T]
    total: int
    skip: int
    limit: int
