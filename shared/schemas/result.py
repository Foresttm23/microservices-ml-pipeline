from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field

from shared.schemas.base import BaseSchema


class ResultMessage(BaseSchema):
    correlation_id: UUID
    interaction_id: UUID
    status: Literal["completed", "failed", "mocked"]
    model: str
    output_text: str | None = None
    error: str | None = None
    user_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)
