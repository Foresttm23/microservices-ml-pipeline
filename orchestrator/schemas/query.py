from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import Field

from orchestrator.schemas.log import LogResponse
from orchestrator.schemas.response import ResponseResponse
from shared.schemas import BaseSchema


class QueryBase(BaseSchema):
    """Base schema for queries."""

    correlation_id: UUID = Field(..., description="Unique correlation ID for tracking")
    interaction_id: UUID = Field(..., description="Interaction session ID")
    message: str = Field(..., description="Query message content")
    state: str = Field(default="PENDING", description="Current state of the query")


class QueryCreate(QueryBase):
    """Schema for creating a query."""

    pass


class QueryUpdate(BaseSchema):
    """Schema for updating a query."""

    state: Optional[str] = Field(None, description="Updated state")
    message: Optional[str] = Field(None, description="Updated message")


class QueryResponse(QueryBase):
    """Schema for query responses with related data."""

    id: UUID = Field(..., description="Query ID")
    created_at: datetime = Field(..., description="When the query was created")
    updated_at: datetime = Field(..., description="When the query was last updated")
    responses: List[ResponseResponse] = Field(
        default_factory=list, description="Associated responses"
    )
    logs: List[LogResponse] = Field(default_factory=list, description="Associated logs")

    class Config:
        from_attributes = True


class QueryDetailResponse(QueryResponse):
    """Detailed query response with all nested relations."""

    pass


class QueryListResponse(BaseSchema):
    """Lightweight query response for list endpoints."""

    id: UUID = Field(..., description="Query ID")
    correlation_id: UUID = Field(..., description="Unique correlation ID")
    interaction_id: UUID = Field(..., description="Interaction session ID")
    state: str = Field(..., description="Current state of the query")
    created_at: datetime = Field(..., description="When the query was created")

    class Config:
        from_attributes = True
