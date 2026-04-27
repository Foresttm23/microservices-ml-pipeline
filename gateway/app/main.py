import os
from contextlib import asynccontextmanager

import httpx
import uvicorn
from .api.v1 import health, query
from .core.exception_handlers import register_exception_handlers
from .core.httpx_client import httpx_client_manager
from .core.logging import setup_logging
from .middleware import RequestContextMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()

    # Startup
    logger.info("Startup")
    httpx_client_manager.start(
        timeout=httpx.Timeout(10.0),
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
    )

    yield

    # Shutdown
    logger.info("Shutdown")
    await httpx_client_manager.stop()


app = FastAPI(lifespan=lifespan)
app.include_router(health.router)
app.include_router(query.router)

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
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
