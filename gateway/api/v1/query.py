from fastapi import APIRouter, Request
from loguru import logger

import httpx

from gateway.core.config import get_settings
from gateway.dependencies.httpx import HTTPXClientDep
from gateway.exceptions import OrchestratorProxyFailed
from shared.schemas import PipelineRequest
from shared.utils import forward_to_service

router = APIRouter()


@router.post("/pipelines/{pipeline_id}/run")
async def proxy_to_orchestrator(
    payload: PipelineRequest, pipeline_id: str, request: Request, client: HTTPXClientDep
):
    logger.info(
        "Proxying pipeline request: pipeline_id={}",
        pipeline_id,
    )
    gateway_settings = get_settings()
    orchestrator_url = f"{gateway_settings.ORCHESTRATOR_URL}/api/run/{pipeline_id}"
    try:
        response = await forward_to_service(
            request,
            client,
            orchestrator_url,
            timeout=gateway_settings.HTTPX_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as exc:
        raise OrchestratorProxyFailed("Orchestrator proxy request failed") from exc
    logger.info(
        "Orchestrator response: pipeline_id={} status_code={}",
        pipeline_id,
        response.status_code,
    )
    return response
