from fastapi import APIRouter, Request

from gateway.core.config import get_settings
from gateway.core.dependencies import HTTPXClientDep
from shared.schemas import PipelineRequest
from shared.utils import forward_to_service

router = APIRouter()


@router.post("/pipelines/{pipeline_id}/run")
async def proxy_to_orchestrator(
    payload: PipelineRequest, pipeline_id: str, request: Request, client: HTTPXClientDep
):
    gateway_settings = get_settings()
    orchestrator_url = f"{gateway_settings.ORCHESTRATOR_URL}/api/run/{pipeline_id}"
    return await forward_to_service(
        request,
        client,
        orchestrator_url,
        timeout=gateway_settings.HTTPX_TIMEOUT_SECONDS,
    )
