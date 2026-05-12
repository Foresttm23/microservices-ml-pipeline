import httpx
from fastapi import APIRouter, Request
from loguru import logger

from gateway.core.config import get_settings
from gateway.dependencies.httpx import HTTPXClientDep
from gateway.exceptions.gateway_errors import AuthProxyFailed
from shared.utils import forward_to_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.api_route(
    "/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
)
async def proxy_to_auth(path: str, request: Request, client: HTTPXClientDep):
    settings = get_settings()
    query = request.url.query
    target_url = f"{settings.AUTH_URL}/auth/{path}"
    if query:
        target_url = f"{target_url}?{query}"

    logger.info("Proxying auth request: path={}", request.url.path)
    try:
        response = await forward_to_service(
            request,
            client,
            target_url,
            timeout=settings.HTTPX_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as exc:
        raise AuthProxyFailed("Auth proxy request failed") from exc
    logger.info(
        "Auth response: path={} status_code={}",
        request.url.path,
        response.status_code,
    )
    return response
