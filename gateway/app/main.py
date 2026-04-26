import os
from contextlib import asynccontextmanager

import uvicorn

from core.httpx_client import http_client_manager
from core.logging import setup_logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()

    # Startup
    logger.info("Startup")
    http_client_manager.start(
        timeout=10.0,
        limits={"max_connections": 100, "max_keepalive_connections": 20},
    )

    yield
    # Shutdown
    logger.info("Shutdown")

    await http_client_manager.stop()


app = FastAPI()
app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    # We point to "app.main:app" so uvicorn knows where the instance is
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
