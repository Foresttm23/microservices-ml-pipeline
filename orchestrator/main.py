import asyncio
import contextlib
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from orchestrator.api.v1 import run
from orchestrator.core.config import get_settings
from orchestrator.services.result_processor import ResultProcessor
from shared.core.exceptions import global_exception_handler
from shared.core.logging import setup_logging
from shared.db import close_db, init_db
from shared.messaging import (
    QueueConsumer,
    RedisPubSub,
    get_redis_client,
    get_result_queue,
)
from shared.middlewares import LoggingContextMiddleware
from shared.schemas.result import ResultMessage


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()

    # Startup
    logger.info("Startup")
    orchestrator_settings = get_settings()
    init_db(orchestrator_settings.DATABASE_URL, pool_size=20, max_overflow=10)

    result_queue = get_result_queue()
    pubsub = RedisPubSub(get_redis_client())
    result_processor = ResultProcessor(pubsub)
    result_consumer = QueueConsumer[ResultMessage, None](
        processor=result_processor,
        queue=result_queue,
        message_factory=ResultMessage.model_validate_json,
    )
    consumer_task = asyncio.create_task(result_consumer.run())

    yield

    # Shutdown
    logger.info("Shutdown")
    consumer_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await consumer_task
    await close_db()


app = FastAPI(lifespan=lifespan)
global_exception_handler(app)

app.add_middleware(LoggingContextMiddleware)

app.add_middleware(
    CORSMiddleware,  # type: ignore[arg-type]
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API routers
app.include_router(run.router)


def main() -> None:
    orchestrator_settings = get_settings()
    uvicorn.run(
        "orchestrator.main:app",
        host="0.0.0.0",
        port=orchestrator_settings.PORT,
        reload=True,
    )


if __name__ == "__main__":
    main()
