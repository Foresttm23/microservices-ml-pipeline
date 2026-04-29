import os
from contextlib import asynccontextmanager

import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from shared.core import register_exception_handlers, setup_logging

from .api.v1 import health_router, query_router
from .core import close_httpx, get_settings, init_httpx
from .middleware import RequestContextMiddleware


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

    yield

    # Shutdown
    logger.info("Shutdown")
    await close_httpx()


app = FastAPI(lifespan=lifespan)
app.include_router(health_router)
app.include_router(query_router)

register_exception_handlers(app)
app.add_middleware(RequestContextMiddleware)

app.add_middleware(
    CORSMiddleware,  # type: ignore[arg-type]
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    # Keep ASGI import target explicit for module-based startup.
    uvicorn.run("gateway.app.main:app", host="0.0.0.0", port=port, reload=True)
