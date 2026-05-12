from shared.core.exceptions import ErrorDefinition

from ml_worker.core.exceptions.errors import (
    InferenceFailed,
    ModelInitializationFailed,
    ProviderRequestFailed,
    ProviderResponseInvalid,
)

ML_ERROR_MAP = {
    ModelInitializationFailed: ErrorDefinition(code="ml_model_init_failed"),
    ProviderRequestFailed: ErrorDefinition(code="ml_provider_request_failed"),
    ProviderResponseInvalid: ErrorDefinition(code="ml_provider_response_invalid"),
    InferenceFailed: ErrorDefinition(code="ml_inference_failed"),
}
