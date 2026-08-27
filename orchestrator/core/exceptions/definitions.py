from orchestrator.exceptions.domain_errors import (
    EmptyLogMessage,
    EmptyMetadataKey,
    EmptyResponseContent,
    InvalidQueryStateTransition,
    NegativeTokenCount,
)
from orchestrator.exceptions.orchestrator_errors import (
    InvalidQueryState,
    QueryNotFound,
    ResultPublishFailed,
    TaskEnqueueFailed,
)
from shared.core.exceptions import ErrorDefinition

ORCHESTRATOR_ERROR_MAP: dict[type[Exception], ErrorDefinition] = {
    TaskEnqueueFailed: ErrorDefinition(
        code="orchestrator_enqueue_failed",
        status_code=503,
        detail="Failed to enqueue task.",
    ),
    QueryNotFound: ErrorDefinition(
        code="orchestrator_query_not_found",
        status_code=404,
        detail="Query not found.",
    ),
    InvalidQueryState: ErrorDefinition(
        code="orchestrator_invalid_state",
        status_code=409,
        detail="Query is in an invalid state.",
    ),
    ResultPublishFailed: ErrorDefinition(
        code="orchestrator_publish_failed",
        status_code=503,
        detail="Failed to publish result.",
    ),
    InvalidQueryStateTransition: ErrorDefinition(
        code="orchestrator_invalid_transition",
        status_code=409,
        detail="Invalid query state transition.",
    ),
    EmptyResponseContent: ErrorDefinition(
        code="orchestrator_empty_response",
        status_code=400,
        detail="Response content cannot be empty.",
    ),
    NegativeTokenCount: ErrorDefinition(
        code="orchestrator_negative_tokens",
        status_code=400,
        detail="Token count cannot be negative.",
    ),
    EmptyLogMessage: ErrorDefinition(
        code="orchestrator_empty_log_message",
        status_code=400,
        detail="Log message cannot be empty.",
    ),
    EmptyMetadataKey: ErrorDefinition(
        code="orchestrator_empty_metadata_key",
        status_code=400,
        detail="Metadata key cannot be empty.",
    ),
}
