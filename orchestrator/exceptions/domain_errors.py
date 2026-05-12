class OrchestratorDomainError(Exception):
    """Base class for orchestrator domain validation errors."""


class InvalidQueryStateTransition(OrchestratorDomainError):
    """Raised when a query attempts an invalid state transition."""


class EmptyResponseContent(OrchestratorDomainError):
    """Raised when response content is empty."""


class NegativeTokenCount(OrchestratorDomainError):
    """Raised when tokens used is negative."""


class EmptyLogMessage(OrchestratorDomainError):
    """Raised when a log message is empty."""


class EmptyMetadataKey(OrchestratorDomainError):
    """Raised when a metadata key is empty."""

