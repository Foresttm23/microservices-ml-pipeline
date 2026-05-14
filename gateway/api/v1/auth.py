import httpx
from fastapi import APIRouter, Request
from loguru import logger

from auth.schemas.user import UserLoginRequest, UserRegisterRequest
from gateway.dependencies.httpx import HTTPXClientDep
from gateway.dependencies.rate_limiter import (
    RateLimiterLoginDep,
    RateLimiterLogoutDep,
    RateLimiterMeDep,
    RateLimiterRefreshDep,
    RateLimiterRegisterDep,
)
from gateway.dependencies.settings import GatewaySettingsDep
from gateway.exceptions.gateway_errors import AuthProxyFailed
from shared.utils import proxy_request

router = APIRouter(prefix="/auth", tags=["auth"])

# Default error mapping for Auth Service interactions
AUTH_ERROR_MAP = {
    401: AuthProxyFailed,
    403: AuthProxyFailed,
}


@router.post("/login", dependencies=[RateLimiterLoginDep])
async def login(
    payload: UserLoginRequest,
    request: Request,
    client: HTTPXClientDep,
    settings: GatewaySettingsDep,
):
    logger.info("Login attempt for email={}", payload.email)
    return await proxy_request(
        request, client, f"{settings.AUTH_URL}/login", status_error_map=AUTH_ERROR_MAP
    )


@router.post("/register", dependencies=[RateLimiterRegisterDep])
async def register(
    payload: UserRegisterRequest,
    request: Request,
    client: HTTPXClientDep,
    settings: GatewaySettingsDep,
):
    logger.info("Register attempt for email={}", payload.email)
    return await proxy_request(
        request,
        client,
        f"{settings.AUTH_URL}/register",
        status_error_map=AUTH_ERROR_MAP,
    )


@router.post("/refresh", dependencies=[RateLimiterRefreshDep])
async def refresh(
    request: Request, client: HTTPXClientDep, settings: GatewaySettingsDep
):
    return await proxy_request(request, client, f"{settings.AUTH_URL}/refresh")


@router.post("/logout", dependencies=[RateLimiterLogoutDep])
async def logout(
    request: Request, client: HTTPXClientDep, settings: GatewaySettingsDep
):
    return await proxy_request(request, client, f"{settings.AUTH_URL}/logout")


@router.get("/me", dependencies=[RateLimiterMeDep])
async def me(request: Request, client: HTTPXClientDep, settings: GatewaySettingsDep):
    return await proxy_request(
        request, client, f"{settings.AUTH_URL}/me", status_error_map=AUTH_ERROR_MAP
    )


@router.api_route(
    "/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
)
async def proxy_to_auth(
    path: str, request: Request, client: HTTPXClientDep, settings: GatewaySettingsDep
):
    """Catch-all for any other auth-related sub-routes."""
    return await proxy_request(request, client, f"{settings.AUTH_URL}/{path}")
