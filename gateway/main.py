import os
from contextlib import asynccontextmanager

import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
from loguru import logger

from gateway.api.v1.auth import router as auth_router
from gateway.api.v1.health import router as health_router
from gateway.api.v1.query import router as query_router
from gateway.api.v1.websocket import router as websocket_router
from gateway.core.config import get_settings
from gateway.core.exceptions.definitions import GATEWAY_ERROR_MAP
from gateway.dependencies.rate_limiter import RateLimiterGlobalDep
from gateway.infra.httpx_client import close_httpx, init_httpx
from shared.core.exceptions import global_exception_handler
from shared.core.logging import setup_logging
from shared.messaging import get_redis_client
from shared.middlewares import (
    JWTAuthMiddleware,
    LoggingContextMiddleware,
    ResponseLogMiddleware,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()

    # Startup
    logger.info("Startup")
    settings = get_settings()
    init_httpx(
        timeout=httpx.Timeout(settings.HTTPX_TIMEOUT_SECONDS),
        limits=httpx.Limits(
            max_connections=settings.HTTPX_MAX_CONNECTIONS,
            max_keepalive_connections=settings.HTTPX_MAX_KEEPALIVE_CONNECTIONS,
        ),
    )

    redis = get_redis_client()
    await FastAPILimiter.init(redis)

    yield

    # Shutdown
    logger.info("Shutdown")
    await close_httpx()


app = FastAPI(lifespan=lifespan, dependencies=[RateLimiterGlobalDep])
app.include_router(auth_router)
app.include_router(health_router)
app.include_router(query_router)
app.include_router(websocket_router)

global_exception_handler(app, service_error_map=GATEWAY_ERROR_MAP)

app.add_middleware(ResponseLogMiddleware)
app.add_middleware(JWTAuthMiddleware, settings=get_settings())
app.add_middleware(LoggingContextMiddleware)

app.add_middleware(
    CORSMiddleware,  # type: ignore[arg-type]
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def main() -> None:
    port = int(os.getenv("PORT", 8000))
    # Keep ASGI import target explicit for module-based startup.
    uvicorn.run("gateway.main:app", host="0.0.0.0", port=port, reload=True)


if __name__ == "__main__":
    main()
