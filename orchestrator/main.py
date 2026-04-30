from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from orchestrator.core.config import get_settings
from orchestrator.db.session import close_db, init_db
from shared.core import register_exception_handlers, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()

    # Startup
    logger.info("Startup")
    orchestrator_settings = get_settings()
    init_db(orchestrator_settings, pool_size=20, max_overflow=10)

    yield

    # Shutdown
    logger.info("Shutdown")
    await close_db()


app = FastAPI(lifespan=lifespan)
register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,  # type: ignore[arg-type]
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    orchestrator_settings = get_settings()
    uvicorn.run(
        "orchestrator.main:app",
        host="0.0.0.0",
        port=orchestrator_settings.PORT,
        reload=True,
    )
