from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from shared.core.enums import QueryState
from shared.schemas.base import BaseSchema


class ResultMessage(BaseSchema):
    correlation_id: UUID
    interaction_id: UUID
    status: QueryState
    model: str
    output_text: str | None = None
    tokens_used: int | None = None
    error: str | None = None
    user_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)
