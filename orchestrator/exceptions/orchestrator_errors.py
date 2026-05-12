class OrchestratorServiceError(Exception):
    """Base class for orchestrator service errors."""


class TaskEnqueueFailed(OrchestratorServiceError):
    """Raised when a task cannot be enqueued."""


class QueryNotFound(OrchestratorServiceError):
    """Raised when a query entity cannot be found."""


class InvalidQueryState(OrchestratorServiceError):
    """Raised when a query is in an unexpected state."""


class ResultPublishFailed(OrchestratorServiceError):
    """Raised when publishing results fails."""

