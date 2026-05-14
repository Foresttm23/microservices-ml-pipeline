class GatewayServiceError(Exception):
    """Base class for gateway service errors."""


class AuthProxyFailed(GatewayServiceError):
    """Raised when auth proxying fails."""


class OrchestratorProxyFailed(GatewayServiceError):
    """Raised when orchestrator proxying fails."""


class WebSocketBridgeFailed(GatewayServiceError):
    """Raised when WebSocket bridging fails."""

