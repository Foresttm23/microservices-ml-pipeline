class MLWorkerError(Exception):
    """Base class for ML worker errors."""


class ModelInitializationFailed(MLWorkerError):
    """Raised when the model or generator cannot initialize."""


class ProviderRequestFailed(MLWorkerError):
    """Raised when the model provider request fails."""


class ProviderResponseInvalid(MLWorkerError):
    """Raised when the provider response is invalid or missing data."""


class InferenceFailed(MLWorkerError):
    """Raised when inference fails unexpectedly."""

