from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import Field

from orchestrator.exceptions.domain_errors import InvalidQueryStateTransition
from orchestrator.schemas.log import LogResponse
from orchestrator.schemas.response import ResponseResponse
from shared.core import QueryState
from shared.schemas import BaseDomainEntity, BaseSchema


class QueryEntity(BaseDomainEntity):
    user_id: str
    correlation_id: UUID
    interaction_id: UUID = Field(default_factory=uuid4)
    message: str
    state: QueryState = QueryState.PENDING

    @classmethod
    def create(cls, user_id: str, correlation_id: UUID, message: str) -> "QueryEntity":
        """Factory to ensure a clean initial state."""
        return cls(
            user_id=user_id,
            correlation_id=correlation_id,
            message=message,
            state=QueryState.PENDING,
        )

    def transition_to(self, next_state: QueryState) -> None:
        """Internal state machine logic."""
        if self.state == QueryState.COMPLETED and next_state != QueryState.COMPLETED:
            raise InvalidQueryStateTransition(
                f"Cannot transition from COMPLETED to {next_state}"
            )

        if self.state == QueryState.FAILED and next_state != QueryState.FAILED:
            raise InvalidQueryStateTransition(
                f"Cannot transition from FAILED to {next_state}"
            )

        self.state = next_state

    def mark_completed(self) -> None:
        self.transition_to(QueryState.COMPLETED)

    def mark_failed(self) -> None:
        self.transition_to(QueryState.FAILED)


class QueryBase(BaseSchema):
    """Base schema for queries."""

    correlation_id: UUID = Field(..., description="Unique correlation ID for tracking")
    interaction_id: UUID = Field(..., description="Interaction session ID")
    message: str = Field(..., description="Query message content")
    state: QueryState = Field(
        default=QueryState.PENDING, description="Current state of the query"
    )


class QueryCreate(QueryBase):
    """Schema for creating a query."""

    pass


class QueryUpdate(BaseSchema):
    """Schema for updating a query."""

    state: Optional[QueryState] = Field(None, description="Updated state")
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
    state: QueryState = Field(..., description="Current state of the query")
    created_at: datetime = Field(..., description="When the query was created")

    class Config:
        from_attributes = True
