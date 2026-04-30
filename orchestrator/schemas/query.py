from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class LogBase(BaseModel):
    """Base schema for logs."""

    message: str = Field(..., description="Log message")
    metadata_: dict = Field(default_factory=dict, description="Additional metadata")


class LogCreate(LogBase):
    """Schema for creating a log."""

    query_id: UUID = Field(..., description="Reference to the query")


class LogResponse(LogBase):
    """Schema for log responses."""

    id: UUID = Field(..., description="Log ID")
    query_id: UUID = Field(..., description="Reference to the query")
    created_at: datetime = Field(..., description="When the log was created")

    class Config:
        from_attributes = True


class ResponseBase(BaseModel):
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


class QueryBase(BaseModel):
    """Base schema for queries."""

    correlation_id: UUID = Field(..., description="Unique correlation ID for tracking")
    interaction_id: UUID = Field(..., description="Interaction session ID")
    message: str = Field(..., description="Query message content")
    state: str = Field(default="PENDING", description="Current state of the query")


class QueryCreate(QueryBase):
    """Schema for creating a query."""

    pass


class QueryUpdate(BaseModel):
    """Schema for updating a query."""

    state: Optional[str] = Field(None, description="Updated state")
    message: Optional[str] = Field(None, description="Updated message")


class QueryResponse(QueryBase):
    """Schema for query responses with related data."""

    id: UUID = Field(..., description="Query ID")
    created_at: datetime = Field(..., description="When the query was created")
    updated_at: datetime = Field(..., description="When the query was last updated")
    responses: List[ResponseResponse] = Field(default_factory=list, description="Associated responses")
    logs: List[LogResponse] = Field(default_factory=list, description="Associated logs")

    class Config:
        from_attributes = True


class QueryDetailResponse(QueryResponse):
    """Detailed query response with all nested relations."""

    pass


class QueryListResponse(BaseModel):
    """Lightweight query response for list endpoints."""

    id: UUID = Field(..., description="Query ID")
    correlation_id: UUID = Field(..., description="Unique correlation ID")
    interaction_id: UUID = Field(..., description="Interaction session ID")
    state: str = Field(..., description="Current state of the query")
    created_at: datetime = Field(..., description="When the query was created")

    class Config:
        from_attributes = True

