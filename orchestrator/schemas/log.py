from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import Field

from orchestrator.exceptions.domain_errors import EmptyLogMessage, EmptyMetadataKey
from shared.schemas import BaseDomainEntity, BaseSchema, CreatedAtMixin


class LogEntity(BaseDomainEntity, CreatedAtMixin):
    """Rich domain entity for Log with business logic."""

    query_id: UUID
    message: str
    metadata_: dict[str, Any] = Field(default_factory=dict, alias="metadata_")

    @classmethod
    def create(
        cls,
        query_id: UUID,
        message: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> "LogEntity":
        """
        Factory method to create a log entity.

        Args:
            query_id: ID of the query this log belongs to
            message: Log message
            metadata: Optional additional metadata

        Returns:
            LogEntity instance ready for persistence

        Raises:
            EmptyLogMessage: If message is empty
        """
        if not message or not message.strip():
            raise EmptyLogMessage("Log message cannot be empty")

        return cls(
            query_id=query_id,
            message=message,
            metadata_=metadata or {},
        )

    def add_metadata(self, key: str, value: Any) -> None:
        """
        Add or update a metadata key-value pair.

        Args:
            key: Metadata key
            value: Metadata value

        Raises:
            EmptyMetadataKey: If key is empty
        """
        if not key or not key.strip():
            raise EmptyMetadataKey("Metadata key cannot be empty")
        self.metadata_[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a metadata value by key.

        Args:
            key: Metadata key
            default: Default value if key not found

        Returns:
            Metadata value or default
        """
        return self.metadata_.get(key, default)

    def is_error_log(self) -> bool:
        """Check if this log is tagged as an error log."""
        return self.metadata_.get("is_error", False)

    def mark_as_error(self) -> None:
        """Mark this log as an error log."""
        self.add_metadata("is_error", True)


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
