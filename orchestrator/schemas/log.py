from datetime import datetime
from uuid import UUID

from pydantic import Field
from shared.schemas import BaseSchema


class LogBase(BaseSchema):
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
