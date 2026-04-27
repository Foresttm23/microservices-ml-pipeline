from typing import Any

from pydantic import BaseModel, Field


class TaskMessage(BaseModel):
    prompt: str = Field(min_length=1, description="Prompt sent to Gemini")
    interaction_id: str | None = Field(
        default=None,
        description="Cross-service trace id propagated from gateway/orchestrator",
    )
    user_id: str | None = Field(default=None)
    model: str | None = Field(
        default=None, description="Optional Gemini model override"
    )
    metadata: dict[str, Any] = Field(default_factory=dict)

