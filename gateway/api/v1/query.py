from fastapi import APIRouter, Request
from loguru import logger

from gateway.core.config import get_settings
from gateway.dependencies.httpx import HTTPXClientDep
from gateway.dependencies.rate_limiter import RateLimiterQueryRunDep
from gateway.exceptions.gateway_errors import OrchestratorProxyFailed
from shared.schemas import PipelineRequest
from shared.utils import proxy_request  # Your new utility

router = APIRouter(tags=["orchestrator"])
settings = get_settings()

# Map upstream error codes to your specific exception
ORCHESTRATOR_ERROR_MAP = {
    500: OrchestratorProxyFailed,
    502: OrchestratorProxyFailed,
    503: OrchestratorProxyFailed,
    504: OrchestratorProxyFailed,
}


@router.post("/pipelines/{pipeline_id}/run", dependencies=[RateLimiterQueryRunDep])
async def proxy_to_orchestrator(
    payload: PipelineRequest, pipeline_id: str, request: Request, client: HTTPXClientDep
):
    logger.info("Running pipeline: pipeline_id={}", pipeline_id)
    return await proxy_request(
        request,
        client,
        f"{settings.ORCHESTRATOR_URL}/api/run/{pipeline_id}",
        timeout=settings.HTTPX_TIMEOUT_SECONDS,
        status_error_map=ORCHESTRATOR_ERROR_MAP,
    )


@router.get("/chats")
async def proxy_get_chats(request: Request, client: HTTPXClientDep):
    return await proxy_request(
        request,
        client,
        f"{settings.ORCHESTRATOR_URL}/api/chats",
        timeout=settings.HTTPX_TIMEOUT_SECONDS,
        status_error_map=ORCHESTRATOR_ERROR_MAP,
    )


@router.get("/chats/{interaction_id}/messages")
async def proxy_get_chat_messages(
    interaction_id: str, request: Request, client: HTTPXClientDep
):
    return await proxy_request(
        request,
        client,
        f"{settings.ORCHESTRATOR_URL}/api/chats/{interaction_id}/messages",
        timeout=settings.HTTPX_TIMEOUT_SECONDS,
        status_error_map=ORCHESTRATOR_ERROR_MAP,
    )
