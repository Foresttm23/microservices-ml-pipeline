from shared.schemas import BaseSchema
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field


class ResponseBase(BaseSchema):
    """Base schema for responses."""

    content: str = Field(..., description="Response content")
    tokens_used: Optional[int] = Field(None, description="Tokens used for the response")


class ResponseCreate(ResponseBase):
    """Schema for creating a response."""

    query_id: UUID = Field(..., description="Reference to the query")


class ResponseResponse(ResponseBase):
    """Schema for response records."""

    id: UUID = Field(..., description="Response ID")
    query_id: UUID = Field(..., description="Reference to the query")
    created_at: datetime = Field(..., description="When the response was created")
    updated_at: datetime = Field(..., description="When the response was last updated")

    class Config:
        from_attributes = True
