from pydantic import Field
from uuid import UUID

from shared.schemas import BaseSchema


class PipelineRequest(BaseSchema):
    message: str
    interaction_id: UUID | None = None


class PipelineResponse(BaseSchema):
    status: str
    query_id: UUID
    correlation_id: UUID
    message: str = Field(..., min_length=1)
