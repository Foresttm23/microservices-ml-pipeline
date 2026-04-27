from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ResultMessage(BaseModel):
	interaction_id: str
	status: Literal["completed", "failed", "mocked"]
	model: str
	output_text: str | None = None
	error: str | None = None
	user_id: str | None = None
	created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
	metadata: dict[str, Any] = Field(default_factory=dict)

