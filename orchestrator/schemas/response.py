from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field, ConfigDict

from orchestrator.exceptions.domain_errors import (
    EmptyResponseContent,
    NegativeTokenCount,
)
from shared.schemas import BaseDomainEntity, BaseSchema, CreatedAtMixin, UpdatedAtMixin


class ResponseEntity(BaseDomainEntity, CreatedAtMixin, UpdatedAtMixin):
    """Rich domain entity for Response with business logic."""

    query_id: UUID
    content: str
    tokens_used: Optional[int] = None

    @classmethod
    def create(
        cls,
        query_id: UUID,
        content: str,
        tokens_used: Optional[int] = None,
    ) -> "ResponseEntity":
        """
        Factory method to create a response entity.

        Args:
            query_id: ID of the query this response belongs to
            content: Response content/text
            tokens_used: Optional token count from the model

        Returns:
            ResponseEntity instance ready for persistence
        """
        return cls(
            query_id=query_id,
            content=content,
            tokens_used=tokens_used,
        )

    def update_content(self, new_content: str) -> None:
        """Update response content (immutable by default - use this for mutations)."""
        if not new_content or not new_content.strip():
            raise EmptyResponseContent("Response content cannot be empty")
        self.content = new_content

    def add_token_count(self, tokens: int) -> None:
        """
        Add or update token count for this response.
        Validates that token count is non-negative.
        """
        if tokens < 0:
            raise NegativeTokenCount("Token count cannot be negative")
        self.tokens_used = tokens


class ResponseBase(BaseSchema):
    """Base schema for responses."""

    content: str = Field(..., description="Response content")
    tokens_used: Optional[int] = Field(None, description="Tokens used for the response")


class ResponseCreate(ResponseBase):
    """Schema for creating a response."""

    query_id: UUID = Field(..., description="Reference to the query")


class ResponseResponse(ResponseBase):
    """Schema for response records."""

    model_config = ConfigDict(from_attributes=True)

    query_id: UUID = Field(..., description="Reference to the query")
    created_at: datetime = Field(..., description="When the response was created")
    updated_at: datetime = Field(..., description="When the response was last updated")
