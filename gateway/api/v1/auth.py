from fastapi import APIRouter, Request
from loguru import logger

from gateway.core.exceptions.gateway_errors import AuthProxyFailed
from gateway.dependencies.httpx import HTTPXClientDep
from gateway.dependencies.rate_limiter import (
    RateLimiterLoginDep,
    RateLimiterLogoutDep,
    RateLimiterMeDep,
    RateLimiterRefreshDep,
    RateLimiterRegisterDep,
)
from gateway.dependencies.settings import GatewaySettingsDep
from shared.schemas import UserLoginRequest, UserRegisterRequest
from shared.utils import proxy_request

router = APIRouter(prefix="/auth", tags=["auth"])

AUTH_ERROR_MAP = {
    500: AuthProxyFailed,
    502: AuthProxyFailed,
    503: AuthProxyFailed,
    504: AuthProxyFailed,
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
        request,
        client,
        f"{settings.AUTH_URL}/auth/login",
        status_error_map=AUTH_ERROR_MAP,
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
        f"{settings.AUTH_URL}/auth/register",
        status_error_map=AUTH_ERROR_MAP,
    )


@router.post("/refresh", dependencies=[RateLimiterRefreshDep])
async def refresh(
    request: Request, client: HTTPXClientDep, settings: GatewaySettingsDep
):
    return await proxy_request(request, client, f"{settings.AUTH_URL}/auth/refresh")


@router.post("/logout", dependencies=[RateLimiterLogoutDep])
async def logout(
    request: Request, client: HTTPXClientDep, settings: GatewaySettingsDep
):
    return await proxy_request(request, client, f"{settings.AUTH_URL}/auth/logout")


@router.get("/me", dependencies=[RateLimiterMeDep])
async def me(request: Request, client: HTTPXClientDep, settings: GatewaySettingsDep):
    return await proxy_request(
        request, client, f"{settings.AUTH_URL}/auth/me", status_error_map=AUTH_ERROR_MAP
    )


@router.api_route(
    "/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
)
async def proxy_to_auth(
    path: str, request: Request, client: HTTPXClientDep, settings: GatewaySettingsDep
):
    """Catch-all for any other auth-related sub-routes."""
    return await proxy_request(request, client, f"{settings.AUTH_URL}/auth/{path}")
