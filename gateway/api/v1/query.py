from fastapi import APIRouter, Request

from gateway.core.config import get_settings
from gateway.core.dependencies import HTTPXClientDep
from gateway.schemas.query import BaseQuery
from shared.utils import forward_to_service

router = APIRouter()


# Todo add middleware to verify that the message is not null before passing a post request.
@router.post("/pipelines/{pipeline_id}/run")
async def proxy_to_orchestrator(
    message: BaseQuery, pipeline_id: str, request: Request, client: HTTPXClientDep
):
    gateway_settings = get_settings()
    orchestrator_url = f"{gateway_settings.ORCHESTRATOR_URL}/api/run/{pipeline_id}"
    return await forward_to_service(
        request,
        client,
        orchestrator_url,
        timeout=gateway_settings.HTTPX_TIMEOUT_SECONDS,
    )
