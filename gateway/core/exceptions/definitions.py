from shared.core.exceptions import ErrorDefinition

from gateway.core.exceptions.gateway_errors import (
    AuthProxyFailed,
    OrchestratorProxyFailed,
    WebSocketBridgeFailed,
)

GATEWAY_ERROR_MAP = {
    AuthProxyFailed: ErrorDefinition(
        code="gateway_auth_proxy_failed",
        status_code=502,
        detail="Failed to reach auth service.",
    ),
    OrchestratorProxyFailed: ErrorDefinition(
        code="gateway_orchestrator_proxy_failed",
        status_code=502,
        detail="Failed to reach orchestrator service.",
    ),
    WebSocketBridgeFailed: ErrorDefinition(
        code="gateway_websocket_failed",
        status_code=500,
        detail="WebSocket bridge error.",
    ),
}
